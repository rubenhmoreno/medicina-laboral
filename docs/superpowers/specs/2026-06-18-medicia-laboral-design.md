# Spec — Sistema de Medicina Laboral (medicia-laboral)

- **Fecha:** 2026-06-18
- **Estado:** Diseño aprobado, pendiente de revisión final del usuario
- **Carpeta del proyecto:** `/home/mva/medicia-laboral`
- **Autor:** Claude Code + Ruben Moreno

---

## 1. Resumen ejecutivo

Aplicación web para **gestión de ausentismo y licencias médicas** en el ámbito laboral.
Sistema standalone (sin integraciones externas en v1), uso interno por médico/a laboral, RRHH y administrador.
Escala objetivo: 200–2000 empleados, 5–20 usuarios concurrentes.
Despliegue on-prem (VPS Linux + Docker Compose). Diseñado para que Claude Code pueda migrarlo entre servidores con un script.

### Funcionalidades MVP

1. Carga de partes/certificados con adjunto (PDF/foto) y firma de integridad SHA-256.
2. Máquina de estados de licencias (`borrador → enviado → validado | rechazado | anulado`).
3. Cómputo automático de días con **topes parametrizables** por categoría laboral (planta permanente, contratado, monotributista) y por tipo de licencia.
4. Reportes de ausentismo por área, diagnóstico (agregado) y período.
5. Auditoría inmutable (append-only) de todas las acciones.

### Marco regulatorio

Argentina: LCT (ausencias por enfermedad inculpable, art. 208), Ley de Riesgos del Trabajo (24.557), Ley 25.326 (datos personales sensibles — diagnóstico es dato sensible de salud).

---

## 2. Arquitectura

### 2.1 Topología

```
┌────────────────────────────────────────────────────────────┐
│  VPS Linux (Ubuntu 24.04) — Docker Compose                  │
│                                                             │
│   nginx (TLS, certbot) ─┬─▶ /api/*  → fastapi:8000          │
│                         └─▶ /        → spa-static (React)    │
│                                                             │
│   postgres:16   (volumen Docker nombrado, backup diario)    │
│   minio          (objeto local para adjuntos, volumen)      │
└────────────────────────────────────────────────────────────┘
```

Sin servicios externos. Postgres y MinIO en contenedor → portabilidad total.

### 2.2 Estructura del repositorio

```
medicia-laboral/
├── README.md
├── docker-compose.yml          # dev
├── docker-compose.prod.yml     # prod (nginx, certbot, volúmenes)
├── docker-compose.ci.yml       # CI E2E
├── .env.example                # variables completas y comentadas
├── backend/
│   ├── pyproject.toml          # uv, ruff, mypy, pytest
│   ├── app/
│   │   ├── main.py             # FastAPI app factory
│   │   ├── core/               # config, security, deps, db session, permissions
│   │   ├── modules/
│   │   │   ├── empleados/      # router + service + repository + models + schemas
│   │   │   ├── licencias/      # + state_machine.py
│   │   │   ├── adjuntos/
│   │   │   ├── categorias/     # categorías laborales + topes
│   │   │   ├── usuarios/
│   │   │   ├── auditoria/
│   │   │   └── reportes/
│   │   └── shared/             # exceptions, pagination, audit decorator
│   ├── alembic/
│   └── tests/
├── frontend/
│   ├── package.json            # vite + react + react-router + zod + shadcn/ui
│   ├── src/
│   │   ├── api/                # cliente generado desde OpenAPI
│   │   ├── features/           # empleados/, licencias/, reportes/, admin/
│   │   ├── components/         # ui/ (shadcn) + layout/
│   │   ├── hooks/, lib/, routes/
│   │   └── App.tsx
│   └── tests/                  # vitest + testing-library + Playwright
├── scripts/
│   ├── bootstrap.sh            # primera instalación: volúmenes, migrations, admin
│   ├── backup.sh               # dump diario Postgres + mirror MinIO
│   ├── restore.sh              # restauración desde backup
│   └── migrate.sh              # mover instancia a otro servidor
├── docs/
│   ├── MIGRATION.md            # runbook portabilidad
│   └── superpowers/
│       ├── specs/
│       └── plans/
└── .github/workflows/
    └── ci.yml
```

