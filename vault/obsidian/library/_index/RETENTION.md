# Politique de rétention — vault library Obsidian

> Ajoutée le 2026-08-09 (Phase C / BUG-016). Objectif : empêcher l'explosion de
> notes quasi-doublons sous `vault/obsidian/library/`.

## Règles

1. **Une note canonique par sujet** — le slug de sujet (`slugify_topic`) est la clé.
   Un nouvel export **écrase** ou met à jour la note existante ; il ne crée pas un
   second fichier `Sujet-<hash8>.md`.
2. **Le catalogue est la source d'index** — `data/topic_catalog.json` +
   `library/_index/TOPICS.md` listent les sujets. Les agents lisent le catalogue
   avant d'ouvrir des notes.
3. **Ne pas committer les dumps massifs** — les corps `library/{bureau}/*.md` sont
   des artefacts d'export (régénérables via `python scripts/export_library_to_vault.py`).
   Ils sont **gitignorés** (sauf `_index/`). Le catalogue JSON reste trackable s'il
   est utile au runtime.
4. **Dédup one-shot** — les centaines de notes untracked déjà présentes sur disque
   peuvent être supprimées localement après un export propre ; elles ne doivent
   jamais entrer dans `git add`.

## Commandes

```bash
python scripts/export_library_to_vault.py
# optionnel : --index-chroma
```

## Suivi

- BUG-016 (Audit 002) — policy + gitignore livrés en Phase C.
- Amélioration code export (overwrite-by-slug au lieu de hash unique) : Phase D
  ou ticket dédié si les doublons continuent après ignore.
