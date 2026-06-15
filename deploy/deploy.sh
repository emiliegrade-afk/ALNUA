#!/bin/bash
# deploy.sh — Redéployer le Hub après une mise à jour
# Usage : ./deploy/deploy.sh

set -e

REPO_DIR="/home/alnua/hub"
cd "$REPO_DIR"

echo "📦 Récupération du code..."
git pull origin main

echo "🐳 Rebuild + redémarrage..."
docker compose build hub_api hub_bot
docker compose up -d --no-deps hub_api hub_bot

echo "⏳ Attente démarrage..."
for i in $(seq 1 12); do
  if curl -sf http://127.0.0.1:8000/health >/dev/null; then
    echo "✅ API OK"
    break
  fi
  sleep 5
  if [ "$i" -eq 12 ]; then
    echo "❌ API KO — health check timeout"
    docker compose logs --tail=40 hub_api
    exit 1
  fi
done

echo "📋 Logs récents :"
docker compose logs --tail=20 hub_api
