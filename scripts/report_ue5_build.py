"""
report_ue5_build.py — Rapporte un build UE5 réel au Hub ALNUA (Phase 16, ROADMAP.md).

Ce script n'a besoin d'aucune dépendance du Hub — il peut tourner depuis une
machine de build UE5 séparée. Il ne fait qu'un POST HTTP vers /gaming/builds.

Prérequis (aucun n'existe encore dans cet environnement, à mettre en place
côté studio) :
  - Un pipeline qui compile/package Wyrdheim (UAT BuildCookRun, Jenkins, etc.)
  - Ce script appelé à la fin de ce pipeline, avec les vraies métriques

Usage :
    python scripts/report_ue5_build.py \\
        --project "Wyrdheim Online" \\
        --branch develop \\
        --build 1287 \\
        --status success \\
        --engine-version 5.8 \\
        --game-version 0.4.2 \\
        --fps 58.4 \\
        --crashes 0 \\
        --draw-calls 2400 \\
        --commit abc1234

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
    parser = argparse.ArgumentParser(description="Rapporte un build UE5 au Hub ALNUA")
    parser.add_argument("--project", required=True, help="Nom du projet (ex: 'Wyrdheim Online')")
    parser.add_argument("--branch", required=True, help="Branche Git buildée")
    parser.add_argument("--build", required=True, help="Numéro de build (ex: 1287)")
    parser.add_argument("--status", default="success", choices=["success", "failed", "running"])
    parser.add_argument("--engine-version", default="5.8")
    parser.add_argument("--game-version", default=None, help="Version du jeu (ex: 0.4.2)")
    parser.add_argument("--fps", type=float, default=None, help="FPS moyen mesuré")
    parser.add_argument("--crashes", type=int, default=None, help="Nombre de crashs constatés")
    parser.add_argument("--draw-calls", type=int, default=None)
    parser.add_argument("--commit", default=None, help="SHA du commit buildé")
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
        "build_number": str(args.build),
        "game_version": args.game_version,
        "engine_version": args.engine_version,
        "status": args.status,
        "fps_avg": args.fps,
        "crashes": args.crashes,
        "draw_calls": args.draw_calls,
        "commit_sha": args.commit,
        "notes": args.notes,
    }

    try:
        result = _api_post(args.hub_url, args.hub_key, "/gaming/builds", payload)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        print(f"[ERREUR] Echec du rapport de build ({exc.code}) : {detail}", file=sys.stderr)
        sys.exit(1)

    print(f"[OK] Build #{result['build_number']} rapporte pour {args.project} ({result['id']})")


if __name__ == "__main__":
    main()
