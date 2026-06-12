FROM python:3.12-slim

# ── System deps ─────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# ── Python deps ─────────────────────────────────────────────
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# ── Application code ────────────────────────────────────────
COPY backend/ .
# content.json is needed by the seed command
COPY frontend/content.json /app/content.json

# ── Entrypoint ──────────────────────────────────────────────
EXPOSE 8001
CMD ["sh", "-c", "\
    python manage.py migrate --noinput && \
    python manage.py seed_content --path /app/content.json && \
    gunicorn config.wsgi:application --bind 0.0.0.0:8001 --workers 4 \
"]
