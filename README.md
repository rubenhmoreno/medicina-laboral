# Medicina Laboral — Municipalidad de Villa Allende

Sistema integral de gestion de medicina laboral. Administra la salud ocupacional de empleados municipales: licencias medicas, atenciones clinicas, historia clinica digital, pedidos de estudios, recetas medicas y reportes de ausentismo.

---

## Stack Tecnologico

| Capa | Tecnologia |
|------|------------|
| Backend | Python 3.12 · FastAPI · SQLAlchemy 2.0 async · asyncpg |
| Base de datos | PostgreSQL 16 |
| Frontend | React 18 · TypeScript · Vite · TailwindCSS |
| Almacenamiento | MinIO (S3-compatible) |
| PDF | ReportLab 4.x |
| Auth | JWT + Argon2 |
| Contenedores | Docker Compose |
| Proxy / SSL | Nginx · Let's Encrypt |

---

## Inicio Rapido

```bash
# 1. Clonar y configurar
cp .env.example .env        # editar con tus valores

# 2. Levantar postgres + minio
docker compose up -d

# 3. Backend (desde /backend)
POSTGRES_HOST=localhost uv run alembic upgrade head
POSTGRES_HOST=localhost uv run python -m scripts.seed_dev
POSTGRES_HOST=localhost uv run uvicorn app.main:app --host 0.0.0.0 --port 8000

# 4. Frontend (desde /frontend)
npm install && npm run dev
```

Acceder a `http://localhost:5173` — login default: `admin` / `123`

---

## Roles de Usuario

| Rol | Descripcion |
|-----|------------|
| **Admin** | Acceso completo. Gestiona usuarios, catalogos, configuracion y todas las funcionalidades clinicas y administrativas. |
| **Medico** | Acceso clinico. Registra atenciones, signos vitales, evoluciones, recetas, pedidos. Valida licencias. |
| **RRHH** | Acceso administrativo. Gestiona empleados, crea licencias y atenciones. No ve diagnosticos medicos. |

---

## Secciones del Sistema

### Dashboard

Panel principal con cards de resumen (empleados activos, licencias vigentes, atenciones pendientes), accesos rapidos y actividad reciente. Se adapta al rol del usuario.

### Empleados

Gestion completa del personal municipal.

- **Lista**: tabla paginada con busqueda por nombre, legajo o CUIL.
- **Crear / Editar**: datos personales (nombre, CUIL, fecha nacimiento, email, telefono), datos de salud (obra social, nro carnet), datos laborales (area, categoria, supervisor).
- **Historia Clinica**: vista unificada de todo el historial medico del empleado (atenciones, signos vitales, evoluciones, recetas, pedidos, licencias). Exportable a PDF con header/footer institucional configurable.

### Licencias Medicas

Ciclo de vida completo de licencias con maquina de estados.

- **Formulario**: empleado, tipo de licencia, fechas, diagnostico (oculto para RRHH), certificante, modo de constatacion (presencial/telefonica/virtual), adjunto de certificado.
- **Workflow**: `borrador → enviado → validado | rechazado`. Licencias validadas pueden anularse (solo admin).
- **Topes**: evaluacion automatica contra topes de dias configurados por categoria laboral y tipo de licencia.
- **Filtros**: estado, empleado, area, rango de fechas, vigentes.

### Atenciones Clinicas

Turnos y consultas medicas organizados en 6 pestanas:

| Pestana | Contenido |
|---------|-----------|
| **Informacion** | Datos del paciente, turno, medico, estado. Acciones: completar / cancelar. |
| **Signos Vitales** | Peso, altura, IMC, presion arterial, temperatura, FC, SpO2, glucemia. |
| **Evolucion** | Motivo, anamnesis, examen fisico, diagnosticos, tratamiento, observaciones. Multiples por atencion. |
| **Recetas** | Medicamentos con dosis, frecuencia y duracion. Boton imprimir con header/footer configurable. |
| **Pedidos** | Estudios de laboratorio, imagen, interconsulta. Selector con catalogo agrupado por categoria. Boton imprimir A4 con datos del paciente (nombre, edad, obra social, peso, estatura). |
| **Adjuntos** | Upload/download de archivos (PDF, imagenes) via MinIO. |

### Reportes

Tres tipos de reportes, todos con filtros de fecha y exportacion CSV:

- **Por area**: ausentismo agrupado por area organizacional.
- **Por categoria/diagnostico**: patrones de ausentismo por tipo de enfermedad.
- **Mensual**: resumen y tendencias mensuales.

### Administracion (solo admin)

