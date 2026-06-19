#!/usr/bin/env bash
# scripts/migrate.sh <user@host> <ruta-en-destino>
# Migra una instalación ya operativa al servidor destino.
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "uso: $0 user@host /ruta/destino" >&2; exit 1
fi
TARGET_HOST="$1"
TARGET_DIR="$2"

echo "→ Generando backup local…"
./scripts/backup.sh
LAST=$(ls -1dt ./backups/*/ | head -1 | sed 's:/$::')

echo "→ Sincronizando código a $TARGET_HOST:$TARGET_DIR …"
rsync -avz --delete \
  --exclude='backups/' \
  --exclude='.git/' \
  --exclude='node_modules/' \
  --exclude='.venv/' \
  --exclude='__pycache__/' \
  ./ "$TARGET_HOST:$TARGET_DIR/"

echo "→ Sincronizando último backup…"
rsync -avz "$LAST" "$TARGET_HOST:$TARGET_DIR/backups/"

echo "→ Restaurando en destino y arrancando stack…"
ssh "$TARGET_HOST" "
  set -e
  cd $TARGET_DIR
  if [[ ! -f .env ]]; then
    echo 'ERROR: .env no existe en $TARGET_HOST:$TARGET_DIR. Copialo y editalo antes de migrar.' >&2
    exit 1
  fi
  docker compose -f docker-compose.prod.yml up -d postgres minio
  sleep 5
  ./scripts/restore.sh backups/$(basename $LAST)
  docker compose -f docker-compose.prod.yml up -d --build
  sleep 5
  curl -fsS http://localhost/readyz && echo OK
"

echo "Migración OK → verificá https://<dominio>/readyz"
