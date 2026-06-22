#!/usr/bin/env bash
# ── Run the Django backend without Docker ────────────────────────────
# Loads env vars from .env, activates the venv, and starts the dev server.
set -a                          # automatically export all sourced vars
source "$(dirname "$0")/.env"
set +a

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Now it will reliably find .venv no matter where you call this script from!
if [ ! -d "$SCRIPT_DIR/.venv" ]; then
    echo "❌  Virtual environment not found. Run setup.sh first."
    exit 1
fi
source "$SCRIPT_DIR/.venv/bin/activate"

echo "🚀  Starting backend on http://0.0.0.0:8001"
exec python manage.py runserver 0.0.0.0:8001
