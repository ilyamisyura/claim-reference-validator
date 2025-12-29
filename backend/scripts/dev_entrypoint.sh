#!/bin/sh
set -e

export PYTHONPATH="/app:${PYTHONPATH}"

echo "[dev] Waiting for database..."
if command -v uv >/dev/null 2>&1; then
  uv run -m scripts.wait_for_db
else
  python -m scripts.wait_for_db
fi

if [ "${AUTO_MIGRATE:-true}" = "true" ]; then
  echo "[dev] Running alembic migrations..."
  if command -v uv >/dev/null 2>&1; then
    uv run alembic upgrade head || true
  else
    alembic upgrade head || true
  fi
fi

echo "[dev] Starting FastAPI dev server..."
exec fastapi dev --host 0.0.0.0 app/main.py
