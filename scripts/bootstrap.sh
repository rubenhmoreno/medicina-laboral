#!/usr/bin/env bash
# scripts/bootstrap.sh — primera instalación en un servidor.
set -euo pipefail

if [[ ! -f .env ]]; then
  echo "ERROR: copiá .env.example a .env y completá los valores antes de correr bootstrap." >&2
  exit 1
fi

set -a; . ./.env; set +a

echo "→ Levantando dependencias (postgres + minio)…"
docker compose -f docker-compose.prod.yml up -d postgres minio

echo "→ Esperando a postgres…"
until docker compose -f docker-compose.prod.yml exec -T postgres pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB" >/dev/null 2>&1; do
  sleep 1
done

echo "→ Creando bucket en MinIO (si no existe)…"
docker compose -f docker-compose.prod.yml run --rm minio-init || true

echo "→ Ejecutando migraciones…"
docker compose -f docker-compose.prod.yml run --rm backend uv run alembic upgrade head

echo "→ Seed (admin desde .env si no existe)…"
docker compose -f docker-compose.prod.yml run --rm \
  -e ADMIN_EMAIL -e ADMIN_PASSWORD backend uv run python scripts/seed_dev.py

echo "→ Levantando backend + nginx…"
docker compose -f docker-compose.prod.yml up -d

echo "OK → curl -fsS http://localhost/readyz"
