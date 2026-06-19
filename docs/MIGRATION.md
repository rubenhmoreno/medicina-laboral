# Migración entre servidores

Este runbook está pensado para que Claude Code (o un humano) pueda mover el sistema
medicia-laboral de un servidor a otro siguiendo pasos secuenciales sin contexto adicional.

## 0) Pre-requisitos en el servidor destino

- Linux x86_64 (Ubuntu 24.04 recomendado)
- Docker Engine ≥ 25, Docker Compose ≥ v2.27
- Acceso SSH al servidor desde la máquina origen
- Puertos 80/443 libres
- Disco con espacio ≥ 2× el tamaño actual de `backups/`
- (Opcional) Dominio con DNS apuntando al servidor para TLS automático

## 1) Primera instalación

```bash
ssh user@servidor
sudo mkdir -p /opt/medicia-laboral && sudo chown $USER /opt/medicia-laboral
git clone <repo> /opt/medicia-laboral
cd /opt/medicia-laboral
cp .env.example .env
# Editar .env y completar:
#  - POSTGRES_PASSWORD
#  - MINIO_ROOT_PASSWORD
#  - APP_SECRET_KEY (≥ 32 chars, generar con `openssl rand -hex 24`)
#  - ADMIN_EMAIL / ADMIN_PASSWORD
#  - DOMAIN_NAME (si vas a usar TLS auto)
nano .env

./scripts/bootstrap.sh
curl -fsS http://localhost/readyz
```

## 2) Migrar una instalación existente

Desde el servidor origen, con la instalación corriendo:

```bash
cd /opt/medicia-laboral
./scripts/migrate.sh user@servidor-destino /opt/medicia-laboral
```

El script:
1. Genera un backup local (`./backups/<ts>/`)
2. Rsync del código al destino
3. Rsync del backup al destino
4. SSH al destino: levanta postgres+minio, restaura, levanta el stack completo
5. Curl `/readyz` para verificar

> Si el destino es un servidor nuevo, primero seguir la "Primera instalación" hasta
> que `./scripts/bootstrap.sh` termine. Luego `migrate.sh` solo migra los datos.

## 3) Smoke-test post-migración

```bash
ssh user@servidor-destino "cd /opt/medicia-laboral && curl -fsS http://localhost/readyz"
# Login con ADMIN_EMAIL/ADMIN_PASSWORD y verificar:
#   - Listado de empleados
#   - Listado de licencias
#   - Una transición (enviar/validar) en una licencia existente
```

## 4) Backups automáticos

Agregar al cron del host del servidor de producción:

```cron
0 3 * * * cd /opt/medicia-laboral && ./scripts/backup.sh >> /var/log/medicia-backup.log 2>&1
```

## 5) Rollback de emergencia

```bash
cd /opt/medicia-laboral
docker compose -f docker-compose.prod.yml down
./scripts/restore.sh ./backups/<timestamp-anterior>
docker compose -f docker-compose.prod.yml up -d
```

## 6) TLS inicial

Después de `bootstrap.sh`, completar el cert HTTPS:

```bash
docker compose -f docker-compose.prod.yml exec certbot \
  certbot certonly --webroot -w /var/www/certbot \
  -d "$DOMAIN_NAME" --agree-tos -m "$ADMIN_EMAIL" --non-interactive
docker compose -f docker-compose.prod.yml exec nginx nginx -s reload
```

El servicio `certbot` corre en loop y renueva cada 12h.
