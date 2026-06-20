# Sistema de Medicina Laboral — Municipalidad de Villa Allende

## Descripcion General

Sistema integral de gestion de medicina laboral desarrollado para la Municipalidad de Villa Allende. Permite administrar la salud ocupacional de los empleados municipales, incluyendo el control de licencias medicas, atenciones clinicas, historia clinica digital, pedidos de estudios, recetas medicas y reportes de ausentismo.

El sistema esta orientado a tres perfiles de usuario: **administradores**, **medicos** del servicio de medicina laboral y personal de **recursos humanos (RRHH)**.

---

## Acceso al Sistema

### Pantalla de Login

El sistema requiere autenticacion con email y contrasena. Al ingresar, el usuario accede a un panel principal (dashboard) con informacion resumida segun su rol.

### Roles de Usuario

| Rol | Descripcion |
|-----|------------|
| **Admin** | Acceso completo. Gestiona usuarios, catalogos, configuracion y todas las funcionalidades clinicas y administrativas. |
| **Medico** | Acceso clinico completo. Registra atenciones, signos vitales, evoluciones, recetas, pedidos. Valida licencias. No gestiona empleados ni catalogos. |
| **RRHH** | Acceso administrativo. Gestiona empleados, crea licencias y atenciones. No accede a funciones clinicas (evoluciones, recetas, pedidos). No ve diagnosticos medicos. |

---

## Secciones del Sistema

### 1. Dashboard (Pagina de Inicio)

Al ingresar, el usuario ve un panel con:

- **Cards de resumen**: cantidad de empleados activos, licencias vigentes, atenciones pendientes.
- **Accesos rapidos**: botones para crear nueva licencia, nueva atencion, nuevo empleado.
- **Actividad reciente**: ultimas acciones realizadas en el sistema.

El dashboard se adapta al rol del usuario, mostrando solo la informacion y acciones relevantes.

---

### 2. Empleados

Modulo central para la gestion del personal municipal.

#### Lista de Empleados (`/empleados`)

- Tabla paginada con todos los empleados registrados.
- Busqueda por nombre, apellido, legajo o CUIL.
- Cada fila muestra: legajo, nombre completo, CUIL, area, categoria, estado (activo/inactivo).
- Click en una fila permite acceder a la edicion o historia clinica.

#### Crear Empleado (`/empleados/nuevo`)

Formulario para registrar un nuevo empleado con los siguientes datos:

- **Datos de identificacion**: legajo (unico, solo numeros), CUIL (formato XX-XXXXXXXX-X).
- **Datos personales**: nombre, apellido, fecha de nacimiento, email, telefono.
- **Datos de salud**: obra social (ej: OSDE, APROSS), numero de carnet de obra social.
- **Datos laborales**: area, categoria laboral, fecha de ingreso, supervisor (opcional), estado activo/inactivo.

#### Editar Empleado (`/empleados/:id/editar`)

Permite modificar todos los datos del empleado excepto legajo, CUIL y fecha de ingreso (que son inmutables). Incluye los campos de obra social y numero de carnet.

#### Historia Clinica (`/empleados/:id/historia-clinica`)

Vista completa del historial medico del empleado, que reune toda la informacion clinica generada en sus atenciones:

- **Datos del paciente**: nombre, legajo, CUIL, fecha de nacimiento, obra social.
- **Atenciones**: listado cronologico de todas las atenciones con su fecha, motivo, estado y notas medicas.
- **Signos vitales**: registro de cada toma de signos (peso, altura, IMC, presion arterial, temperatura, frecuencia cardiaca, saturacion O2, glucemia).
- **Evoluciones**: notas clinicas con motivo de consulta, anamnesis, examen fisico, diagnosticos y tratamiento.
- **Recetas**: recetas medicas emitidas con detalle de medicamentos, dosis, frecuencia y duracion.
- **Pedidos**: pedidos de estudios (laboratorio, imagen, interconsulta) con listado de practicas solicitadas.
- **Licencias**: historial de licencias del empleado con tipo, fechas, diagnostico y estado.

Incluye boton para **descargar PDF** con toda la historia clinica, generado en el servidor con header y footer institucional configurable.

