"""
test_fix_pipeline.py — Test bout-en-bout du pipeline autonome.

Ce script :
1. Injecte un vrai bug dans un fichier temporaire
2. Logue l'erreur dans agent_error_journal
3. Lance fix_pipeline.run() directement
4. Vérifie que le fix a été appliqué

Lance avec :
    cd C:/Dev/ALUNA_HUB
    python scripts/test_fix_pipeline.py
"""
import asyncio
import os
import sys
import tempfile
from pathlib import Path

# Ajoute le root au path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Charge le .env
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

REPO_PATH = os.getenv("HUB_REPO_PATH", "C:/Dev/ALUNA_HUB")


async def main():
    print("=" * 60)
    print("TEST — Pipeline autonome ALNUA")
    print("=" * 60)

    # 1. Crée un fichier Python avec un bug volontaire
    test_file = Path(REPO_PATH) / "scripts" / "_test_buggy_file.py"
    buggy_code = '''"""Fichier de test avec bug volontaire."""

def calculate_average(numbers):
    # BUG: division par zéro si liste vide
    total = sum(numbers)
    return total / len(numbers)  # ZeroDivisionError si numbers=[]

def get_user_name(user_dict):
    # BUG: KeyError si "name" absent
    return user_dict["name"]  # devrait utiliser .get()

if __name__ == "__main__":
    print(calculate_average([]))  # Plantera ici
'''
    test_file.write_text(buggy_code, encoding="utf-8")
    print(f"✅ Fichier bugué créé : {test_file.name}")

    # 2. Simule l'erreur que ce bug produirait
    error_message = """Traceback (most recent call last):
  File "_test_buggy_file.py", line 13, in <module>
    print(calculate_average([]))
  File "_test_buggy_file.py", line 5, in calculate_average
    return total / len(numbers)
ZeroDivisionError: division by zero"""

    fake_error = {
        "id": "test-error-001",
        "agent_name": "dev_app",
        "error_type": "ZeroDivisionError",
        "error_message": error_message,
        "context": "Test pipeline autonome",
        "attempts": 0,
    }

    print(f"✅ Erreur simulée : ZeroDivisionError dans {test_file.name}")

    # 3. Lance fix_pipeline directement (sans Supabase pour ce test)
    print("\n🚀 Lancement fix_pipeline...")
    print("   CodeAgent → lit le fichier → appelle LLM → applique fix")

    from skills.skill_code_agent import fix_bug

    result = fix_bug(
        error_message=error_message,
        error_context="Bug détecté dans script de test ALNUA",
        repo_path=REPO_PATH,
        hint_files=["scripts/_test_buggy_file.py"],
        dry_run=False,
    )

    print("\n" + "=" * 60)
    if result.get("success"):
        print("✅ FIX APPLIQUÉ")
        print(f"   Fichiers modifiés : {result.get('fixed_files')}")
        print(f"   Résumé : {result.get('summary')}")
        print(f"   Branche : {result.get('branch', 'N/A')}")
        print(f"   PR : {result.get('pr_url', 'N/A')}")

        # Vérifie que le fichier a bien changé
        new_content = test_file.read_text(encoding="utf-8")
        if "ZeroDivisionError" not in new_content or ".get(" in new_content:
            print("✅ Contenu du fichier corrigé confirmé")
        else:
            print("⚠️  Le fichier ne semble pas corrigé — vérifie manuellement")

        print("\n📄 Nouveau contenu :")
        print("-" * 40)
        print(new_content[:800])
    else:
        print("❌ ÉCHEC")
        print(f"   Raison : {result.get('summary')}")

    # 4. Test skill_agent_learning
    print("\n" + "=" * 60)
    print("TEST — Apprentissage agent")
    from skills.skill_agent_learning import learn_from_outcome
    learn_from_outcome(
        agent_id="dev_app",
        task="Corriger ZeroDivisionError dans calculate_average()",
        outcome="Fix appliqué : ajout vérification len(numbers) == 0 avant division",
        success=True,
        blocking=True,  # bloquant pour le test
    )
    print("✅ Leçon enregistrée dans Mem0 pour dev_app")

    # 5. Test veille web (juste une recherche)
    print("\n" + "=" * 60)
    print("TEST — Veille web")
    from skills.skill_web_research import research_domain
    print("🔍 Recherche 'Python security vulnerabilities 2026' pour dev_app...")
    research_domain("dev_app", topic="Python security patch 2026", blocking=True)
    print("✅ Veille terminée (résultats dans Mem0 si duckduckgo-search installé)")

    # Nettoyage
    print("\n" + "=" * 60)
    cleanup = input("Supprimer le fichier de test ? (o/n) : ").strip().lower()
    if cleanup == "o":
        test_file.unlink(missing_ok=True)
        print("✅ Fichier de test supprimé")

    print("\n✅ TEST TERMINÉ")


if __name__ == "__main__":
    asyncio.run(main())
