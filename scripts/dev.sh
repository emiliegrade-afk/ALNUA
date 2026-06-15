#!/usr/bin/env bash
# dev.sh — Start local API via Docker (dev compose)
set -euo pipefail
cd "$(dirname "$0")/.."
docker compose -f docker-compose.dev.yml up --build "$@"
