"""
sync_ue5_assets.py — Synchronise un vrai inventaire d'assets vers le Hub ALNUA
(Phase 17, ROADMAP.md).

Aucune dépendance du Hub — tourne depuis n'importe quelle machine ayant accès
au dossier d'assets réel (ex: le projet Wyrdheim, sur un disque séparé du Hub).
Scanne récursivement un dossier et pousse l'inventaire complet (nom, catégorie
= dossier parent, type = extension, taille, date de modification réelles).
Chaque exécution remplace l'inventaire existant du projet par l'état actuel
du dossier — pense à relancer après un ajout/suppression d'assets.

Usage :
    python scripts/sync_ue5_assets.py \\
        --project "Wyrdheim Online" \\
        --root "D:/Wyrdheim/Content"

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
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_HUB_URL = "http://127.0.0.1:8003"

EXTENSION_TYPES = {
    ".uasset": "Blueprint",
    ".umap": "Niveau",
    ".png": "Texture",
    ".tga": "Texture",
    ".jpg": "Texture",
    ".jpeg": "Texture",
    ".hdr": "Texture",
    ".wav": "Son",
    ".mp3": "Son",
    ".ogg": "Son",
    ".fbx": "Mesh",
    ".obj": "Mesh",
    ".anim": "Animation",
}


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
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def resolve_project_id(base_url: str, api_key: str, project_name: str) -> str:
    projects = _api_get(base_url, api_key, "/projects")
    for p in projects:
        if p["name"].strip().lower() == project_name.strip().lower():
            return p["id"]
    names = ", ".join(p["name"] for p in projects)
    raise SystemExit(f"Projet introuvable : {project_name!r}. Projets disponibles : {names}")


def scan_folder(root: Path) -> list[dict]:
    assets: list[dict] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        ext = path.suffix.lower()
        asset_type = EXTENSION_TYPES.get(ext, "Autre")
        category = path.parent.name if path.parent != root else "Racine"
        stat = path.stat()
        modified = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()
        assets.append(
            {
                "category": category,
                "name": path.stem,
                "asset_type": asset_type,
                "file_path": str(path.relative_to(root)),
                "size_bytes": stat.st_size,
                "modified_at": modified,
            }
        )
    return assets


def main() -> None:
    parser = argparse.ArgumentParser(description="Synchronise un inventaire d'assets réel vers le Hub ALNUA")
    parser.add_argument("--project", required=True, help="Nom du projet (ex: 'Wyrdheim Online')")
    parser.add_argument("--root", required=True, help="Dossier à scanner (ex: le dossier Content d'un projet UE5)")
    parser.add_argument("--hub-url", default=os.getenv("HUB_API_URL", DEFAULT_HUB_URL))
    parser.add_argument("--hub-key", default=os.getenv("HUB_API_KEY", ""))
    args = parser.parse_args()

    if not args.hub_key:
        raise SystemExit("HUB_API_KEY manquant (variable d'env ou --hub-key)")

    root = Path(args.root)
    if not root.is_dir():
        raise SystemExit(f"Dossier introuvable : {root}")

    project_id = resolve_project_id(args.hub_url, args.hub_key, args.project)
    assets = scan_folder(root)

    if not assets:
        print(f"[INFO] Aucun fichier trouve dans {root} — inventaire vide envoye quand meme.")

    try:
        result = _api_post(
            args.hub_url,
            args.hub_key,
            "/gaming/assets/sync",
            {"project_id": project_id, "assets": assets},
        )
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        print(f"[ERREUR] Echec de synchronisation ({exc.code}) : {detail}", file=sys.stderr)
        sys.exit(1)

    print(f"[OK] {result['synced']} assets synchronises pour {args.project} depuis {root}")


if __name__ == "__main__":
    main()
