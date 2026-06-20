# Medicina Laboral — Referencia del Proyecto

Sistema de gestion de medicina laboral para la Municipalidad de Villa Allende. Gestiona empleados, licencias medicas, atenciones clinicas, historia clinica con exportacion PDF, y reportes de ausentismo.

---

## Stack Tecnologico

| Capa | Tecnologia |
|------|------------|
| Backend | FastAPI 0.115 + Python 3.12 |
| ORM | SQLAlchemy 2.0 async (asyncpg) |
| DB | PostgreSQL 16 |
| Migraciones | Alembic |
| Almacenamiento | MinIO (S3-compatible) |
| Auth | JWT (python-jose) + Argon2 (password hashing) |
| PDF | ReportLab 4.x |
| Frontend | React 18 + TypeScript 5.6 + Vite 5.4 |
| CSS | TailwindCSS 3.4 (tema custom) |
| HTTP Client | Axios 1.18 |
| Router | React Router DOM 6.30 |
| Testing | Vitest + Playwright + pytest |
| Containerizacion | Docker Compose (dev, CI, prod) |

---

## Estructura de Directorios

```
medicia-laboral/
├── backend/
│   ├── app/
│   │   ├── core/               # Config, auth, DB, storage, middleware
│   │   │   ├── settings.py     # Pydantic Settings (env vars)
│   │   │   ├── db.py           # AsyncSession factory
│   │   │   ├── deps.py         # Dependency injection (get_session, current_user)
│   │   │   ├── security.py     # Argon2 password hash/verify
│   │   │   ├── jwt.py          # JWT create/decode (access + refresh)
│   │   │   ├── permissions.py  # require_role() decorator RBAC
│   │   │   ├── storage.py      # MinIO client init
│   │   │   ├── logging.py      # structlog config
│   │   │   ├── middleware.py   # Request ID middleware
│   │   │   └── throttle.py    # Login brute-force throttle
│   │   ├── main.py             # FastAPI app factory + router registration
│   │   └── modules/            # 16 modulos de negocio (ver detalle abajo)
│   ├── alembic/
│   │   └── versions/           # Migraciones (9 archivos)
│   ├── scripts/
│   │   └── seed_dev.py         # Seed admin + catalogos base
│   ├── tests/
│   └── pyproject.toml          # Dependencias Python
├── frontend/
│   ├── src/
│   │   ├── api/                # Clientes API (axios)
│   │   ├── auth/               # AuthContext + ProtectedRoute
│   │   ├── components/ui/      # Biblioteca UI reutilizable (12 componentes)
│   │   ├── features/           # Paginas por dominio
│   │   │   ├── admin/          # CRUD catalogos + usuarios + topes + configuracion
│   │   │   ├── empleados/      # Lista, crear, editar, historia clinica
│   │   │   ├── licencias/      # Lista, formulario, detalle con workflow
│   │   │   ├── atenciones/     # Lista, crear, detalle con tabs clinicos
│   │   │   └── reportes/       # 3 reportes con export CSV
│   │   ├── layout/             # AppLayout (sidebar + topbar)
│   │   ├── routes/             # login.tsx, dashboard.tsx
│   │   └── index.css           # Tema global + gradientes custom
│   ├── tailwind.config.ts
│   └── package.json
├── nginx/                      # Config reverse proxy produccion
├── scripts/                    # bootstrap.sh, migrate.sh, backup.sh, restore.sh
├── docker-compose.yml          # Dev (postgres + minio)
├── docker-compose.prod.yml     # Produccion (todo + nginx + certbot)
├── docker-compose.ci.yml       # CI pipeline
└── .env.example                # Variables de entorno requeridas
```

---

## Variables de Entorno

