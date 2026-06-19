#!/usr/bin/env bash
# scripts/restore.sh <dir-de-backup>
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "uso: $0 ./backups/<timestamp>" >&2; exit 1
fi
DIR="$1"
set -a; . ./.env; set +a

echo "→ verificando integridad…"
( cd "$DIR" && sha256sum --check MANIFEST.sha256 )

echo "→ restaurando Postgres…"
cat "$DIR/db.dump" | docker compose -f docker-compose.prod.yml exec -T postgres \
  pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists

echo "→ restaurando MinIO…"
docker compose -f docker-compose.prod.yml run --rm \
  -v "$(pwd)/${DIR}/minio:/mirror" minio-init \
  sh -c "mc alias set local http://minio:9000 \$MINIO_ROOT_USER \$MINIO_ROOT_PASSWORD && mc mirror --overwrite /mirror/ local/\$MINIO_BUCKET"

echo "Restore OK desde $DIR"