| Seccion | Descripcion |
|---------|------------|
| Usuarios | Crear usuarios con rol (admin/medico/rrhh) y matricula. |
| Areas | Jerarquia de areas organizacionales. |
| Categorias | Categorias laborales (planta permanente, contratado, etc.). |
| Tipos de Licencia | Catalogo con base legal, pago y computo de dias. |
| Topes de Dias | Matriz de dias maximos por categoria x tipo licencia. |
| Catalogo Estudios | 55+ estudios de laboratorio e imagen organizados por categoria. |
| Configuracion | Header/footer configurable para impresiones y PDFs. |

---

## Impresion de Documentos

El sistema genera documentos imprimibles desde el navegador:

- **Recetas medicas**: header institucional, datos del paciente, medicamentos con posologia, footer.
- **Pedidos de estudios**: formato A4 con datos completos del paciente (nombre, edad, obra social, nro carnet, peso, estatura), lista de practicas, firma del medico.
- **Historia clinica PDF**: generado en el servidor con todo el historial del empleado.

Header y footer configurables desde `/admin/configuracion`.

---

## Seguridad

- JWT con access token (15 min) + refresh token (7 dias).
- Passwords con Argon2.
- RBAC por endpoint.
- Throttle en login (anti brute-force).
- Diagnosticos redactados para RRHH.
- Adjuntos via URLs firmadas temporales.
- Auditoria completa (usuario, accion, entidad, payload, IP).

---

## Base de Datos

18 tablas con UUID7 como PK:

`usuarios` · `empleados` · `areas` · `categorias_laborales` · `tipos_licencia` · `topes_dias` · `licencias` · `atenciones` · `signos_vitales` · `evoluciones` · `recetas` · `items_receta` · `pedidos` · `items_pedido` · `estudios_catalogo` · `adjuntos` · `configuracion` · `auditoria`

---

## Estructura del Proyecto

```
medicia-laboral/
├── backend/
│   ├── app/
│   │   ├── core/           # Config, auth, DB, storage, middleware
│   │   ├── main.py          # FastAPI app + routers
│   │   └── modules/         # 16 modulos de negocio
│   ├── alembic/versions/    # 9 migraciones
│   └── scripts/             # seed_dev.py
├── frontend/src/
│   ├── api/                 # Clientes HTTP (axios)
│   ├── auth/                # AuthContext, ProtectedRoute
│   ├── components/ui/       # 12 componentes reutilizables
│   ├── features/            # Paginas por dominio
│   │   ├── admin/           # Usuarios, catalogos, configuracion
│   │   ├── empleados/       # Lista, crear, editar, historia clinica
│   │   ├── licencias/       # Lista, formulario, detalle
│   │   ├── atenciones/      # Lista, crear, detalle (6 tabs)
│   │   └── reportes/        # 3 reportes + CSV
│   └── layout/              # Sidebar + topbar
├── scripts/                 # bootstrap, backup, restore, migrate
├── nginx/                   # Reverse proxy produccion
├── docker-compose.yml       # Dev
├── docker-compose.prod.yml  # Produccion
├── SISTEMA.md               # Documentacion funcional detallada
└── CLAUDE.md                # Referencia tecnica del proyecto
```

---

## Produccion

```bash
# Deploy
docker compose -f docker-compose.prod.yml up -d --build

# Backup / Restore
./scripts/backup.sh
./scripts/restore.sh <archivo>

# Migrar a otro servidor
./scripts/migrate.sh user@host /path
```

---

## Documentacion

| Archivo | Contenido |
|---------|-----------|
| `README.md` | Este archivo — vision general del sistema. |
| `SISTEMA.md` | Documentacion funcional detallada de cada seccion y funcionalidad. |
| `CLAUDE.md` | Referencia tecnica completa: esquema DB, endpoints API, patrones de codigo, variables de entorno. |

---

## Historial de Versiones

### Junio 2026 — Version actual

- Gestion completa de empleados con obra social y nro carnet.
- Licencias con workflow de estados y modo de constatacion.
- Atenciones clinicas con 6 tabs: info, signos vitales, evolucion, recetas, pedidos, adjuntos.
- Historia clinica digital con exportacion PDF.
- Impresion de recetas y pedidos con header/footer configurable.
- Datos del paciente en impresion de pedidos: edad, peso, estatura, obra social.
- Catalogo de 55+ estudios de laboratorio e imagen.
- Configuracion de header/footer desde panel admin.
- 3 reportes de ausentismo con export CSV.
- 18 tablas, 16 modulos backend, control de acceso por roles.