---

### 3. Licencias Medicas

Modulo para la gestion completa del ciclo de vida de las licencias.

#### Lista de Licencias (`/licencias`)

- Tabla paginada con filtros por: estado, empleado, area, rango de fechas, licencias vigentes.
- Cada fila muestra: empleado, tipo de licencia, fechas, dias solicitados/otorgados, estado.
- Codigo de colores por estado: borrador (gris), enviado (azul), validado (verde), rechazado (rojo), anulado (gris oscuro).

#### Nueva Licencia (`/licencias/nueva`)

Formulario para crear una licencia con:

- **Empleado**: selector con busqueda.
- **Tipo de licencia**: seleccion del catalogo (enfermedad comun, accidente laboral, maternidad, etc.).
- **Fechas**: desde/hasta con calculo automatico de dias.
- **Diagnostico**: campo de texto libre (solo visible para medicos y admin, oculto para RRHH).
- **Certificante**: nombre y matricula del medico certificante.
- **Modo de constatacion**: presencial, telefonica o virtual.
- **Origen**: si la licencia fue cargada por RRHH o por el medico.
- **Observaciones**: notas adicionales.
- **Adjunto**: posibilidad de subir certificado medico (PDF, imagen).

#### Detalle de Licencia (`/licencias/:id`)

Vista completa de la licencia con:

- **Datos del empleado**: nombre, legajo, CUIL, area.
- **Datos de la licencia**: tipo, fechas, dias, diagnostico (redactado para RRHH), certificante, modo de constatacion.
- **Estado y workflow**: botones de accion segun el estado actual y el rol del usuario.
- **Evaluacion de tope**: comparacion automatica contra los topes de dias configurados para la categoria del empleado y el tipo de licencia.
- **Adjuntos**: certificados adjuntos con opcion de descarga.
- **Historial**: quien creo, quien valido, fechas de cada accion.

#### Workflow de Estados

```
BORRADOR → ENVIADO → VALIDADO
                   → RECHAZADO
VALIDADO → ANULADO
```

- **Borrador**: licencia recien creada, puede editarse.
- **Enviado**: enviada a validacion medica.
- **Validado**: aprobada por medico/admin, se registran los dias otorgados.
- **Rechazado**: rechazada con motivo obligatorio.
- **Anulado**: solo el admin puede anular una licencia ya validada, con motivo.

#### Topes de Dias

El sistema controla que un empleado no exceda los dias maximos de licencia segun su categoria laboral y tipo de licencia. La evaluacion se hace automaticamente al consultar el detalle.

---

### 4. Atenciones Clinicas

Modulo para gestionar los turnos y consultas medicas de los empleados.

#### Lista de Atenciones (`/atenciones`)

- Tabla con filtros por: estado, empleado, medico, fecha.
- Cada fila muestra: empleado, fecha del turno, motivo, medico asignado, estado.
- Estados: pendiente (amarillo), completada (verde), cancelada (rojo).

#### Nueva Atencion (`/atenciones/nueva`)

Formulario para agendar un turno:

- Seleccion de empleado (con busqueda).
- Medico asignado (opcional, puede asignarse despues).
- Fecha y hora del turno.
- Motivo de la consulta.

#### Detalle de Atencion (`/atenciones/:id`)

La pagina de detalle se organiza en **6 pestanas**:

##### Pestana: Informacion

Datos generales de la atencion: paciente, legajo, CUIL, fecha del turno, medico, motivo, estado, notas medicas. Botones para completar (medico/admin) o cancelar (rrhh/admin) la atencion.

##### Pestana: Signos Vitales

Registro de signos vitales del paciente (relacion 1:1 con la atencion):

- Peso (kg), Altura (cm), IMC (calculado automaticamente).
- Presion arterial (sistolica/diastolica).
- Temperatura corporal.
- Frecuencia cardiaca.
- Saturacion de oxigeno (%).
- Glucemia.

##### Pestana: Evolucion

Notas de evolucion clinica (puede haber multiples por atencion):

- Motivo de consulta.
- Anamnesis (interrogatorio).
- Examen fisico.
- Diagnostico presuntivo.
- Diagnostico definitivo.
- Tratamiento indicado.
- Observaciones.

