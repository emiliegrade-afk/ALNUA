"""
report_robo_build.py — Rapporte une itération hardware/firmware d'Eve au Hub
ALNUA (Phase 19, ROADMAP.md).

Aucune dépendance du Hub — POST HTTP simple, peut tourner depuis n'importe
quelle machine.

Usage :
    python scripts/report_robo_build.py \\
        --project "Eve" \\
        --branch develop \\
        --stage Prototype \\
        --version 0.4.2 \\
        --pcb-revision "Rev C" \\
        --firmware fw-2.3 \\
        --tests-passed 92 \\
        --open-issues 3

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
    parser = argparse.ArgumentParser(description="Rapporte une itération hardware/firmware d'Eve au Hub ALNUA")
    parser.add_argument("--project", required=True, help="Nom du projet (ex: 'Eve')")
    parser.add_argument("--branch", required=True)
    parser.add_argument("--stage", default="Prototype", choices=["Prototype", "V2", "V3", "Certification", "Production"])
    parser.add_argument("--version", default=None)
    parser.add_argument("--pcb-revision", default=None)
    parser.add_argument("--firmware", default=None)
    parser.add_argument("--tests-passed", type=int, default=None, help="Pourcentage de tests passés (0-100)")
    parser.add_argument("--open-issues", type=int, default=None)
    parser.add_argument("--notes", default="")
    parser.add_argument("--hub-url", default=os.getenv("HUB_API_URL", DEFAULT_HUB_URL))
    parser.add_argument("--hub-key", default=os.getenv("HUB_API_KEY", ""))
    args = parser.parse_args()

    if not args.hub_key:
        raise SystemExit("HUB_API_KEY manquant (variable d'env ou --hub-key)")

    project_id = resolve_project_id(args.hub_url, args.hub_key, args.project)

    payload = {
        "project_id": project_id,
        "branch": args.branch,
        "stage": args.stage,
        "version": args.version,
        "pcb_revision": args.pcb_revision,
        "firmware_version": args.firmware,
        "tests_passed_pct": args.tests_passed,
        "open_issues": args.open_issues,
        "notes": args.notes,
    }

    try:
        result = _api_post(args.hub_url, args.hub_key, "/robo/builds", payload)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        print(f"[ERREUR] Echec du rapport ({exc.code}) : {detail}", file=sys.stderr)
        sys.exit(1)

    print(f"[OK] Build {args.stage}/{args.branch} rapporte pour {args.project} ({result['id']})")


if __name__ == "__main__":
    main()
