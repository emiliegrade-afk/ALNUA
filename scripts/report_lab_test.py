"""
report_lab_test.py — Rapporte un résultat de banc de test au Hub ALNUA
(Phase 19, ROADMAP.md — Laboratoire).

Aucune dépendance du Hub — POST HTTP simple. À lancer après un vrai essai
(banc thermique, vibratoire, électrique, salle blanche...).

Usage :
    python scripts/report_lab_test.py \\
        --project "Eve" \\
        --category "Batteries" \\
        --name "Endurance pack 4S2P" \\
        --status pass \\
        --value "94%"

Variables d'env :
    HUB_API_URL   URL de base de l'API Hub (défaut : http://127.0.0.1:8003)
    HUB_API_KEY   Clé d'authentification (obligatoire, header X-Hub-Key)
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request

DEFAULT_HUB_URL = "http://127.0.0.1:8003"


def _api_get(base_url: str, api_key: str, path: str) -> list | dict:
    req = urllib.request.Request(f"{base_url}{path}", headers={"X-Hub-Key": api_key})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _api_post(base_url: str, api_key: str, path: str, payload: dict) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{base_url}{path}",
        data=data,
        method="POST",
        headers={"X-Hub-Key": api_key, "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def resolve_project_id(base_url: str, api_key: str, project_name: str) -> str:
    projects = _api_get(base_url, api_key, "/projects")
    for p in projects:
        if p["name"].strip().lower() == project_name.strip().lower():
            return p["id"]
    names = ", ".join(p["name"] for p in projects)
    raise SystemExit(f"Projet introuvable : {project_name!r}. Projets disponibles : {names}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Rapporte un résultat de banc de test au Hub ALNUA")
    parser.add_argument("--project", required=True, help="Nom du projet (ex: 'Eve')")
    parser.add_argument("--category", required=True, help="Ex: Batteries, Capteurs, Prototypes...")
    parser.add_argument("--name", required=True, help="Nom du test")
    parser.add_argument("--status", default="in_progress", choices=["pass", "fail", "in_progress"])
    parser.add_argument("--value", dest="measured_value", default=None, help="Valeur mesurée (ex: '94%', '23.4°C')")
    parser.add_argument("--notes", default="")
    parser.add_argument("--hub-url", default=os.getenv("HUB_API_URL", DEFAULT_HUB_URL))
    parser.add_argument("--hub-key", default=os.getenv("HUB_API_KEY", ""))
    args = parser.parse_args()

    if not args.hub_key:
        raise SystemExit("HUB_API_KEY manquant (variable d'env ou --hub-key)")

    project_id = resolve_project_id(args.hub_url, args.hub_key, args.project)

    payload = {
        "project_id": project_id,
        "category": args.category,
        "name": args.name,
        "status": args.status,
        "measured_value": args.measured_value,
        "notes": args.notes,
    }

    try:
        result = _api_post(args.hub_url, args.hub_key, "/robo/lab-tests", payload)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        print(f"[ERREUR] Echec du rapport ({exc.code}) : {detail}", file=sys.stderr)
        sys.exit(1)

    print(f"[OK] Test '{args.name}' ({args.status}) rapporte pour {args.project} ({result['id']})")


if __name__ == "__main__":
    main()