### 2.3 Convención por módulo backend

Cada módulo es autocontenido y testeable:

```
modules/<modulo>/
├── router.py        # endpoints FastAPI (delgado, sin lógica)
├── service.py       # lógica de negocio (testeable sin HTTP)
├── repository.py    # acceso a DB (testeable con sesión)
├── models.py        # SQLAlchemy
├── schemas.py       # Pydantic (request/response)
└── exceptions.py    # excepciones específicas del módulo
```

### 2.4 Portabilidad — requisito de primer nivel

Para que Claude Code pueda migrar el sistema entre servidores sin intervención manual:

1. **Config 100% en `.env`** — nunca hardcoded. `.env.example` completo y comentado.
2. **Deploy reproducible** — `docker-compose.prod.yml` levanta todo con un comando. Sin servicios managed-only.
3. **Bootstrap idempotente** — `scripts/bootstrap.sh` crea volúmenes, ejecuta migraciones Alembic, crea primer admin desde `.env`.
4. **Backup unificado** — `scripts/backup.sh` produce `./backups/<timestamp>/` con dump Postgres + mirror MinIO + manifest SHA-256.
5. **Migración entre servidores** — `scripts/migrate.sh <user@host> <ruta>` hace rsync + remote restore.
6. **`docs/MIGRATION.md`** — runbook ejecutable por un Claude Code futuro sin contexto adicional.
7. **Sin paths absolutos del host** — todos relativos al repo, volúmenes Docker nombrados.

---

## 3. Modelo de datos

### 3.1 Núcleo de personas

```sql
empleados (
  id UUID PK,
  legajo TEXT UNIQUE NOT NULL,
  cuil TEXT UNIQUE NOT NULL,
  nombre, apellido TEXT NOT NULL,
  fecha_nacimiento DATE,
  fecha_ingreso DATE NOT NULL,
  area_id UUID FK areas(id),
  categoria_id UUID FK categorias_laborales(id) NOT NULL,
  supervisor_id UUID FK empleados(id) NULL,
  email, telefono TEXT,
  activo BOOL DEFAULT TRUE,
  created_at, updated_at TIMESTAMPTZ
)

areas (
  id UUID PK,
  nombre TEXT NOT NULL,
  parent_id UUID FK areas(id) NULL    -- jerarquía de áreas
)
```

### 3.2 Catálogos

```sql
categorias_laborales (
  id UUID PK,
  codigo TEXT UNIQUE NOT NULL,           -- 'planta-permanente', 'contratado', 'monotributista'
  nombre TEXT NOT NULL,
  activa BOOL DEFAULT TRUE,
  created_at, updated_at TIMESTAMPTZ
)

tipos_licencia (
  id UUID PK,
  codigo TEXT UNIQUE NOT NULL,           -- 'enfermedad-comun', 'accidente-trabajo', 'art-larga', ...
  nombre TEXT NOT NULL,
  base_legal TEXT,                       -- 'LCT art. 208', 'Ley 24.557', ...
  paga BOOL DEFAULT TRUE,
  computa_dias BOOL DEFAULT TRUE
)

diagnosticos (
  id UUID PK,
  codigo_cie10 TEXT,
  descripcion TEXT NOT NULL,
  categoria TEXT,                        -- traumatológico, infeccioso, psiquiátrico, ...
  requiere_junta BOOL DEFAULT FALSE
)

-- Topes parametrizables por categoría × tipo de licencia, versionados
topes_dias (
  id UUID PK,
  categoria_id UUID FK categorias_laborales(id) NOT NULL,
  tipo_licencia_id UUID FK tipos_licencia(id) NOT NULL,
  dias_maximos INTEGER NOT NULL,
  ventana TEXT NOT NULL CHECK (ventana IN ('anio-calendario','anio-aniversario','sin-limite')),
  vigente_desde DATE NOT NULL,
  vigente_hasta DATE NULL,                -- NULL = vigente
  observacion TEXT,
  UNIQUE (categoria_id, tipo_licencia_id, vigente_desde)
)
```

