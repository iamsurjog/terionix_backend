#!/usr/bin/env bash
# ── Run the Django backend without Docker ────────────────────────────
# Loads env vars from .env, activates the venv, and starts the dev server.
source "$(dirname "$0")/.env"
set +a

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Check if the environment folder exists
if [ ! -d "$SCRIPT_DIR/.venv" ]; then
    echo "❌ Virtual environment not found. Run setup.sh first."
    exit 1
fi

echo "🚀 Starting backend on http://0.0.0.0:8001"

# CRITICAL FIX: Directly call the python binary inside the .venv 
exec "$SCRIPT_DIR/.venv/bin/python" manage.py runserver 0.0.0.0:8001
