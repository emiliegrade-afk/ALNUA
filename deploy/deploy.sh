#!/bin/bash
# deploy.sh — Redéployer le Hub après une mise à jour
# Usage : ./deploy/deploy.sh

set -e

REPO_DIR="/home/alnua/hub"
cd $REPO_DIR

echo "📦 Récupération du code..."
git pull origin main

echo "🐳 Rebuild + redémarrage..."
docker compose build --no-cache hub_api hub_bot
docker compose up -d --no-deps hub_api hub_bot

echo "⏳ Attente démarrage..."
sleep 5

echo "🔍 Health check..."
curl -f http://localhost:8000/health && echo "✅ API OK" || echo "❌ API KO"

echo "📋 Logs récents :"
docker compose logs --tail=20 hub_api