##### Pestana: Recetas

Recetas medicas asociadas a la atencion:

- Diagnostico de la receta.
- Lista de medicamentos con: nombre, dosis, frecuencia, duracion.
- Observaciones.
- **Boton Imprimir**: genera una pagina HTML con el formato de receta medica, incluyendo header institucional configurable, datos del paciente (nombre, legajo) y footer. Se abre en nueva ventana y ejecuta `window.print()` automaticamente.

##### Pestana: Pedidos

Pedidos de estudios medicos:

- **Tipo de pedido**: laboratorio, imagen (radiografia, ecografia, etc.), interconsulta, otro.
- **Diagnostico e indicaciones**: texto libre.
- **Items del pedido**: se seleccionan del catalogo de estudios (agrupados por categoria con checkboxes) o se agregan como texto libre.
- **Boton Imprimir**: genera una pagina HTML formato A4 con:
  - Header institucional configurable (3 lineas).
  - Tipo de pedido (badge de color).
  - Datos del paciente: nombre, edad (calculada de fecha de nacimiento), obra social, numero de carnet, peso y estatura (leidos de signos vitales).
  - Fecha de emision.
  - Diagnostico e indicaciones.
  - Tabla numerada de estudios/practicas solicitadas.
  - Espacio para firma y sello del medico.
  - Footer institucional configurable.

##### Pestana: Adjuntos

Archivos adjuntos vinculados a la atencion:

- Subida de archivos (PDF, PNG, JPG, JPEG, WEBP).
- Lista de adjuntos con nombre, tipo, tamano.
- Descarga via URL firmada temporal (MinIO/S3).

---

### 5. Reportes

El sistema genera tres tipos de reportes con filtros de fecha y exportacion a CSV.

#### Reporte por Area (`/reportes`)

- Ausentismo agrupado por area organizacional.
- Muestra: area, cantidad de licencias, dias totales, promedio por empleado.

#### Reporte por Categoria/Diagnostico

- Analisis de licencias agrupadas por categoria laboral y diagnostico.
- Permite identificar patrones de ausentismo por tipo de enfermedad.

#### Reporte Mensual

- Resumen mensual de licencias: cantidad, dias, comparativo.
- Permite ver tendencias a lo largo del tiempo.

Todos los reportes aceptan filtros de rango de fechas (`desde`, `hasta`) y pueden exportarse a CSV para analisis externo.

---

### 6. Administracion

Seccion exclusiva para usuarios con rol **admin**.

#### Usuarios (`/admin/usuarios`)

- Lista de usuarios del sistema.
- Crear nuevos usuarios con: email, nombre, rol (admin/medico/rrhh), matricula (solo medicos), contrasena.

#### Areas (`/admin/areas`)

- CRUD de areas organizacionales de la municipalidad.
- Soporte para jerarquia (areas padre/hijo).

#### Categorias Laborales (`/admin/categorias`)

- CRUD de categorias laborales (ej: planta permanente, contratado, monotributista).
- Cada categoria tiene un codigo unico y estado activo/inactivo.

#### Tipos de Licencia (`/admin/tipos-licencia`)

- CRUD del catalogo de tipos de licencia.
- Cada tipo tiene: codigo, nombre, base legal (ley/articulo), si se paga, si computa dias para topes.

#### Topes de Dias (`/admin/topes`)

- Matriz editable de topes maximos de dias por combinacion de categoria laboral y tipo de licencia.
- Configurable con ventana de evaluacion: anio calendario, anio aniversario o sin limite.
- Vigencia temporal (desde/hasta).

#### Catalogo de Estudios (`/admin/estudios-catalogo`)

- CRUD del catalogo de estudios y practicas medicas.
- Cada estudio tiene: nombre, codigo, tipo (laboratorio/imagen/otro), categoria, estado activo/inactivo.
- Actualmente incluye 55+ estudios organizados en categorias:
  - **Laboratorio**: Hematologia, Bioquimica, Serologias, Orina, Endocrinologia, Hepaticos, Coagulacion, Alergias/Inmunologia.
  - **Imagen**: Radiologia, Ecografia, Tomografia, Resonancia, Otros.