```env
# Postgres
POSTGRES_USER=medicia
POSTGRES_PASSWORD=changeme_dev
POSTGRES_DB=medicia
POSTGRES_HOST=postgres          # "localhost" si backend corre fuera de Docker
POSTGRES_PORT=5432

# MinIO
MINIO_ROOT_USER=medicia
MINIO_ROOT_PASSWORD=changeme_dev_minio
MINIO_BUCKET=medicina-adjuntos
MINIO_ENDPOINT=minio:9000
MINIO_USE_SSL=false

# Backend
APP_ENV=dev                     # dev | prod
APP_SECRET_KEY=changeme_32_bytes_minimum_secret_here_12345
JWT_ACCESS_TTL_MINUTES=15
JWT_REFRESH_TTL_DAYS=7
CORS_ORIGINS=http://localhost:5173,http://10.0.0.19:5173
LOG_LEVEL=INFO
METRICS_ENABLED=false

# Seed
ADMIN_EMAIL=admin
ADMIN_PASSWORD=123

# Frontend (Vite solo lee VITE_*)
VITE_API_BASE_URL=http://localhost:8000
```

**IMPORTANTE**: Cuando el backend corre fuera de Docker (desarrollo local), iniciar con:
```bash
POSTGRES_HOST=localhost uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

## Base de Datos — Esquema Completo

### Tablas (18 tablas)

Todas usan UUID (uuid7) como PK y tienen `created_at`, `updated_at` con server defaults.

#### usuarios
| Columna | Tipo | Notas |
|---------|------|-------|
| id | UUID PK | |
| email | String UNIQUE | Login identity |
| password_hash | String | Argon2 |
| nombre | String nullable | Display name |
| rol | Enum | admin, medico, rrhh |
| matricula | String nullable | Solo medicos |
| activo | Boolean | Default true |
| ultimo_login | DateTime nullable | |

#### empleados
| Columna | Tipo | Notas |
|---------|------|-------|
| id | UUID PK | |
| legajo | String(40) UNIQUE | Solo numerico, pattern `^\d+$` |
| cuil | String UNIQUE | Formato `XX-XXXXXXXX-X` o 11 digitos |
| nombre, apellido | String | |
| fecha_nacimiento | Date nullable | |
| fecha_ingreso | Date | |
| area_id | UUID FK → areas nullable | |
| categoria_id | UUID FK → categorias | |
| supervisor_id | UUID FK → empleados nullable | Self-ref |
| obra_social | String(120) nullable | Nombre de la obra social |
| nro_carnet | String(40) nullable | Numero de carnet de la obra social |
| email | String nullable | |
| telefono | String nullable | |
| activo | Boolean | Default true |

#### areas
| Columna | Tipo | Notas |
|---------|------|-------|
| id | UUID PK | |
| nombre | String UNIQUE | |
| parent_id | UUID FK → areas nullable | Jerarquia |

#### categorias_laborales
| Columna | Tipo | Notas |
|---------|------|-------|
| id | UUID PK | |
| codigo | String UNIQUE | |
| nombre | String | |
| activa | Boolean | |

#### tipos_licencia
| Columna | Tipo | Notas |
|---------|------|-------|
| id | UUID PK | |
| codigo | String UNIQUE | |
| nombre | String | |
| base_legal | String nullable | Ley/articulo |
| paga | Boolean | Si se paga |
| computa_dias | Boolean | Si computa para topes |

#### topes_dias
| Columna | Tipo | Notas |
|---------|------|-------|
| id | UUID PK | |
| categoria_id | UUID FK | |
| tipo_licencia_id | UUID FK | |
| dias_maximos | Integer | |
| ventana | String | anio-calendario, anio-aniversario, sin-limite |
| vigente_desde | Date | |
| vigente_hasta | Date nullable | |
| observacion | String nullable | |
| UNIQUE(categoria_id, tipo_licencia_id, vigente_desde) | | |

#### licencias
| Columna | Tipo | Notas |
|---------|------|-------|
| id | UUID PK | |
| empleado_id | UUID FK → empleados | |
| tipo_licencia_id | UUID FK → tipos_licencia | |
| diagnostico | String(500) nullable | Texto libre |
| fecha_desde, fecha_hasta | Date | |
| dias_solicitados | Integer | |
| dias_otorgados | Integer nullable | Se setea al validar |
| estado | String | borrador, enviado, validado, rechazado, anulado |
| origen | String | rrhh, medico |
| observaciones | Text nullable | |
| motivo_rechazo | Text nullable | |
| motivo_anulacion | Text nullable | |
| certificante | String nullable | Nombre del certificante |
| matricula_certificante | String nullable | |
| modo_constatacion | String nullable | presencial, telefonica, virtual |
| creado_por | UUID FK → usuarios | |
| validado_por | UUID FK → usuarios nullable | |
| validado_en | DateTime nullable | |

**Maquina de estados**: borrador → enviado → validado | rechazado. validado → anulado.

#### atenciones
| Columna | Tipo | Notas |
|---------|------|-------|
| id | UUID PK | |
| empleado_id | UUID FK → empleados | |
| asignado_por | UUID FK → usuarios | Quien creo el turno |
| medico_id | UUID FK → usuarios nullable | |
| fecha_turno | DateTime | |
| motivo | Text | |
| estado | String | pendiente, completada, cancelada |
| notas_medicas | Text nullable | Se agrega al completar |

#### signos_vitales
| Columna | Tipo | Notas |
|---------|------|-------|
| id | UUID PK | |
| atencion_id | UUID FK UNIQUE | 1:1 con atencion |
| peso_kg, altura_cm, imc | Float nullable | |
| presion_sistolica, presion_diastolica | Integer nullable | |
| temperatura | Float nullable | |
| frecuencia_cardiaca | Integer nullable | |
| saturacion_o2 | Float nullable | |
| glucemia | Float nullable | |
| registrado_por | UUID FK → usuarios | |

#### evoluciones
| Columna | Tipo | Notas |
|---------|------|-------|
| id | UUID PK | |
| atencion_id | UUID FK | Muchas por atencion |
| motivo_consulta | Text nullable | |
| anamnesis | Text nullable | |
| examen_fisico | Text nullable | |
| diagnostico_presuntivo | String(500) nullable | Texto libre |
| diagnostico_definitivo | String(500) nullable | Texto libre |
| tratamiento | Text nullable | |
| observaciones | Text nullable | |
| medico_id | UUID FK → usuarios | |

#### recetas
| Columna | Tipo | Notas |
|---------|------|-------|
| id | UUID PK | |
| atencion_id | UUID FK | |
| medico_id | UUID FK → usuarios | |
| diagnostico | String nullable | |
| observaciones | Text nullable | |

#### items_receta
| Columna | Tipo | Notas |
|---------|------|-------|
| id | UUID PK | |
| receta_id | UUID FK CASCADE | |
| medicamento | String | |
| dosis | String nullable | |
| frecuencia | String nullable | |
| duracion | String nullable | |
| orden | Integer | |

#### pedidos
| Columna | Tipo | Notas |
|---------|------|-------|
| id | UUID PK | |
| atencion_id | UUID FK | |
| medico_id | UUID FK → usuarios | |
| tipo | String | laboratorio, imagen, interconsulta, otro |
| diagnostico | String nullable | |
| indicaciones | Text nullable | |

#### items_pedido
| Columna | Tipo | Notas |
|---------|------|-------|
| id | UUID PK | |
| pedido_id | UUID FK CASCADE | |
| descripcion | String | |
| codigo | String nullable | |
| orden | Integer | |

#### estudios_catalogo
| Columna | Tipo | Notas |
|---------|------|-------|
| id | UUID PK | |
| nombre | String | |
| codigo | String nullable | |
| tipo | String | laboratorio, imagen, otro |
| categoria | String nullable | |
| activo | Boolean | |

#### adjuntos
| Columna | Tipo | Notas |
|---------|------|-------|
| id | UUID PK | |
| licencia_id | UUID FK nullable | Exclusivo con atencion_id |
| atencion_id | UUID FK nullable | Exclusivo con licencia_id |
| nombre_original | String | |
| mime_type | String | |
| size_bytes | Integer | |
| sha256 | String | |
| storage_key | String | Ruta en MinIO |
| subido_por | UUID FK → usuarios | |

#### configuracion
| Columna | Tipo | Notas |
|---------|------|-------|
| id | UUID PK | |
| clave | String(100) UNIQUE | Clave de configuracion |
| valor | Text | Valor (default "") |
| descripcion | Text nullable | Descripcion para la UI |

Claves actuales: `pdf_header_linea1`, `pdf_header_linea2`, `pdf_header_linea3`, `pdf_footer`

#### auditoria
| Columna | Tipo | Notas |
|---------|------|-------|
| id | BigInt autoincrement | |
| ts | DateTime | |
| usuario_id | UUID FK | |
| accion | String | Nombre de la accion |
| entidad | String | Nombre de tabla |
| entidad_id | UUID | |
| payload | JSONB | Datos del cambio |
| ip | String nullable | |
| user_agent | String nullable | |

---

## Migraciones Alembic

```
c616894c3934  empty initial
049cc680e4b7  usuarios table
142ccb53835a  all tables (areas, categorias, tipos_licencia, empleados, topes, licencias, adjuntos, atenciones)
cf57f12cf1af  auditoria table
b5f2a7d9e1c3  clinical features (signos_vitales, evoluciones, recetas, items_receta, pedidos, items_pedido, estudios_catalogo)
d8a1e3f5b2c4  diagnostico texto libre (elimina tabla diagnosticos, convierte FKs a texto)
e614aa488ccc  add configuracion table
8cee745dc897  add obra_social, nro_carnet to empleados
958076442bc7  add modo_constatacion to licencias
```

Para ejecutar: `POSTGRES_HOST=localhost uv run alembic upgrade head`

---

## API — Todos los Endpoints

### Auth (`/api/auth`)
| Metodo | Ruta | Descripcion | Roles |
|--------|------|-------------|-------|
| POST | `/api/auth/login` | Login → TokenPair | publico |
| POST | `/api/auth/refresh` | Refresh token | publico |
| GET | `/api/auth/me` | Usuario actual | autenticado |

### Usuarios (`/api/usuarios`)
| Metodo | Ruta | Descripcion | Roles |
|--------|------|-------------|-------|
| GET | `/api/usuarios` | Listar usuarios | admin |
| POST | `/api/usuarios` | Crear usuario | admin |

### Empleados (`/api/empleados`)
| Metodo | Ruta | Descripcion | Roles |
|--------|------|-------------|-------|
| GET | `/api/empleados` | Listar (q, limit, offset) | autenticado |
| GET | `/api/empleados/count` | Contar total | autenticado |
| GET | `/api/empleados/{id}` | Detalle | autenticado |
| POST | `/api/empleados` | Crear | admin, rrhh |
| PUT | `/api/empleados/{id}` | Actualizar | admin, rrhh |
| GET | `/api/empleados/{id}/historia-clinica` | Historia clinica completa | autenticado |
| GET | `/api/empleados/{id}/historia-clinica/pdf` | Descargar PDF | autenticado |

### Areas (`/api/areas`)
| Metodo | Ruta | Descripcion | Roles |
|--------|------|-------------|-------|
| GET | `/api/areas` | Listar | autenticado |
| GET | `/api/areas/{id}` | Detalle | autenticado |
| POST | `/api/areas` | Crear | admin, rrhh |
| PUT | `/api/areas/{id}` | Actualizar | admin |
| DELETE | `/api/areas/{id}` | Eliminar | admin |

### Categorias (`/api/categorias`)
| Metodo | Ruta | Descripcion | Roles |
|--------|------|-------------|-------|
| GET | `/api/categorias` | Listar | autenticado |
| GET | `/api/categorias/{id}` | Detalle | autenticado |
| POST | `/api/categorias` | Crear | admin |
| PUT | `/api/categorias/{id}` | Actualizar | admin |
| DELETE | `/api/categorias/{id}` | Eliminar | admin |

### Tipos Licencia (`/api/tipos-licencia`)
| Metodo | Ruta | Descripcion | Roles |
|--------|------|-------------|-------|
| GET | `/api/tipos-licencia` | Listar | autenticado |
| GET | `/api/tipos-licencia/{id}` | Detalle | autenticado |
| POST | `/api/tipos-licencia` | Crear | admin |
| PUT | `/api/tipos-licencia/{id}` | Actualizar | admin |
| DELETE | `/api/tipos-licencia/{id}` | Eliminar | admin |

### Topes (`/api/admin/topes`)
| Metodo | Ruta | Descripcion | Roles |
|--------|------|-------------|-------|
| GET | `/api/admin/topes` | Listar topes vigentes | admin |
| PUT | `/api/admin/topes/{cat}/{tipo}` | Crear/actualizar tope | admin |

### Licencias (`/api/licencias`)
| Metodo | Ruta | Descripcion | Roles |
|--------|------|-------------|-------|
| GET | `/api/licencias` | Listar con filtros | autenticado |
| GET | `/api/licencias/count` | Contar con filtros | autenticado |
| GET | `/api/licencias/{id}` | Detalle enriquecido | autenticado |
| POST | `/api/licencias` | Crear borrador | admin, rrhh, medico |
| POST | `/api/licencias/{id}/enviar` | Enviar a validacion | admin, rrhh, medico |
| POST | `/api/licencias/{id}/validar` | Validar (dias_otorgados) | medico, admin |
| POST | `/api/licencias/{id}/rechazar` | Rechazar (motivo) | medico, admin |
| POST | `/api/licencias/{id}/anular` | Anular (motivo) | admin |
| GET | `/api/licencias/{id}/tope` | Evaluar contra tope | autenticado |

**Filtros GET**: estado, empleado_id, area_id, desde, hasta, vigente (bool), limit, offset

**Respuesta enriquecida**: incluye `empleado_nombre`, `tipo_licencia_nombre`, `diagnostico` (texto), `empleado_legajo`, `empleado_cuil`, `empleado_area`, `modo_constatacion`

### Atenciones (`/api/atenciones`)
| Metodo | Ruta | Descripcion | Roles |
|--------|------|-------------|-------|
| GET | `/api/atenciones` | Listar con filtros | autenticado |
| GET | `/api/atenciones/{id}` | Detalle enriquecido | autenticado |
| POST | `/api/atenciones` | Crear turno | admin, rrhh, medico |
| PUT | `/api/atenciones/{id}` | Actualizar | admin, rrhh |
| POST | `/api/atenciones/{id}/completar` | Completar (notas) | admin, medico |
| POST | `/api/atenciones/{id}/cancelar` | Cancelar | admin, rrhh |

**Respuesta enriquecida**: incluye `empleado_nombre`, `empleado_legajo`, `empleado_cuil`, `empleado_obra_social`, `empleado_nro_carnet`, `empleado_fecha_nacimiento`, `medico_nombre`

### Signos Vitales (`/api/signos-vitales`)
| Metodo | Ruta | Descripcion | Roles |
|--------|------|-------------|-------|
| POST | `/api/signos-vitales` | Crear | admin, medico |
| GET | `/api/signos-vitales/by-atencion/{id}` | Obtener por atencion | autenticado |
| PUT | `/api/signos-vitales/{id}` | Actualizar | admin, medico |

### Evoluciones (`/api/evoluciones`)
| Metodo | Ruta | Descripcion | Roles |
|--------|------|-------------|-------|
| POST | `/api/evoluciones` | Crear | admin, medico |
| GET | `/api/evoluciones/by-atencion/{id}` | Listar por atencion | autenticado |
| GET | `/api/evoluciones/{id}` | Detalle | autenticado |
| PUT | `/api/evoluciones/{id}` | Actualizar | admin, medico |

### Recetas (`/api/recetas`)
| Metodo | Ruta | Descripcion | Roles |
|--------|------|-------------|-------|
| POST | `/api/recetas` | Crear con items | admin, medico |
| GET | `/api/recetas/by-atencion/{id}` | Listar por atencion | autenticado |
| GET | `/api/recetas/{id}` | Detalle con items | autenticado |

### Pedidos (`/api/pedidos`)
| Metodo | Ruta | Descripcion | Roles |
|--------|------|-------------|-------|
| POST | `/api/pedidos` | Crear con items | admin, medico |
| GET | `/api/pedidos/by-atencion/{id}` | Listar por atencion | autenticado |
| GET | `/api/pedidos/{id}` | Detalle con items | autenticado |

### Estudios Catalogo (`/api/estudios-catalogo`)
| Metodo | Ruta | Descripcion | Roles |
|--------|------|-------------|-------|
| GET | `/api/estudios-catalogo` | Listar (tipo, activo) | autenticado |
| POST | `/api/estudios-catalogo` | Crear | admin |
| PUT | `/api/estudios-catalogo/{id}` | Actualizar | admin |

### Configuracion (`/api/configuracion`)
| Metodo | Ruta | Descripcion | Roles |
|--------|------|-------------|-------|
| GET | `/api/configuracion` | Listar todas las claves | autenticado |
| PUT | `/api/configuracion/{clave}` | Actualizar valor | admin |

### Adjuntos (`/api/adjuntos`)
| Metodo | Ruta | Descripcion | Roles |
|--------|------|-------------|-------|
| POST | `/api/adjuntos` | Upload (multipart) | admin, rrhh, medico |
| GET | `/api/adjuntos/by-licencia/{id}` | Listar por licencia | autenticado |
| GET | `/api/adjuntos/by-atencion/{id}` | Listar por atencion | autenticado |
| GET | `/api/adjuntos/{id}/download` | URL firmada descarga | autenticado |

### Reportes (`/api/reportes`)
| Metodo | Ruta | Descripcion | Roles |
|--------|------|-------------|-------|
| GET | `/api/reportes/por-area` | Ausentismo por area | autenticado |
| GET | `/api/reportes/por-categoria-diag` | Por categoria/diagnostico | autenticado |
| GET | `/api/reportes/mensual` | Reporte mensual | autenticado |

Todos aceptan `desde`, `hasta`, `format=csv` para exportar.

---

## Frontend — Rutas y Paginas

### Rutas Publicas
| Ruta | Componente | Descripcion |
|------|-----------|-------------|
| `/login` | LoginPage | Formulario email/password |

### Rutas Protegidas (autenticado)
| Ruta | Componente | Descripcion |
|------|-----------|-------------|
| `/` | DashboardPage | Cards resumen, accesos rapidos, actividad reciente |
| `/empleados` | EmpleadosListPage | Busqueda, tabla paginada |
| `/empleados/nuevo` | EmpleadoCreateForm | Formulario con catalogos |
| `/empleados/:id/editar` | EmpleadoEditPage | Edicion (legajo no editable) |
| `/empleados/:id/historia-clinica` | HistoriaClinicaPage | Historia completa + boton PDF |
| `/licencias` | LicenciasListPage | Filtros estado/vigente/fecha |
| `/licencias/nueva` | LicenciaForm | Formulario + adjunto |
| `/licencias/:id` | LicenciaDetailPage | Detalle + workflow + tope + adjuntos |
| `/atenciones` | AtencionesListPage | Lista con filtros |
| `/atenciones/nueva` | AtencionCreatePage | Turno + medico + adjunto |
| `/atenciones/:id` | AtencionDetailPage | 6 tabs (info, signos, evolucion, recetas, pedidos, adjuntos) |
| `/reportes` | ReportesPage | 3 tipos + export CSV |

### Rutas Admin (rol: admin)
| Ruta | Componente | Descripcion |
|------|-----------|-------------|
| `/admin/topes` | TopesPage | Matriz categorias x tipos (editable) |
| `/admin/usuarios` | UsuariosPage | CRUD usuarios |
| `/admin/areas` | AreasPage | CRUD areas |
| `/admin/categorias` | CategoriasPage | CRUD categorias |
| `/admin/tipos-licencia` | TiposLicenciaPage | CRUD tipos licencia |
| `/admin/estudios-catalogo` | EstudiosCatalogoPage | CRUD catalogo estudios |
| `/admin/configuracion` | ConfiguracionPage | Header/footer PDF configurable |

---

## Frontend — Componentes UI (`/src/components/ui/`)

| Componente | Props principales | Uso |
|-----------|------------------|-----|
| Button | variant (primary/secondary/danger/ghost), size, loading | Botones con spinner |
| Input | label, error, helper, tipo HTML | Campos de texto |
| Select | label, error, placeholder, children | Dropdowns |
| Card, CardBody, CardFooter | className | Contenedores |
| Modal | open, onClose, title, actions, size | Dialogos modales |
| Badge | variant (gray/blue/green/red/amber), size | Etiquetas de estado |
| PageHeader | title, subtitle, actions | Cabecera de pagina |
| Tabs | tabs[], active, onChange | Navegacion por pestanas |
| Table, THead, TBody, TH, TD, TR | className, onClick (TR) | Tablas con hover |
| Spinner | size (sm/md/lg) | Indicador de carga |
| EmptyState | icon, message, description, action | Estado vacio |

---

## Frontend — Autenticacion

### AuthContext (`/src/auth/AuthContext.tsx`)
- Provee `useAuth()` hook: `{ user, ready, login(), logout() }`
- Tokens en localStorage: `med:access`, `med:refresh`
- Interceptor axios: inyecta Authorization header, 401 → logout

### ProtectedRoute (`/src/auth/ProtectedRoute.tsx`)
- Wrappea rutas, redirige a `/login` si no autenticado
- Prop `roles` opcional para restringir por rol

### Tipo User (Me)
```typescript
{ id: string, email: string, nombre: string | null, rol: "admin" | "medico" | "rrhh", matricula: string | null, activo: boolean }
```

---

## Frontend — Clientes API (`/src/api/`)

| Archivo | Funciones principales |
|---------|----------------------|
| `http.ts` | Instancia axios con baseURL + token interceptor |
| `auth.ts` | login, refresh, me |
| `empleados.ts` | list, count, get, create, update |
| `licencias.ts` | count, list, get, create, enviar, validar, rechazar, anular, evaluarTope |
| `catalogos.ts` | areas, categorias, tiposLicencia |
| `adjuntos.ts` | upload, downloadUrl |
| `reportes.ts` | porArea, porCategoriaDiag, mensual, downloadCsv |
| `topes.ts` | list, set |

---

## Permisos por Rol

| Funcionalidad | admin | medico | rrhh |
|--------------|-------|--------|------|
| Ver empleados/licencias/atenciones | si | si | si |
| Crear/editar empleados | si | no | si |
| Crear licencias | si | si | si |
| Validar/rechazar licencias | si | si | no |
| Anular licencias | si | no | no |
| Crear atenciones | si | si | si |
| Completar atenciones | si | si | no |
| Cancelar atenciones | si | no | si |
| Registrar signos/evoluciones/recetas/pedidos | si | si | no |
| Subir adjuntos en atenciones | si | si | no |
| Admin (usuarios, catalogos, topes, configuracion) | si | no | no |
| Reportes | si | si | si |
| Historia clinica + PDF | si | si | si |

---

## Patrones de Codigo

### Backend — Patron por Modulo
Cada modulo tiene la misma estructura:
```
modulo/
├── __init__.py
├── models.py      # SQLAlchemy model
├── schemas.py     # Pydantic schemas (Create, Update, Out)
├── repository.py  # DB queries (async, recibe session)
├── service.py     # Logica de negocio
└── router.py      # FastAPI router (endpoints)
```

### Backend — Enrichment Pattern
Para mostrar nombres relacionados sin JOINs en el ORM:
```python
# En repository.py
async def _enrich(s: AsyncSession, rows: list[Model]) -> None:
    ids = {r.related_id for r in rows}
    result = await s.execute(select(Related).where(Related.id.in_(ids)))
    mapping = {r.id: r for (r,) in result}
    for r in rows:
        related = mapping.get(r.related_id)
        r.related_nombre = f"{related.apellido}, {related.nombre}" if related else None  # type: ignore[attr-defined]

