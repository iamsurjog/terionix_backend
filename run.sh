#!/usr/bin/env bash
# ── Run the Django backend without Docker ────────────────────────────
# Loads env vars from .env, activates the venv, and starts the dev server.
set -a                          # automatically export all sourced vars
source "$(dirname "$0")/.env"
set +a

cd "$(dirname "$0")"

if [ ! -d .venv ]; then
    echo "❌  Virtual environment not found. Run setup.sh first."
    exit 1
fi
source .venv/bin/activate

echo "🚀  Starting backend on http://0.0.0.0:8001"
exec python manage.py runserver 0.0.0.0:8001