**Versionado de topes:** cada edición desde el admin crea una nueva fila con `vigente_desde = today` y cierra la anterior (`vigente_hasta = today - 1`). Las licencias ya validadas no se recalculan — el tope vigente al momento de validar es el que rigió.

### 3.3 Núcleo del dominio

```sql
licencias (
  id UUID PK,                            -- UUID v7 (ordenable por tiempo)
  empleado_id UUID FK empleados(id) NOT NULL,
  tipo_licencia_id UUID FK tipos_licencia(id) NOT NULL,
  diagnostico_id UUID FK diagnosticos(id) NULL,
  fecha_desde DATE NOT NULL,
  fecha_hasta DATE NOT NULL,
  dias_solicitados INTEGER NOT NULL,     -- persistido, no recalculado en read
  dias_otorgados INTEGER NULL,           -- decisión del médico al validar
  estado TEXT NOT NULL CHECK (estado IN
       ('borrador','enviado','validado','rechazado','anulado')),
  origen TEXT NOT NULL CHECK (origen IN ('rrhh','medico')),
  observaciones TEXT,
  motivo_rechazo TEXT NULL,
  motivo_anulacion TEXT NULL,
  certificante TEXT,                     -- médico tratante externo
  matricula_certificante TEXT,
  creado_por UUID FK usuarios(id) NOT NULL,
  validado_por UUID FK usuarios(id) NULL,
  validado_en TIMESTAMPTZ NULL,
  created_at, updated_at TIMESTAMPTZ
)

-- adjuntos persisten cuando la licencia pasa a estado 'anulado' (soft-delete).
-- CASCADE solo dispara en hard-delete administrativo, que requiere job manual.
adjuntos (
  id UUID PK,
  licencia_id UUID FK licencias(id) ON DELETE CASCADE,
  nombre_original TEXT,
  mime_type TEXT,
  size_bytes BIGINT,
  sha256 TEXT NOT NULL,                  -- integridad
  storage_key TEXT NOT NULL,             -- key en MinIO
  subido_por UUID FK usuarios(id),
  created_at TIMESTAMPTZ
)
```

### 3.4 Seguridad y auditoría

```sql
usuarios (
  id UUID PK,
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,           -- argon2id
  nombre TEXT,
  rol TEXT NOT NULL CHECK (rol IN ('admin','medico','rrhh')),
  matricula TEXT NULL,                   -- requerida para rol médico
  activo BOOL DEFAULT TRUE,
  ultimo_login TIMESTAMPTZ,
  created_at, updated_at TIMESTAMPTZ
)

auditoria (
  id BIGSERIAL PK,
  ts TIMESTAMPTZ NOT NULL DEFAULT now(),
  usuario_id UUID NULL,                  -- NULL = acción del sistema
  accion TEXT NOT NULL,                  -- login, logout, create, update, delete,
                                         -- state_change, export, tope_change,
                                         -- permission_denied, login_failed
  entidad TEXT NOT NULL,
  entidad_id UUID NULL,
  payload JSONB NULL,                    -- diff before/after o snapshot
  ip TEXT,
  user_agent TEXT
)
```

A nivel DB: `REVOKE INSERT, UPDATE, DELETE ON auditoria FROM <rol_app>` excepto para INSERT — append-only real, no se puede modificar histórico desde la aplicación.

### 3.5 Índices

- `licencias(empleado_id, fecha_desde)`
- `licencias(estado)`
- `licencias(tipo_licencia_id, validado_en) WHERE estado='validado'` (para cálculo de topes)
- `auditoria(ts, entidad, entidad_id)`
- `empleados(legajo)`, `empleados(cuil)`, `usuarios(email)` (los unique ya implican índice)

---

## 4. Máquina de estados y cómputo de días

### 4.1 Transiciones

```
                              ┌─── (rrhh) ──┐
   (creado por rrhh|medico)   │             ▼
       ┌─────────┐  enviar       ┌──────────┐  validar (medico)   ┌───────────┐
       │borrador │ ─────────────▶│ enviado  │ ──────────────────▶ │ validado  │
       └────┬────┘               └────┬─────┘                     └─────┬─────┘
            │ anular                   │ rechazar (medico)               │ anular (admin)
            ▼                          ▼                                 ▼
        ┌────────┐                ┌───────────┐                     ┌────────┐
        │anulado │                │ rechazado │                     │anulado │
        └────────┘                └─────┬─────┘                     └────────┘
                                        │ reabrir (admin)
                                        ▼
                                     borrador
```

