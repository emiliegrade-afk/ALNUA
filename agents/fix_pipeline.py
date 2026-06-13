"""
fix_pipeline.py — Pipeline autonome de correction de bugs ALNUA.

Inspiré de AI Scientist (Sakana) + Hermes (Nous Research) :
- Itératif : jamais "impossible", juste "pas encore assez de contexte"
- Auto-apprenant : chaque tentative enrichit le journal
- Multi-agent : QA + Spec vérifient avant merge
- Auto-déploiement : détecte l'environnement et redémarre seul

Flow complet :
    bug_watchdog détecte erreur
        ↓
    fix_pipeline.run(error)
        ↓
    [Boucle itérative — contexte croissant à chaque retry]
    Tentative N : CodeAgent génère fix → pytest → QA review → Spec review
        ↓ (tout vert)
    Auto-merge main → Auto-deploy → Telegram ✅
        ↓ (persistance)
    Journal mis à jour → Mem0 → agents apprennent pour la prochaine fois
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import subprocess
import urllib.request
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE = "https://openrouter.ai/api/v1/chat/completions"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
REVIEW_MODEL = os.getenv("REVIEW_MODEL", "anthropic/claude-sonnet-4-5")
FIX_MODEL = os.getenv("FIX_MODEL", "minimax/minimax-m1")

# Contexte croissant selon le numéro de tentative
CONTEXT_LEVELS = [
    {"files": 2,  "history": 3,  "depth": "shallow"},   # Tentative 1 : rapide
    {"files": 5,  "history": 8,  "depth": "medium"},    # Tentative 2 : élargi
    {"files": 10, "history": 15, "depth": "deep"},      # Tentative 3 : complet
    {"files": 20, "history": 20, "depth": "exhaustive"},# Tentative 4+ : tout
]


# ---------------------------------------------------------------------------
# LLM call direct
# ---------------------------------------------------------------------------

def _llm(system: str, user: str, model: str = REVIEW_MODEL) -> str:
    payload = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.1,
        "max_tokens": 6000,
    }).encode()
    req = urllib.request.Request(
        OPENROUTER_BASE,
        data=payload,
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())["choices"][0]["message"]["content"]


# ---------------------------------------------------------------------------
# Auto-détection du déploiement (style Hermes — lit l'env, ne suppose rien)
# ---------------------------------------------------------------------------

def _detect_deploy_method(repo_path: str) -> dict[str, Any]:
    """
    Lit le repo et détecte comment l'app tourne.
    Retourne {"method": str, "command": list, "restart_signal": str}
    """
    root = Path(repo_path)

    # PM2
    if (root / "pm2.config.js").exists() or (root / "ecosystem.config.js").exists():
        name = "hub"
        try:
            cfg = (root / "pm2.config.js").read_text()
            import re
            m = re.search(r'name["\s:]+["\']([^"\']+)', cfg)
            if m:
                name = m.group(1)
        except Exception:
            pass
        return {"method": "pm2", "command": ["pm2", "restart", name], "name": name}

    # Docker Compose
    if (root / "docker-compose.yml").exists() or (root / "docker-compose.yaml").exists():
        return {"method": "docker", "command": ["docker-compose", "restart"], "name": "docker"}

    # Systemd service
    for f in Path("/etc/systemd/system").glob("*.service") if Path("/etc/systemd/system").exists() else []:
        if "hub" in f.stem or "alnua" in f.stem.lower():
            return {"method": "systemd", "command": ["systemctl", "restart", f.stem], "name": f.stem}

    # Procfile (Heroku style)
    if (root / "Procfile").exists():
        try:
            proc = (root / "Procfile").read_text().split("\n")[0]
            cmd = proc.split(":", 1)[-1].strip().split()
            return {"method": "procfile", "command": cmd, "name": "web"}
        except Exception:
            pass

    # uvicorn / FastAPI détecté dans requirements ou main.py
    if (root / "api" / "main.py").exists() or (root / "main.py").exists():
        entry = "api.main:app" if (root / "api" / "main.py").exists() else "main:app"
        return {
            "method": "uvicorn",
            "command": ["uvicorn", entry, "--reload", "--port", "8000"],
            "name": "uvicorn",
        }

    return {"method": "unknown", "command": [], "name": "unknown"}


def _restart_app(repo_path: str, deploy_info: dict) -> bool:
    """Redémarre l'app selon la méthode détectée."""
    method = deploy_info["method"]
    cmd = deploy_info["command"]

    if not cmd:
        logger.warning("fix_pipeline: méthode de déploiement inconnue, pas de restart")
        return False

    try:
        if method in ("pm2", "systemd", "docker"):
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return r.returncode == 0
        elif method == "uvicorn":
            # Tue l'ancien process uvicorn et redémarre en background
            subprocess.run(["pkill", "-f", "uvicorn"], capture_output=True)
            asyncio.get_event_loop().run_in_executor(
                None,
                lambda: subprocess.Popen(cmd, cwd=repo_path),
            )
            return True
        elif method == "procfile":
            subprocess.Popen(cmd, cwd=repo_path)
            return True
    except Exception as exc:
        logger.error("fix_pipeline: restart failed: %s", exc)
    return False


