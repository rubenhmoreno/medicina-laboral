#!/usr/bin/env bash
# scripts/backup.sh — corre vía cron. Salida: ./backups/<timestamp>/
set -euo pipefail

set -a; . ./.env; set +a

TS=$(date -u +%Y-%m-%dT%H-%M-%SZ)
OUT="./backups/${TS}"
mkdir -p "$OUT" "$OUT/minio"

echo "→ pg_dump..."
docker compose -f docker-compose.prod.yml exec -T postgres \
  pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc -Z9 > "$OUT/db.dump"

echo "→ pg_dump auditoría (separado)..."
docker compose -f docker-compose.prod.yml exec -T postgres \
  pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t auditoria -Fc -Z9 > "$OUT/auditoria.dump"

echo "→ mirror MinIO..."
docker compose -f docker-compose.prod.yml run --rm \
  -v "$(pwd)/${OUT}/minio:/mirror" minio-init \
  sh -c "mc alias set local http://minio:9000 \$MINIO_ROOT_USER \$MINIO_ROOT_PASSWORD && mc mirror --overwrite local/\$MINIO_BUCKET /mirror/"

echo "→ manifest sha256..."
( cd "$OUT" && sha256sum db.dump auditoria.dump > MANIFEST.sha256 )

echo "→ retención 30 días..."
find ./backups -mindepth 1 -maxdepth 1 -type d -mtime +30 -exec rm -rf {} +

echo "Backup OK → $OUT"