| Desde     | Hacia      | Quién                | Validaciones                                  |
|-----------|------------|----------------------|-----------------------------------------------|
| borrador  | enviado    | rrhh, medico         | adjunto presente, fechas válidas, días > 0    |
| borrador  | anulado    | creador, admin       | —                                             |
| enviado   | validado   | medico               | `dias_otorgados` requerido, evalúa tope       |
| enviado   | rechazado  | medico               | `motivo_rechazo` obligatorio                  |
| validado  | anulado    | admin                | `motivo_anulacion` obligatorio                |
| rechazado | borrador   | admin                | reapertura para corrección                    |

Transición ilegal → `InvalidStateTransition` → HTTP 409.
Todo cambio de estado escribe en `auditoria` con `accion='state_change'`, payload `{from, to, motivo}`.

### 4.2 Cómputo de días

```python
def calcular_dias(fecha_desde: date, fecha_hasta: date) -> int:
    if fecha_hasta < fecha_desde:
        raise ValueError("fecha_hasta < fecha_desde")
    return (fecha_hasta - fecha_desde).days + 1   # corridos, inclusivo ambos extremos
```

### 4.3 Evaluación de tope

`fecha_ref` es la fecha de la acción en que se evalúa el tope: fecha del envío a validación y, separadamente, fecha de la validación. Para una misma licencia el tope vigente al momento de validar es el que rige y queda registrado en auditoría.

```python
def evaluar_tope(empleado, tipo_licencia, dias_solicitados, fecha_ref, repo) -> TopeEvaluacion:
    tope = repo.tope_vigente(empleado.categoria_id, tipo_licencia.id, en_fecha=fecha_ref)
    if tope is None or tope.ventana == 'sin-limite':
        return TopeEvaluacion(tope_aplicable=None, excede=False)
    ventana = _ventana_para(tope.ventana, empleado, fecha_ref)
    consumidos = repo.dias_consumidos(empleado.id, tipo_licencia.id, ventana)
    excede = (consumidos + dias_solicitados) > tope.dias_maximos
    return TopeEvaluacion(
        tope_aplicable=tope.dias_maximos,
        dias_consumidos_ventana=consumidos,
        dias_restantes=max(0, tope.dias_maximos - consumidos),
        excede=excede,
        warning_msg=f"Excede tope ({consumidos + dias_solicitados}/{tope.dias_maximos})" if excede else None,
    )
```

**Aplicación:**
- Se evalúa al enviar a validación y al validar.
- Si `excede=True`: el médico ve un warning visible (no bloquea). La decisión queda registrada en `auditoria` con snapshot del cálculo.
- Las reglas de ventana (`anio-calendario`, `anio-aniversario`) se resuelven contra `empleados.fecha_ingreso` para aniversario, o año civil para calendario.

### 4.4 Pantalla de configuración de topes (admin)

- Ruta: `/admin/topes` (solo rol `admin`).
- Grilla: filas = categorías laborales, columnas = tipos de licencia, celdas editables = días máximos + ventana.
- Endpoint: `PUT /api/admin/topes/{categoria_id}/{tipo_licencia_id}` → inserta nueva fila con `vigente_desde = today`, cierra la anterior. Sin UPDATE in-place.

---

## 5. Seguridad y RBAC

### 5.1 Autenticación

- `fastapi-users`, hashing **argon2id**.
- Access JWT (15 min) + refresh token (7 días) HTTP-only, Secure, SameSite=Strict.
- Bloqueo 15 min tras 5 intentos fallidos consecutivos (auditado).
- Password ≥ 12 caracteres, validado contra top-10k passwords (`zxcvbn`).
- Reset por email, token de un solo uso, expiración 30 min.
- Forzar cambio en primer login del admin sembrado.

### 5.2 Matriz RBAC

