"""
report_robo_telemetry.py — Rapporte une lecture de télémétrie IoT d'Eve au
Hub ALNUA (Phase 20, ROADMAP.md).

Aucune dépendance du Hub — POST HTTP simple. Prévu pour tourner directement
sur le Raspberry Pi d'Eve (lecture de capteurs réels), ou manuellement en
attendant.

Usage :
    python scripts/report_robo_telemetry.py \\
        --project "Eve" \\
        --power 8.4 \\
        --temperature 41.2 \\
        --cpu 37 \\
        --battery 82 \\
        --cycles 214 \\
        --autonomy 6.5

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
    parser = argparse.ArgumentParser(description="Rapporte une lecture de télémétrie IoT d'Eve au Hub ALNUA")
    parser.add_argument("--project", required=True, help="Nom du projet (ex: 'Eve')")
    parser.add_argument("--power", type=float, default=None, help="Consommation en watts")
    parser.add_argument("--temperature", type=float, default=None, help="Température en °C")
    parser.add_argument("--cpu", type=int, default=None, help="Charge CPU en %%")
    parser.add_argument("--battery", type=int, default=None, help="Niveau de batterie en %%")
    parser.add_argument("--cycles", type=int, default=None, help="Nombre de cycles de charge")
    parser.add_argument("--autonomy", type=float, default=None, help="Autonomie estimée en heures")
    parser.add_argument("--hub-url", default=os.getenv("HUB_API_URL", DEFAULT_HUB_URL))
    parser.add_argument("--hub-key", default=os.getenv("HUB_API_KEY", ""))
    args = parser.parse_args()

    if not args.hub_key:
        raise SystemExit("HUB_API_KEY manquant (variable d'env ou --hub-key)")

    project_id = resolve_project_id(args.hub_url, args.hub_key, args.project)

    payload = {
        "project_id": project_id,
        "power_w": args.power,
        "temperature_c": args.temperature,
        "cpu_pct": args.cpu,
        "battery_pct": args.battery,
        "charge_cycles": args.cycles,
        "autonomy_hours": args.autonomy,
    }

    try:
        result = _api_post(args.hub_url, args.hub_key, "/robo/telemetry", payload)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        print(f"[ERREUR] Echec du rapport ({exc.code}) : {detail}", file=sys.stderr)
        sys.exit(1)

    print(f"[OK] Telemetrie rapportee pour {args.project} ({result['id']})")


if __name__ == "__main__":
    main()
