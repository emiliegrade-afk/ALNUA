"""Bootstrap CreatorFlow: dossier → package CEO → approve → dispatch → livrables disque."""
from __future__ import annotations

import json
import sys
import time
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agents.rnd_ceo_agent import RndCeoAgent  # noqa: E402
from config.paths import get_alnua_workspace  # noqa: E402
from services.rnd_repository import get_rnd_repository  # noqa: E402

SECTION_KEYS = [
    ("problem", "Problème", "Les créateurs perdent 20h/semaine en logistique multi-plateformes."),
    ("solution", "Solution", "CreatorFlow automatise import, calendrier et export vers 3 plateformes."),
    ("market", "Marché", "Concurrents Buffer/Hootsuite — gap sur l'IA créative et le workflow solo."),
    ("mvp", "MVP", "Import assets, calendrier éditorial, export YouTube/Instagram/TikTok."),
    ("feasibility", "Faisabilité", "Next.js + Supabase + OpenRouter — stack ALNUA existante."),
    ("business_case", "Business case", "SaaS 16-49€/mois, break-even M18, modèle ai_solo."),
    ("risks", "Risques", "Dépendance APIs Meta/TikTok, rate limits export."),
    ("decision", "Décision", "Recommandation GO — MVP scope réduit sans TikTok v1."),
]

FINANCE_JSON = {
    "capex_eur": 4200,
    "capex_dev_eur": 3500,
    "capex_llm_agents_eur": 400,
    "opex_monthly_eur": 45,
    "verdict_finance": "viable",
    "revenue_hypothesis": {
        "pricing_model": {
            "model_type": "subscription",
            "blended_arpu_eur": 32,
            "tiers": [
                {"name": "Starter", "price_eur": 16.99, "mix_pct": 0.5},
                {"name": "Pro", "price_eur": 49.0, "mix_pct": 0.5},
            ],
        },
        "m12_monthly_run_rate_eur": 1984,
    },
}


def _ensure_creatorflow_dossier(repo, agent: RndCeoAgent) -> str:
    existing = repo.db.select("rnd_dossiers", filters={"slug": "creatorflow"}, limit=1)
    if existing:
        dossier_id = str(existing[0]["id"])
        print(f"Dossier existant creatorflow → {dossier_id}")
        return dossier_id

    legacy_id = f"creatorflow_{uuid.uuid4().hex[:8]}"
    idea_row = repo.db.insert(
        "rnd_ideas",
        {
            "legacy_id": legacy_id,
            "title": "CreatorFlow",
            "description": "Pipeline IA pour créateurs — distribution multi-plateformes automatisée.",
            "domain": "saas",
            "source": "bootstrap",
            "status": "evaluated",
            "agent_verdict": "GO",
            "score": 85,
        },
    )
    idea_row = idea_row[0] if isinstance(idea_row, list) else idea_row

    dossier_row = repo.db.insert(
        "rnd_dossiers",
        {
            "idea_id": idea_row["id"],
            "slug": "creatorflow",
            "title": "CreatorFlow",
            "tagline": "Pipeline IA pour créateurs",
            "domain": "saas",
            "branch": "app",
            "status": "ready_for_ceo",
        },
    )
    dossier_row = dossier_row[0] if isinstance(dossier_row, list) else dossier_row
    dossier_id = str(dossier_row["id"])

    for sort_order, (key, title, content) in enumerate(SECTION_KEYS):
        repo.db.insert(
            "rnd_dossier_sections",
            {
                "dossier_id": dossier_id,
                "section_key": key,
                "title": title,
                "content_md": content,
                "sort_order": (sort_order + 1) * 10,
                "status": "validated",
            },
        )

    repo.db.update(
        "rnd_dossiers",
        dossier_id,
        {
            "finance_json": FINANCE_JSON,
            "committee_report_md": (
                "## Décisions actées\n"
                "- MVP validé sans TikTok v1\n"
                "- Pricing Starter 16,99€ / Pro 49€\n\n"
                "**Verdict :** GO"
            ),
        },
    )
    print(f"Dossier creatorflow créé → {dossier_id}")
    return dossier_id


def _wait_execution(repo, dossier_id: str, *, timeout_s: int = 900) -> dict:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        rows = repo.db.select("rnd_dossiers", filters={"id": dossier_id}, limit=1)
        if not rows:
            break
        dj = rows[0].get("dispatch_json") or {}
        if isinstance(dj, str):
            dj = json.loads(dj)
        status = dj.get("execution_status")
        if status in ("completed", "failed"):
            return rows[0]
        print(f"  … exécution agents ({status or 'pending'}) — attente 15s")
        time.sleep(15)
    return repo.db.select("rnd_dossiers", filters={"id": dossier_id}, limit=1)[0]


def _list_workspace_files(slug: str) -> list[str]:
    root = get_alnua_workspace()
    found: list[str] = []
    for p in root.rglob("*"):
        if p.is_file() and slug in str(p):
            found.append(str(p.relative_to(root)))
    manifest = root / f"{slug}.manifest.json"
    if manifest.is_file():
        found.append(str(manifest.relative_to(root)))
    return sorted(set(found))


def main() -> int:
    repo = get_rnd_repository()
    if not repo._use_db:
        print("ERROR: Supabase indisponible")
        return 1

    agent = RndCeoAgent()
    dossier_id = _ensure_creatorflow_dossier(repo, agent)
    dossier = repo.get_dossier(dossier_id)
    if not dossier:
        print("ERROR: dossier introuvable après création")
        return 1

    pkg = agent.get_package(dossier_id)
    if not pkg.get("package"):
        print("Génération package CEO…")
        agent.generate_package(dossier_id, force=True)

    dossier = repo.get_dossier(dossier_id)
    if dossier and dossier.ceo_status != "approved":
        print("Validation CEO (approved)…")
        agent.record_ceo_decision(
            dossier_id,
            ceo_status="approved",
            ceo_note="GO — lancer conception CreatorFlow (bootstrap Phase 9)",
        )

    dispatch_status = repo.db.select("rnd_dossiers", filters={"id": dossier_id}, limit=1)[0]
    if dispatch_status.get("dispatch_status") != "dispatched":
        print("Dispatch COO + exécution agents (LLM réels, ~5-10 min)…")
        agent.dispatch_to_coo(dossier_id)
    else:
        print("Dispatch déjà effectué — relance exécution agents…")
        agent.kickoff_execution(dossier_id)

    final = _wait_execution(repo, dossier_id)
    wv = final.get("workspace_validation") or {}
    if isinstance(wv, str):
        wv = json.loads(wv)

    print("\n=== RÉSULTAT ===")
    print(f"workspace_path: {final.get('workspace_path')}")
    print(f"workspace_validation: {json.dumps(wv, indent=2, ensure_ascii=False)}")
    print(f"dispatch_status: {final.get('dispatch_status')}")

    files = _list_workspace_files("creatorflow")
    print(f"\nFichiers disque ({len(files)}):")
    for f in files:
        print(f"  - {f}")

    if wv.get("success"):
        print("\nOK — livrables Phase 9 validés.")
        return 0
    missing = wv.get("missing_files") or []
    if missing:
        print(f"\nPARTIEL — fichiers manquants: {missing}")
    return 0 if files else 1


if __name__ == "__main__":
    sys.exit(main())