#### Configuracion (`/admin/configuracion`)

- Configuracion de header y footer para impresiones y PDFs.
- Claves editables:
  - `pdf_header_linea1`: primera linea del encabezado (ej: "Municipalidad de Villa Allende").
  - `pdf_header_linea2`: segunda linea (ej: "Servicio de Medicina Laboral").
  - `pdf_header_linea3`: tercera linea opcional (direccion, telefono).
  - `pdf_footer`: pie de pagina (ej: "Documento confidencial - Uso exclusivo del servicio de medicina laboral").
- Los valores se aplican a: impresion de recetas, impresion de pedidos, PDF de historia clinica.

---

## Funcionalidades Transversales

### Impresion de Documentos

El sistema permite imprimir dos tipos de documentos clinicos directamente desde el navegador:

- **Recetas medicas**: formato imprimible con header institucional, datos del paciente, lista de medicamentos con posologia, y footer. Se genera como HTML y se imprime via `window.print()`.
- **Pedidos de estudios**: formato A4 con header institucional, datos completos del paciente (nombre, edad, obra social, nro carnet, peso, estatura), listado de practicas solicitadas, espacio para firma medica y footer.

Ambos documentos usan el header y footer configurados en `/admin/configuracion`.

### Historia Clinica en PDF

La historia clinica completa de un empleado puede descargarse como PDF generado en el servidor (ReportLab). Incluye todos los datos clinicos (atenciones, signos vitales, evoluciones, recetas, pedidos, licencias) con header y footer institucional configurable.

### Adjuntos

Los archivos se almacenan en MinIO (compatible con S3). Se soportan PDF e imagenes. La descarga se realiza via URLs firmadas temporales, sin exponer los archivos directamente.

### Auditoria

Todas las acciones relevantes del sistema quedan registradas en una tabla de auditoria con: timestamp, usuario, accion, entidad afectada, datos del cambio, IP y user-agent.

### Seguridad

- Autenticacion JWT con tokens de acceso (15 min) y refresh (7 dias).
- Contrasenas hasheadas con Argon2.
- Control de acceso por roles en cada endpoint.
- Proteccion contra fuerza bruta en login (throttle).
- RRHH no accede a datos medicos sensibles (diagnosticos redactados).
- CORS configurado para origenes especificos.

---

## Arquitectura Tecnica

| Componente | Tecnologia |
|-----------|------------|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.0 async |
| Base de datos | PostgreSQL 16 |
| Frontend | React 18, TypeScript, Vite, TailwindCSS |
| Almacenamiento | MinIO (S3-compatible) |
| PDF | ReportLab 4.x |
| Contenedores | Docker Compose |
| Proxy | Nginx (produccion) |
| SSL | Let's Encrypt / Certbot |

### Entorno de Desarrollo

- Backend: `uv run uvicorn app.main:app --host 0.0.0.0 --port 8000`
- Frontend: `npm run dev` (Vite en puerto 5173)
- Base de datos y MinIO: `docker compose up -d`

### Produccion

- Todo containerizado con Docker Compose.
- Nginx como reverse proxy con TLS.
- Scripts de backup, restore y migracion incluidos.

---

## Historial de Cambios

### Version actual (junio 2026)

- Sistema completo con gestion de empleados, licencias, atenciones clinicas.
- 6 tabs en detalle de atencion: info, signos vitales, evolucion, recetas, pedidos, adjuntos.
- Historia clinica digital con exportacion PDF.
- Impresion de recetas y pedidos medicos con header/footer configurable.
- Datos de obra social y nro de carnet en empleados y en impresion de pedidos.
- Datos del paciente en impresion: edad, peso, estatura, obra social.
- Catalogo de 55+ estudios de laboratorio e imagen.
- Modo de constatacion en licencias (presencial, telefonica, virtual).
- Modulo de configuracion para personalizar impresiones.
- 3 reportes de ausentismo con exportacion CSV.
- 18 tablas en base de datos, 16 modulos de backend.
- Control de acceso por roles (admin, medico, rrhh).