# En schemas.py
class ModelOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    related_nombre: str | None = None  # Campo enriquecido, default None
```

### Backend — Dependency Injection
```python
from app.core.deps import get_session, current_user
from app.core.permissions import require_role

@router.post("/", dependencies=[Depends(require_role("admin", "medico"))])
async def create(payload: SchemaCreate, s: AsyncSession = Depends(get_session), user = Depends(current_user)):
    ...
```

### Frontend — Patron de Pagina
```tsx
export function FeaturePage() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);

  async function reload() {
    setLoading(true);
    try {
      const { data } = await http.get("/api/...");
      setData(data);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { reload(); }, []);

  // render con Card, Table, Modal, etc.
}
```

### Frontend — Formulario con setF helper
```tsx
const [form, setForm] = useState({ campo1: "", campo2: "" });
function setF<K extends keyof typeof form>(k: K, v: string) {
  setForm((p) => ({ ...p, [k]: v }));
}
// Uso: onChange={(e) => setF("campo1", e.target.value)}
```

---

## Tema Visual

- **Colores principales**: Navy (#1E3A5F) sidebar, Cyan (#00AEEF) accent
- **Fondo**: #F3F5F7, Cards: #FFFFFF
- **Texto**: heading #2A2A2A, body #494949, muted #94A3B8
- **Bordes**: #E2E8F0
- **Font**: Inter (system-ui fallback)
- **Gradiente**: `.gradient-va` navy→cyan diagonal, `.gradient-va-horizontal` horizontal
- **Transiciones**: `.transition-default` 200ms ease-in-out

---

## Comandos de Desarrollo

```bash
# Levantar servicios (postgres + minio)
docker compose up -d