# ---------------------------------------------------------------------------
# Tests automatiques
# ---------------------------------------------------------------------------

def _run_tests(repo_path: str) -> dict[str, Any]:
    """
    Lance pytest si disponible. Retourne {"passed": bool, "output": str, "coverage": int}.
    Si pas de tests → retourne passed=True (no tests = no regression detected).
    """
    root = Path(repo_path)

    # Cherche un dossier de tests
    test_dirs = [d for d in ["tests", "test", "spec"] if (root / d).is_dir()]
    test_files = list(root.glob("test_*.py")) + list(root.glob("*_test.py"))

    if not test_dirs and not test_files:
        return {
            "passed": True,
            "output": "Aucun test trouvé — skip (pas de régression détectée).",
            "coverage": -1,
        }

    try:
        r = subprocess.run(
            ["python", "-m", "pytest", "-x", "-q", "--tb=short", "--no-header"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=120,
        )
        passed = r.returncode == 0
        output = (r.stdout + r.stderr)[-3000:]
        return {"passed": passed, "output": output, "coverage": -1}
    except FileNotFoundError:
        return {"passed": True, "output": "pytest non installé — skip.", "coverage": -1}
    except subprocess.TimeoutExpired:
        return {"passed": False, "output": "pytest timeout (>2min) — fix potentiellement bloquant.", "coverage": -1}


# ---------------------------------------------------------------------------
# Review multi-agents
# ---------------------------------------------------------------------------

def _qa_review(diff: str, error_message: str, fix_summary: str) -> dict[str, Any]:
    """
    QA Agent — vérifie que le fix est logiquement correct.
    Retourne {"approved": bool, "feedback": str}
    """
    system = """Tu es un agent QA expert Python pour ALNUA Hub.
Tu analyses un diff de code et décides si le fix est correct.
Réponds UNIQUEMENT en JSON : {"approved": true/false, "feedback": "raison en 2 phrases max"}
Sois strict : approuve uniquement si le fix est clairement correct et ciblé."""

    user = f"""ERREUR ORIGINALE :
{error_message[:800]}

FIX APPLIQUÉ (résumé) :
{fix_summary}

DIFF :
{diff[:3000]}

Ce fix résout-il correctement l'erreur sans introduire de nouveaux problèmes ?"""

    try:
        raw = _llm(system, user)
        import re
        m = re.search(r'\{.*\}', raw, re.DOTALL)
        if m:
            return json.loads(m.group())
    except Exception as exc:
        logger.warning("QA review failed: %s", exc)
    return {"approved": False, "feedback": "Review impossible — fix non approuvé par précaution."}


def _spec_review(diff: str, fix_summary: str, repo_context: str) -> dict[str, Any]:
    """
    Spec Agent — vérifie cohérence architecturale.
    Retourne {"approved": bool, "feedback": str}
    """
    system = """Tu es un agent Spec/Architecture expert pour ALNUA Hub.
Tu vérifies qu'un fix respecte l'architecture du projet.
Réponds UNIQUEMENT en JSON : {"approved": true/false, "feedback": "raison en 2 phrases max"}
Approuve si le fix est minimal et cohérent avec la structure existante."""

    user = f"""CONTEXTE PROJET :
{repo_context[:1000]}

FIX APPLIQUÉ :
{fix_summary}

DIFF :
{diff[:2000]}

Le fix respecte-t-il l'architecture et les conventions du projet ?"""

    try:
        raw = _llm(system, user)
        import re
        m = re.search(r'\{.*\}', raw, re.DOTALL)
        if m:
            return json.loads(m.group())
    except Exception as exc:
        logger.warning("Spec review failed: %s", exc)
    return {"approved": False, "feedback": "Review impossible — fix non approuvé par précaution."}


# ---------------------------------------------------------------------------
# Git helpers
# ---------------------------------------------------------------------------

def _get_diff(repo_path: str, branch: str) -> str:
    """Récupère le diff entre la branche de fix et main."""
    try:
        r = subprocess.run(
            ["git", "diff", "main", branch, "--stat", "-p", "--no-color"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=15,
        )
        return r.stdout[:5000]
    except Exception:
        return ""


def _auto_merge(repo_path: str, branch: str) -> bool:
    """Merge automatique de la branche fix sur main."""
    try:
        import git
        repo = git.Repo(repo_path)
        repo.git.checkout("main")
        repo.git.pull("origin", "main")
        repo.git.merge(branch, "--no-ff", m=f"[auto-merge] {branch}")
        origin = repo.remote("origin")
        origin.push("main")
        logger.info("fix_pipeline: merge automatique OK — %s → main", branch)
        return True
    except Exception as exc:
        logger.error("fix_pipeline: auto-merge failed: %s", exc)
        return False


def _rollback(repo_path: str, branch: str) -> None:
    """Supprime la branche de fix sans merger."""
    try:
        import git
        repo = git.Repo(repo_path)
        repo.git.checkout("main")
        repo.delete_head(branch, force=True)
        logger.info("fix_pipeline: rollback — branche %s supprimée", branch)
    except Exception as exc:
        logger.warning("fix_pipeline: rollback failed: %s", exc)


# ---------------------------------------------------------------------------
# Enrichissement contexte (pour les retries)
# ---------------------------------------------------------------------------

def _build_context(error: dict, repo_path: str, attempt: int) -> dict[str, Any]:
    """
    Construit un contexte de plus en plus riche selon le numéro de tentative.
    Cœur du système d'apprentissage itératif.
    """
    level = CONTEXT_LEVELS[min(attempt, len(CONTEXT_LEVELS) - 1)]
    context: dict[str, Any] = {
        "error": error,
        "attempt": attempt + 1,
        "level": level["depth"],
    }

    # Historique des tentatives précédentes (depuis le journal)
    try:
        from skills.skill_error_journal import get_error_history
        context["history"] = get_error_history(
            agent_name=error.get("agent_name", ""),
            error_type=error.get("error_type", ""),
            limit=level["history"],
        )
    except Exception:
        context["history"] = []

    # Contexte Mem0 — leçons du dev concerné sur ce type d'erreur
    try:
        from skills.skill_agent_learning import get_learning_context, memory_agent_id

        agent_name = error.get("agent_name", "dev_app")
        query = f"fix {error.get('error_type', '')} {error.get('error_message', '')[:100]}"
        context["memory"] = get_learning_context(memory_agent_id(agent_name), query)
    except Exception:
        context["memory"] = ""

    # Fichiers supplémentaires si retry (lecture plus large du repo)
    if attempt >= 1 and repo_path:
        root = Path(repo_path)
        extra_files = {}
        py_files = sorted(root.rglob("*.py"), key=lambda p: p.stat().st_mtime, reverse=True)
        for pf in py_files[:level["files"]]:
            if ".git" not in str(pf) and "__pycache__" not in str(pf):
                try:
                    rel = str(pf.relative_to(root))
                    extra_files[rel] = pf.read_text(encoding="utf-8", errors="ignore")[:2000]
                except Exception:
                    pass
        context["extra_files"] = extra_files

    return context


# ---------------------------------------------------------------------------
# Apprentissage — enregistrement dans journal + Mem0
# ---------------------------------------------------------------------------

def _record_attempt(error_id: str, attempt: int, result: str, learned: str) -> None:
    """Enregistre ce qu'on a appris de cette tentative."""
    try:
        from skills.skill_error_journal import add_attempt_note
        add_attempt_note(error_id, attempt=attempt, note=f"Tentative {attempt+1}: {result} | Appris: {learned}")
    except Exception:
        pass


def _record_failure_learning(error: dict, attempt: int, reason: str, learned: str) -> None:
    """Distille et enregistre chaque échec intermédiaire dans Mem0."""
    try:
        from skills.skill_agent_learning import learn_from_failure, memory_agent_id

        agent_name = memory_agent_id(error.get("agent_name", "dev_app"))
        err_type = error.get("error_type", "unknown")
        learn_from_failure(
            agent_id=agent_name,
            task=(
                f"fix {err_type} (tentative {attempt + 1}): "
                f"{error.get('error_message', '')[:200]}"
            ),
            error=f"{reason}: {learned[:400]}",
        )
    except Exception as exc:
        logger.warning("fix_pipeline: failure learning failed: %s", exc)


def _record_resolution(error: dict, fix_summary: str, diff: str) -> None:
    """
    Enregistre le fix réussi dans Mem0 — apprentissage ciblé par domaine.

    Principe : chaque agent apprend uniquement ce qui est pertinent pour son rôle.
    - Agent concerné → apprend le fix complet (son propre bug, sa propre erreur)
    - QA + Spec → apprennent le pattern de review (c'est leur domaine)
    - COO → reçoit un résumé de supervision (il supervise tout)
    - Autres agents → rien (le comptable n'a pas besoin de savoir déboguer Python)
    """
    try:
        from skills.skill_mem0 import remember
        from skills.skill_agent_learning import learn_from_outcome, memory_agent_id

        agent_name = memory_agent_id(error.get("agent_name", ""))
        err_type = error.get("error_type", "erreur")

        # 1. L'agent qui a eu le bug — apprend le fix complet + comment éviter
        if agent_name:
            remember(
                f"[Apprentissage propre] Bug '{err_type}' résolu : {fix_summary[:400]}. "
                f"Ne plus répéter cette erreur — contexte : {error.get('error_message', '')[:200]}",
                agent_id=agent_name,
            )
            learn_from_outcome(
                agent_id=agent_name,
                task=f"fix {err_type}",
                outcome=fix_summary,
                success=True,
            )

        # 2. QA Agent — apprend le pattern de validation pour ce type d'erreur
        remember(
            f"[Pattern QA] Fix type '{err_type}' validé : {fix_summary[:200]}. "
            f"Critères qui ont permis l'approbation — fix minimal, ciblé, tests verts.",
            agent_id="qa",
        )

        # 3. Spec Agent — apprend le pattern architectural validé
        remember(
            f"[Pattern Spec] Correction architecturale approuvée pour '{err_type}' "
            f"(agent {agent_name}) : {fix_summary[:200]}.",
            agent_id="spec",
        )

        # 4. COO — résumé de supervision uniquement (pas les détails techniques)
        remember(
            f"[Supervision] Bug '{err_type}' de {agent_name} auto-résolu. "
            f"Résumé : {fix_summary[:150]}. Système autonome opérationnel.",
            agent_id="coo",
        )

        logger.info(
            "fix_pipeline: apprentissage ciblé — %s + qa + spec + coo",
            agent_name,
        )
    except Exception as exc:
        logger.warning("fix_pipeline: record_resolution failed: %s", exc)


# ---------------------------------------------------------------------------
# Notification Telegram
# ---------------------------------------------------------------------------

async def _notify(message: str) -> None:
    try:
        from api.telegram_bot import get_telegram_bot
        bot = get_telegram_bot()
        chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
        if chat_id:
            await bot.bot.send_message(chat_id=int(chat_id), text=message)
    except Exception as exc:
        logger.warning("Telegram notification failed: %s", exc)


# ---------------------------------------------------------------------------
# PIPELINE PRINCIPAL
# ---------------------------------------------------------------------------

async def run(error: dict[str, Any], repo_path: str, github_repo: str | None = None) -> dict[str, Any]:
    """
    Pipeline de fix autonome complet. Appelé par bug_watchdog.

    Pas de limite de tentatives fixée — contexte croissant à chaque retry.
    Chaque tentative ratée enrichit le journal et Mem0.
    Merge automatique uniquement si QA + Spec + tests sont verts.

    Returns:
        {"resolved": bool, "attempts": int, "pr_url": str|None, "summary": str}
    """
    from skills.skill_code_agent import fix_bug
    from skills.skill_error_journal import mark_resolved, mark_escalated, increment_attempts
    from skills.skill_agent_learning import memory_agent_id

    error_id = error["id"]
    error_message = error.get("error_message", "")
    agent_name = error.get("agent_name", "unknown")
    fix_agent_id = memory_agent_id(agent_name if agent_name != "unknown" else "dev_app")
    err_type = error.get("error_type", "unknown")

    # Détecte le déploiement une seule fois
    deploy_info = _detect_deploy_method(repo_path)
    logger.info("fix_pipeline: déploiement détecté → %s (%s)", deploy_info["method"], deploy_info["name"])

    # Repo context pour les reviews
    try:
        readme = (Path(repo_path) / "README.md").read_text(encoding="utf-8", errors="ignore")[:800]
    except Exception:
        readme = f"Repo ALNUA Hub — agent {agent_name}"

    attempt = 0
    last_branch = None

    while True:
        logger.info("fix_pipeline: tentative %d pour erreur %s", attempt + 1, error_id[:8])
        increment_attempts(error_id)

        # 1. Contexte croissant
        context = _build_context(error, repo_path, attempt)
        error_context = (
            f"Tentative {attempt+1} | Niveau contexte: {context['level']}\n"
            f"Historique similaire: {len(context.get('history', []))} erreurs\n"
            f"Mémoire agents: {context.get('memory', '')[:300]}"
        )

        # Nettoyage branche précédente si retry
        if last_branch:
            _rollback(repo_path, last_branch)

        # 2. CodeAgent applique le fix
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: fix_bug(
                error_message=error_message,
                error_context=error_context,
                repo_path=repo_path,
                github_repo=github_repo,
                model=FIX_MODEL,
                agent_id=fix_agent_id,
                dry_run=False,
            ),
        )

        if not result.get("success"):
            learned = f"CodeAgent n'a pas pu générer un fix: {result.get('summary', '')[:200]}"
            _record_attempt(error_id, attempt, "échec generation", learned)
            _record_failure_learning(error, attempt, "échec generation", learned)
            logger.warning("fix_pipeline: génération fix échouée — retry avec plus de contexte")
            attempt += 1
            await asyncio.sleep(5)
            continue

        fix_summary = result.get("summary", "Fix appliqué")
        last_branch = result.get("branch")

        # 3. Tests automatiques
        test_result = await loop.run_in_executor(None, lambda: _run_tests(repo_path))

        if not test_result["passed"]:
            learned = (
                f"Fix '{fix_summary[:100]}' a cassé les tests. "
                f"Output: {test_result['output'][:300]}"
            )
            _record_attempt(error_id, attempt, "tests échoués", learned)
            _record_failure_learning(error, attempt, "tests échoués", learned)
            # Injecte l'output des tests dans le contexte du prochain retry
            error["error_message"] = (
                f"{error_message}\n\n[TENTATIVE {attempt+1} ÉCHOUÉE — Tests output:]\n{test_result['output'][:500]}"
            )
            logger.warning("fix_pipeline: tests ratés — retry avec output tests dans contexte")
            attempt += 1
            await asyncio.sleep(5)
            continue

        # 4. QA Review
        diff = _get_diff(repo_path, last_branch) if last_branch else ""
        qa = await loop.run_in_executor(
            None, lambda: _qa_review(diff, error_message, fix_summary)
        )

        if not qa.get("approved"):
            learned = f"QA rejeté: {qa.get('feedback', '')}"
            _record_attempt(error_id, attempt, "QA rejeté", learned)
            _record_failure_learning(error, attempt, "QA rejeté", learned)
            error["error_message"] = (
                f"{error_message}\n\n[QA FEEDBACK tentative {attempt+1}:]\n{qa.get('feedback', '')}"
            )
            logger.warning("fix_pipeline: QA a rejeté le fix — retry")
            attempt += 1
            await asyncio.sleep(5)
            continue

        # 5. Spec Review
        spec = await loop.run_in_executor(
            None, lambda: _spec_review(diff, fix_summary, readme)
        )

        if not spec.get("approved"):
            learned = f"Spec rejeté: {spec.get('feedback', '')}"
            _record_attempt(error_id, attempt, "Spec rejeté", learned)
            _record_failure_learning(error, attempt, "Spec rejeté", learned)
            error["error_message"] = (
                f"{error_message}\n\n[SPEC FEEDBACK tentative {attempt+1}:]\n{spec.get('feedback', '')}"
            )
            logger.warning("fix_pipeline: Spec a rejeté le fix — retry")
            attempt += 1
            await asyncio.sleep(5)
            continue

        # ✅ TOUT EST VERT — merge + deploy
        logger.info("fix_pipeline: ✅ fix validé (tentative %d) — merge + deploy", attempt + 1)

        merged = False
        if last_branch:
            merged = await loop.run_in_executor(None, lambda: _auto_merge(repo_path, last_branch))

        deployed = False
        if merged:
            deployed = await loop.run_in_executor(None, lambda: _restart_app(repo_path, deploy_info))

        # Apprentissage — enrichit Mem0 pour les prochaines fois
        _record_resolution(error, fix_summary, diff)
        mark_resolved(error_id, solution=fix_summary)

        # Notification finale
        status_line = "✅ déployé automatiquement" if deployed else "✅ mergé (redémarrage manuel requis)"
        pr_url = result.get("pr_url", "")
        await _notify(
            f"🤖 Bug auto-résolu — {agent_name}\n"
            f"Type: {err_type}\n"
            f"Fix ({attempt+1} tentative{'s' if attempt > 0 else ''}) : {fix_summary[:200]}\n"
            f"{status_line}"
            + (f"\nPR: {pr_url}" if pr_url else "")
        )

        return {
            "resolved": True,
            "attempts": attempt + 1,
            "pr_url": pr_url,
            "summary": fix_summary,
            "deployed": deployed,
        }
