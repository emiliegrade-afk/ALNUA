"""
add_project.py - Ajouter un nouveau projet ALNUA en une commande.

Usage :
    python scripts/add_project.py --name "Wyrdheim" --github emiliegrade-afk/wyrdheim --local C:/Dev/wyrdheim

Ce script :
  1. Clone le repo GitHub en local si le dossier n existe pas
  2. Ajoute les variables dans .env
  3. Enregistre le repo dans config/github_repos.py
  4. Insere le projet dans Supabase (table projects)
"""

import argparse
import json
import os
import re
import subprocess
import sys
import unicodedata
import urllib.request
from pathlib import Path

ROOT = Path(__file__).parent.parent


def slugify(name: str) -> str:
    # Normalise les accents (Naïa → Naia) avant de slugifier
    normalized = unicodedata.normalize("NFD", name)
    ascii_name = "".join(c for c in normalized if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]", "_", ascii_name.lower()).strip("_")


def step(msg: str):
    print(f"\n✦ {msg}")


def ok(msg: str):
    print(f"  ✅ {msg}")


def err(msg: str):
    print(f"  ❌ {msg}")
    sys.exit(1)


# ──────────────────────────────────────────────
# 1. Parse args
# ──────────────────────────────────────────────
parser = argparse.ArgumentParser(description="Ajouter un projet ALNUA")
parser.add_argument("--name", required=True, help='Nom du projet, ex: "Wyrdheim"')
parser.add_argument("--github", required=True, help="Slug GitHub, ex: emiliegrade-afk/wyrdheim")
parser.add_argument("--local", required=True, help=r"Chemin local, ex: C:\Dev\wyrdheim")
parser.add_argument(
    "--branch",
    default="app",
    choices=["app", "gaming", "robo", "hub"],
    help="Branche ALNUA (default: app)",
)
args = parser.parse_args()

name = args.name
github = args.github
local = Path(args.local)
branch = args.branch
slug = slugify(name)
env_key = slug.upper()

print(f"\n{'─'*50}")
print(f"  Ajout du projet : {name}")
print(f"  GitHub          : {github}")
print(f"  Chemin local    : {local}")
print(f"  Branche ALNUA   : {branch}")
print(f"{'─'*50}")

# ──────────────────────────────────────────────
# 2. Clone le repo
# ──────────────────────────────────────────────
step("Clonage du repo GitHub")
if local.exists():
    ok(f"Dossier {local} existe déjà — clone ignoré")
else:
    result = subprocess.run(
        ["git", "clone", f"https://github.com/{github}.git", str(local)],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        err(f"git clone échoué : {result.stderr}")
    ok(f"Cloné dans {local}")

# ──────────────────────────────────────────────
# 3. Mettre à jour .env
# ──────────────────────────────────────────────
step("Mise à jour du .env")
env_path = ROOT / ".env"
env_content = env_path.read_text(encoding="utf-8") if env_path.exists() else ""

lines_to_add = []
github_key = f"GITHUB_REPO_{env_key}"
path_key = f"REPO_PATH_{env_key}"

if github_key not in env_content:
    lines_to_add.append(f"{github_key}={github}")
    ok(f"Ajouté : {github_key}={github}")
else:
    ok(f"{github_key} déjà présent")

if path_key not in env_content:
    lines_to_add.append(f"{path_key}={local}")
    ok(f"Ajouté : {path_key}={local}")
else:
    ok(f"{path_key} déjà présent")

if lines_to_add:
    with open(env_path, "a", encoding="utf-8") as f:
        f.write("\n" + "\n".join(lines_to_add) + "\n")

# ──────────────────────────────────────────────
# 4. Enregistrer dans config/github_repos.py
# ──────────────────────────────────────────────
step("Enregistrement dans config/github_repos.py")
repos_path = ROOT / "config" / "github_repos.py"

if repos_path.exists():
    repos_content = repos_path.read_text(encoding="utf-8")
    if slug in repos_content:
        ok(f"'{slug}' déjà dans github_repos.py")
    else:
        # Cherche la fin du dict REPOS = { ... } et insère avant le }
        new_entry = (
            f'    "{slug}": {{\n'
            f'        "github": "{github}",\n'
            f'        "local": r"{local}",\n'
            f'        "branch": "{branch}",\n'
            f'    }},\n'
        )
        # Insérer avant la dernière accolade fermante du dict
        updated = re.sub(r"(REPOS\s*=\s*\{.*?)(^\})", new_entry + r"\g<2>",
                         repos_content, flags=re.DOTALL | re.MULTILINE)
        if updated == repos_content:
            # fallback : ajouter à la fin du fichier
            local_str = str(local).replace("\\", "/")
            with open(repos_path, "a", encoding="utf-8") as f:
                f.write(f'\n# {name}\nREPOS["{slug}"] = {{"github": "{github}", "local": "{local_str}", "branch": "{branch}"}}\n')
        else:
            repos_path.write_text(updated, encoding="utf-8")
        ok(f"'{slug}' ajouté dans github_repos.py")
else:
    ok("config/github_repos.py introuvable — ignoré")

# ──────────────────────────────────────────────
# 5. Insérer dans Supabase
# ──────────────────────────────────────────────
step("Insertion dans Supabase (table projects)")
try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")

    sb_url = os.getenv("SUPABASE_URL")
    sb_key = (os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY")
              or os.getenv("SUPABASE_SERVICE_ROLE_KEY"))

    if not sb_url or not sb_key:
        print("  ⚠️  SUPABASE_URL ou SUPABASE_KEY manquante — insertion skippée")
    else:
        headers = {
            "apikey": sb_key,
            "Authorization": f"Bearer {sb_key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }
        # Vérifier si déjà existant par nom
        check_req = urllib.request.Request(
            f"{sb_url}/rest/v1/projects?name=eq.{urllib.parse.quote(name)}&select=id",
            headers=headers,
        )
        import urllib.parse
        check_req = urllib.request.Request(
            f"{sb_url}/rest/v1/projects?name=eq.{urllib.parse.quote(name)}&select=id",
            headers=headers,
        )
        with urllib.request.urlopen(check_req) as r:
            existing = json.loads(r.read())
        if existing:
            ok(f"Projet '{name}' déjà dans Supabase")
        else:
            payload = json.dumps({
                "name": name,
                "branch": branch,
                "status": "dev",
                "description": f"Projet {name} — branche {branch}",
            }).encode()
            insert_req = urllib.request.Request(
                f"{sb_url}/rest/v1/projects",
                data=payload,
                headers=headers,
                method="POST",
            )
            with urllib.request.urlopen(insert_req) as r:
                result = json.loads(r.read())
            ok(f"Projet '{name}' inséré dans Supabase (id: {result[0]['id']})")
except Exception as e:
    print(f"  ⚠️  Supabase skippé : {e}")

# ──────────────────────────────────────────────
# Résumé
# ──────────────────────────────────────────────
print(f"\n{'─'*50}")
print(f"  🎉 Projet {name} ajouté avec succès !")
print("  Relance l'API pour que le pipeline le détecte.")
print(f"{'─'*50}\n")