# Backend (desde /backend)
POSTGRES_HOST=localhost uv run uvicorn app.main:app --host 0.0.0.0 --port 8000

# Frontend (desde /frontend)
npm run dev    # http://localhost:5173

# Migraciones
cd backend && POSTGRES_HOST=localhost uv run alembic upgrade head

# Crear nueva migracion
cd backend && POSTGRES_HOST=localhost uv run alembic revision --autogenerate -m "descripcion"

# Seed datos de prueba
cd backend && POSTGRES_HOST=localhost uv run python -m scripts.seed_dev
uv run python scripts/seed_clinical_data.py

# Tests
cd backend && uv run pytest
cd frontend && npm test
cd frontend && npx playwright test
```

---

## Produccion

```bash
# Primera vez
./scripts/bootstrap.sh

# Deploy
docker compose -f docker-compose.prod.yml up -d --build

# Backup
./scripts/backup.sh

# Restore
./scripts/restore.sh <archivo_backup>

# Migrar a otro servidor
./scripts/migrate.sh user@host /path/deploy
```

---

## Decisiones de Diseno

1. **UUID7** en lugar de auto-increment para todas las PKs (ordenable por tiempo)
2. **Diagnostico como texto libre** — se elimino la tabla `diagnosticos` y FKs a favor de campos String(500) editables
3. **Enrichment en repository** — los nombres de entidades relacionadas se agregan como atributos dinamicos en el ORM, no con JOINs en el schema Pydantic
4. **Adjuntos exclusivos** — cada adjunto pertenece a UNA licencia O UNA atencion (nunca ambas)
5. **Estado machine en licencias** — transiciones validadas en backend, no en frontend
6. **RRHH no ve diagnostico** — datos medicos redactados para rol RRHH en licencias
7. **Recetas/pedidos con items** — relacion 1:N con cascade delete
8. **MinIO signed URLs** — archivos nunca se sirven directamente, siempre via URL temporal firmada
9. **ReportLab para PDF** — generacion server-side de historia clinica
10. **Tabs en atencion** — UI separada por dominio clinico (signos, evolucion, recetas, pedidos, adjuntos)
11. **Configuracion key-value** — tabla `configuracion` con claves como `pdf_header_linea1`, permite al admin personalizar header/footer de PDFs e impresiones
12. **Impresion HTML** — recetas y pedidos se imprimen via `window.open()` + HTML template + `window.print()`, con header/footer leidos de `/api/configuracion`
13. **Datos del paciente en impresion** — pedidos muestran nombre, edad (calculada de fecha_nacimiento), obra social, nro carnet, peso y estatura (de signos vitales)