| Recurso                      | admin | medico | rrhh |
|------------------------------|:-----:|:------:|:----:|
| Empleados — listar           |  ✅   |   ✅   |  ✅  |
| Empleados — crear/editar     |  ✅   |   —    |  ✅  |
| Licencias — crear            |  ✅   |   ✅   |  ✅  |
| Licencias — validar/rechazar |  —    |   ✅   |  —   |
| Licencias — anular validadas |  ✅   |   —    |  —   |
| Reportes — ver/exportar      |  ✅   |   ✅   |  ✅  |
| Categorías / topes           |  ✅   |   —    |  —   |
| Diagnósticos / tipos         |  ✅   |   —    |  —   |
| Usuarios                     |  ✅   |   —    |  —   |
| Auditoría — leer             |  ✅   |   —    |  —   |

### 5.3 Protección de datos sensibles (Ley 25.326 + LRT)

1. Diagnóstico y observaciones médicas: visibles solo a `medico` y `admin`. Para `rrhh`, las APIs los devuelven como `null`.
2. Reportes para RRHH: agregados por **categoría de diagnóstico**, nunca por descripción individual.
3. Cifrado at-rest: volumen Docker sobre LUKS (sysadmin, documentado en MIGRATION.md).
4. TLS obligatorio: nginx + HSTS + redirect 80→443 + certbot.
5. Headers de seguridad: CSP estricto, `X-Content-Type-Options: nosniff`, `Referrer-Policy: same-origin`, `Permissions-Policy` mínimo.
6. CORS: solo origin del frontend (config por `.env`).
7. Adjuntos: descarga vía URL firmada de MinIO con expiración 5 min, generada por backend con verificación de rol y propiedad. Bucket nunca público.

### 5.4 Auditoría

Decorador `@audited(accion, entidad)` aplicado en services. Cubre: `login`, `login_failed`, `logout`, `create`, `update`, `delete`, `state_change`, `export`, `tope_change`, `permission_denied`. Payload para `update` incluye diff before/after.

Endpoint `GET /api/auditoria?from=&to=&usuario=&entidad=&entidad_id=` solo admin, paginado, exportable CSV. La exportación queda auditada (`accion='export'`).

---

## 6. Errores, observabilidad, backup y migración

### 6.1 Jerarquía de errores

```python
class AppError(Exception):
    http_status = 500
    code = "internal_error"

class ValidationError(AppError):     http_status = 422; code = "validation"
class NotFoundError(AppError):       http_status = 404; code = "not_found"
class ConflictError(AppError):       http_status = 409; code = "conflict"
class ForbiddenError(AppError):      http_status = 403; code = "forbidden"
class UnauthorizedError(AppError):   http_status = 401; code = "unauthorized"
class InvalidStateTransition(ConflictError):  code = "invalid_transition"
```

Handler global produce:
```json
{ "error": { "code": "invalid_transition", "message": "...", "detail": { ... } }, "request_id": "..." }
```

Errores inesperados → 500 con `request_id`. Sin stacktrace al cliente; stacktrace queda en log JSON estructurado (structlog).

### 6.2 Observabilidad mínima v1

- `/healthz` — liveness.
- `/readyz` — readiness (chequea Postgres + MinIO).
- Métricas Prometheus opt-in (`METRICS_ENABLED=true` en `.env`).
- Sin tracing distribuido en v1.

### 6.3 Backup y restore

**`scripts/backup.sh`** (cron diario 03:00 AM):
- `pg_dump -Fc -Z9` completo + dump separado de `auditoria`.
- `mc mirror` del bucket MinIO.
- Manifest `MANIFEST.sha256`.
- Retención 30 días.
- Salida única en `./backups/<timestamp>/`.

**`scripts/restore.sh <dir>`** valida sha256 y restaura.

### 6.4 Migración entre servidores

**`scripts/migrate.sh <user@host> <ruta>`** (sincronización entre dos instalaciones ya existentes):
1. Ejecuta `backup.sh` local.
2. `rsync` código + último backup al servidor destino.
3. SSH al destino: `restore.sh` + `docker compose -f docker-compose.prod.yml up -d`.
4. Imprime URL para verificar `/readyz`.

