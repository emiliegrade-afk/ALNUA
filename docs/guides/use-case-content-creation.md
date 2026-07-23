# Use case — Pipeline contenu

## Objectif
Transformer un brief en contenu multi-plateforme (LinkedIn, Discord, blog).

## Flow
1. **Hub** → `/content` ou API `POST /agents/content/generate`
2. **Sofia** (content) rédige les formats
3. **Camille** (marketing) adapte hooks et CTA
4. Résultat stocké + points compétition

## Exemple (assistant)
```
Lance un sprint contenu : retrospective Academy cette semaine, LinkedIn + Discord
```

## API
```bash
curl -X POST http://localhost:8003/v1/agents/content/generate \
  -H "X-Hub-Key: $HUB_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"project_id":"...", "dev_log":"...", "content_types":["linkedin"]}'
```