**Primera instalación en servidor nuevo** (no usa `migrate.sh`; documentado en `MIGRATION.md`):
1. Clonar repo.
2. `cp .env.example .env` y completar secrets.
3. `./scripts/bootstrap.sh`.
4. (Opcional) `./scripts/restore.sh <backup>` para hidratar con datos del origen.
5. `docker compose -f docker-compose.prod.yml up -d`.

**`docs/MIGRATION.md`** documenta el procedimiento paso a paso para que un Claude Code futuro pueda ejecutarlo sin contexto adicional.

### 6.5 Tareas programadas

Cron del host lanza `backup.sh` 03:00 AM. Sin worker async en v1.

---

## 7. Testing y CI

### 7.1 Pirámide

- **~60% unitarios** — services puros (cómputo días, topes, state machine, RBAC). pytest + factory-boy.
- **~30% integración** — FastAPI TestClient + Postgres real (testcontainers).
- **~10% E2E** — Playwright, 4 happy paths.

**Coverage gates:** backend ≥ 80%, frontend ≥ 70%. CI bloquea merge si no se cumple.

### 7.2 Tests críticos sin negociación

- `test_state_machine.py`: matriz parametrizada **completa** de transiciones permitidas y prohibidas.
- `test_calcular_dias.py`: rangos válidos/inválidos, día único, año bisiesto.
- `test_topes.py`: tope `None`, `sin-limite`, ventana aniversario vs calendario, cambio de tope durante el período, distintos estados de licencias previas.
- `test_rbac.py`: matriz rol × endpoint × resultado esperado.
- `test_auditoria.py`: cada acción genera entry; UPDATE/DELETE en `auditoria` falla a nivel DB.

### 7.3 Frontend

- Vitest + `@testing-library/react` para unitarios.
- MSW para mock de API en integración.
- Playwright para 4 E2E:
  1. Admin crea empleado → crea licencia → envía.
  2. Médico ve pendientes → valida con tope warning visible.
  3. Médico rechaza con motivo.
  4. Admin edita tope → verifica versionado.
- `@axe-core/playwright` en E2E (a11y bloquea si serio/crítico).

### 7.4 Cliente OpenAPI

`pnpm gen:api` corre `openapi-typescript-codegen` contra `/openapi.json` del backend dev → `frontend/src/api/`. CI verifica diff vacío.

### 7.5 CI (GitHub Actions)

Pipeline `ci.yml` con jobs `backend`, `frontend`, `e2e`, `build`. Quality gates bloqueantes: lint, types, coverage, E2E. Sin paso a `main` si alguno falla.

### 7.6 Seeds dev

`scripts/seed_dev.py` crea: 1 admin, 1 médico, 1 rrhh, 3 categorías, 5 tipos de licencia, topes default, 30 empleados ficticios, 20 licencias en distintos estados. Solo dev/test.

---

## 8. Riesgos y mitigaciones

| Riesgo                                                            | Mitigación                                                                |
|-------------------------------------------------------------------|---------------------------------------------------------------------------|
| Exposición de datos médicos a RRHH                                | RBAC + filtrado en API + tests de a11y/visibilidad                        |
| Pérdida de auditoría por bug o atacante                            | Append-only a nivel DB + backup separado de la tabla `auditoria`         |
| Migración entre servidores falla por config olvidada              | `.env.example` completo + `MIGRATION.md` ejecutable + smoke test `/readyz`|
| Recalculo de topes muta historia                                  | Topes versionados, decisión snapshot en `auditoria`                       |
| Cambio de regla LCT                                               | Topes parametrizables, sin lógica LCT hardcodeada                         |

---

## 9. Fuera de alcance v1

- SSO corporativo (Microsoft/Google).
- App móvil o portal del empleado.
- Integración con sistema de RRHH externo.
- API ART para envío automático de denuncias.
- Junta médica (workflow propio) — solo flag `requiere_junta` en diagnóstico.
- Notificaciones por email (queda para v1.1 si se aprueba).
- Multi-tenant.

---

## 10. Próximos pasos

1. Revisión del spec por el usuario.
2. Generación del plan de implementación detallado vía skill `writing-plans`.
3. Ejecución TDD por módulo, con quality gates por fase.
