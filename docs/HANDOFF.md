# HANDOFF — medicia-laboral

**Para la próxima sesión de Claude Code (u otro agente).** Leé este archivo de punta a punta antes de tocar nada. Es la guía operativa para continuar la ejecución del plan sin perder contexto.

---

## TL;DR

Estás a cargo de **ejecutar el plan de implementación** del sistema `medicia-laboral` (gestión de ausentismo y licencias médicas) usando la skill `superpowers:subagent-driven-development`. El plan tiene ~70 tareas distribuidas en 12 fases. Tres tareas ya se completaron en una sesión previa (Fase 0 tasks 0.1, 0.2, 0.3). **La próxima tarea es la 0.4.**

Trabajás en `/home/mva/medicia-laboral`, rama `main`, con consentimiento explícito del usuario para commitear directamente ahí.

---

## 1. Contexto del proyecto

- **Dominio:** medicina laboral / ausentismo / licencias médicas.
- **Stack:** Python 3.12 + FastAPI + Postgres 16 + MinIO (backend) · React 18 + Vite + TypeScript (frontend) · Docker Compose · GitHub Actions.
- **Escala objetivo:** 200–2000 empleados, 5–20 usuarios concurrentes.
- **Marco regulatorio AR:** LCT, Ley 24.557 (LRT), Ley 25.326 (datos sensibles de salud).
- **Roles del sistema:** `admin`, `medico`, `rrhh`. El empleado **no** es usuario directo.
- **Sin integraciones externas en v1** (sin SSO, sin padrón, sin API ART).
- **Portabilidad es requisito de primer nivel:** todo va por `.env`, scripts `scripts/{bootstrap,backup,restore,migrate}.sh` deben permitirle a Claude Code futuro mover el sistema entre servidores sin intervención manual.

**Nota:** el nombre del directorio raíz sigue siendo `medicia-laboral` por conveniencia (renombrarlo requiere mover el repo git), pero el nombre oficial del sistema es **medicina-laboral**. Todas las referencias en código, UI, CI y configuración usan "medicina".

---

## 2. Documentos fuente de verdad

| Archivo | Qué es |
|---|---|
| `docs/superpowers/specs/2026-06-18-medicia-laboral-design.md` | Spec del sistema (555 líneas, aprobado por el usuario) |
| `docs/superpowers/plans/2026-06-18-medicia-laboral-implementation.md` | Plan de implementación TDD paso a paso (~7700 líneas, 12 fases) |
| `docs/HANDOFF.md` | Este archivo |
| `.git/sdd/progress.md` | **Ledger de progreso** — autoridad sobre qué tareas están completas |

**Antes de despachar cualquier subagente, releé el ledger** (`cat .git/sdd/progress.md`). No re-despaches tareas que ya figuran ahí como completas — son commits reales en git.

---

## 3. Estado actual al cierre de la sesión previa (2026-06-18)

### Git

- Branch: `main`
- HEAD: `4d96d73` (`feat(backend): scaffold FastAPI app with healthz`)
- Tareas SDD completas: **0.1, 0.2, 0.3**.
- Próxima tarea: **0.4** (primer test que falla + lint/type/test loop).
- BASE recomendada para Task 0.4: `4d96d73` (`git rev-parse HEAD`).

### Infraestructura

- Docker daemon disponible.
- Stack de dev (postgres + minio) corriendo en background, ambos `healthy`. Si pasó tiempo, levantar con `docker compose up -d`.
- `uv` instalado en `~/.local/bin/uv` (PATH puede no incluirlo: `export PATH="$HOME/.local/bin:$PATH"`).
- `backend/.venv/` con todas las deps sincronizadas (`uv sync` ya corrió).
- `pnpm` **NO instalado todavía** — lo necesitará la Task 0.5 (frontend Vite scaffold).

### Decisiones tomadas en sesión previa (mantenelas)

1. **Co-Authored-By trailer dropped** para commits de implementación. Los subagentes commitean con `git commit -m "subject"` plano. El trailer queda solo en commits manuales de artefactos (spec/plan/handoff). No le pidas trailer al implementer ni al reviewer.
2. **Ejecución continua sin pausas entre tareas** — la skill `subagent-driven-development` lo manda explícitamente. Solo parás por BLOCKED, ambigüedad genuina, o fin del plan.
3. **Modelo por defecto: `haiku`** para tareas mecánicas con código verbatim en el plan (la mayoría). Subir a `sonnet` solo para tareas con integración multi-archivo no trivial o decisiones de diseño. `opus` queda para el review final del branch.

---

## 4. Cómo continuar — el ciclo SDD por tarea

Estás usando `superpowers:subagent-driven-development`. El ciclo por tarea es:

```
1. Extraer brief  → scripts/task-brief PLAN N
2. Registrar BASE → git rev-parse HEAD
3. Despachar implementer subagente (Agent tool, model haiku/sonnet)
4. Esperar reporte (DONE / DONE_WITH_CONCERNS / NEEDS_CONTEXT / BLOCKED)
5. Generar paquete de review → scripts/review-package BASE HEAD
6. Despachar task reviewer subagente (Agent tool, mismo modelo)
7. Si APPROVED: append al ledger. Si NEEDS FIXES (Critical/Important): despachar fix subagente.
8. Avanzar a la siguiente tarea
```

### Comandos exactos por paso

```bash
# Working directory siempre
cd /home/mva/medicia-laboral

# Skill scripts viven acá
SKILL=/root/.claude/plugins/cache/claude-plugins-official/superpowers/6.0.2/skills/subagent-driven-development
PLAN=docs/superpowers/plans/2026-06-18-medicia-laboral-implementation.md

# 1) Extraer brief de la tarea N (ej. 0.4, 1.1, 3.2…)
"$SKILL/scripts/task-brief" "$PLAN" 0.4
# Output: wrote /home/mva/medicia-laboral/.git/sdd/task-0.4-brief.md: N lines

# 2) Registrar BASE
BASE=$(git rev-parse HEAD)
echo "BASE for Task 0.4: $BASE"

# … despachar implementer (ver template abajo) …

# 5) Generar paquete de review (después del DONE del implementer)
"$SKILL/scripts/review-package" "$BASE" <new-head-sha>
# Output: wrote /home/mva/medicia-laboral/.git/sdd/review-<base7>..<head7>.diff: ...

# 7) Anotar en ledger cuando reviewer APPROVED
echo "Task 0.4: complete (commits $BASE..<HEAD>, review APPROVED)" >> .git/sdd/progress.md
```

### Template de prompt para implementer subagente

Usar el tool `Agent` con `subagent_type: general-purpose`, `model: haiku` (subir a `sonnet` solo si la tarea es compleja):

```
You are implementing Task N: <nombre> of the medicia-laboral implementation plan.

## Where this fits

medicia-laboral repo at /home/mva/medicia-laboral, branch main.
<una o dos líneas de contexto sobre dónde encaja la tarea y qué se completó antes>

## Your task brief — READ THIS FIRST

/home/mva/medicia-laboral/.git/sdd/task-N-brief.md

It is your single source of requirements. Copy code blocks verbatim — every import, every blank line, every type hint.

## Working directory

/home/mva/medicia-laboral

## Before you begin

If anything is unclear, ASK before doing anything. Do not guess.

## Your job

1. Read the brief in full.
2. Execute each step in order, exactly as the brief specifies.
3. Run the verification commands the brief lists.
4. Commit with the brief's exact commit message (plain `git commit -m "subject"` — no Co-Authored-By trailer).
5. Self-review: re-read each file you touched.

## Code organization

- Use Write/Edit tools for files (no heredocs in Bash).
- Stage only the files this task creates/modifies (no `git add -A`).
- If a step expects tests to fail FIRST (TDD RED), confirm the failure mode matches what the brief expects before implementing.

## Report contract

Write your full report to:
/home/mva/medicia-laboral/.git/sdd/task-N-report.md

Format:
# Task N report
## Status
DONE | DONE_WITH_CONCERNS | NEEDS_CONTEXT | BLOCKED
## Commits
<short-sha> <subject>
## Verification
<commands run + relevant output>
## Self-review
<one or two sentences>
## Concerns
<empty unless any>

Return ONLY: status, commits short-shas, one-line verification summary, any concerns.
```

### Template de prompt para task reviewer subagente

```
You are reviewing Task N's implementation. Two verdicts: spec compliance + code quality. Task-scoped gate only.

## What was requested
Read the task brief: /home/mva/medicia-laboral/.git/sdd/task-N-brief.md

Global constraints binding this task:
- Portability: all config via .env, no hardcoded secrets.
- Folder name is `medicia-laboral` (intentional, not a typo).
- Conventional-commit subject. NO Co-Authored-By trailer required for impl commits.
- <constraints específicas de esta tarea: marco regulatorio, RBAC, append-only audit, etc.>

## Implementer's report
Read: /home/mva/medicia-laboral/.git/sdd/task-N-report.md

## Diff under review
**Base:** <BASE>
**Head:** <HEAD>
**Diff file:** /home/mva/medicia-laboral/.git/sdd/review-<base7>..<head7>.diff

Read the diff file once. That IS the change. Do not Read changed files separately unless a hunk is cut mid-context. Do not re-run git commands.

## Your job

### Verdict 1 — Spec compliance
- Each file the brief mandates exists at the right path with verbatim content?
- Anything in brief missing? Anything extra not requested?
- Commit subject matches brief? Single commit, only the right files?

### Verdict 2 — Code quality
- Tests assert the right behavior?
- Types/imports correct?
- Follows project patterns (router → service → repository)?
- No obvious smells (magic numbers, dead code, missing error handling on real failure modes)?

## Report format

# Task N review
## Spec compliance: ✅ | ❌
<findings with file:line refs>
## Code quality: ✅ | ❌
<findings>
## Findings
- Critical: <blockers>
- Important: <should-fix>
- Minor: <nice-to-have>
- ⚠️ Cannot verify from diff: <items for controller>
## Verdict
APPROVED | NEEDS FIXES
```

---

## 5. Tabla de modelos por tarea

| Tipo de tarea | Modelo |
|---|---|
| Tareas con código verbatim completo en el brief (la mayoría de Fase 0 a 5) | `haiku` |
| Tareas que tocan ≥3 archivos con integración entre módulos | `sonnet` |
| State machine (Task 6.2), evaluación de tope (6.3), service de licencias (6.6) | `sonnet` |
| Frontend con UX/diseño (Fase 8-9) | `haiku` cuando el código está en el brief, `sonnet` si requiere decisiones de layout |
| Scripts de portabilidad (Fase 11) | `haiku` |
| **Review final del branch entero (Task 22)** | `opus` |

Especificá **siempre** el modelo en el dispatch. Omitirlo hereda el modelo de la sesión y suele ser el más caro.

---

## 6. Estructura del directorio

```
/home/mva/medicia-laboral/
├── .git/sdd/                           # Ledger + briefs + reports + diff files (SDD state)
│   ├── progress.md                     # AUTORIDAD de qué está hecho
│   ├── task-N-brief.md                 # Generado por scripts/task-brief
│   ├── task-N-report.md                # Escrito por cada implementer
│   └── review-<base>..<head>.diff      # Generado por scripts/review-package
├── docs/
│   ├── HANDOFF.md                      # Este archivo
│   ├── MIGRATION.md                    # (se crea en Fase 11)
│   └── superpowers/
│       ├── specs/2026-06-18-medicia-laboral-design.md
│       └── plans/2026-06-18-medicia-laboral-implementation.md
├── backend/                            # Existe desde Task 0.3
│   ├── pyproject.toml                  # uv, ruff, mypy, pytest configurados
│   ├── .python-version                 # "3.12"
│   ├── uv.lock                         # commiteado
│   ├── .venv/                          # gitignored
│   ├── app/
│   │   ├── __init__.py                 # vacío
│   │   └── main.py                     # FastAPI app factory con /healthz
│   └── tests/
│       └── __init__.py                 # vacío
├── frontend/                           # Aún no existe (Task 0.5)
├── scripts/                            # Aún no existe (Fase 11)
├── nginx/                              # Aún no existe (Fase 12)
├── docker-compose.yml                  # dev stack (Task 0.2)
├── docker-compose.prod.yml             # Aún no existe (Fase 12)
├── docker-compose.ci.yml               # Aún no existe (Fase 10)
├── .env.example                        # Task 0.1
├── .env                                # Existe localmente (gitignored), no commitear
├── .gitignore, .editorconfig, README.md
└── .github/workflows/ci.yml            # Aún no existe (Task 0.6)
```

---

## 7. Cosas que NO hay que olvidar

### Antes de cada tarea
- `cat .git/sdd/progress.md` para confirmar qué está hecho.
- `git log --oneline -10` para mirar lo último.
- `git status` para asegurarte que el árbol esté limpio (no debería haber cambios sin commitear).
- `BASE=$(git rev-parse HEAD)` ANTES de despachar el implementer — el reviewer necesita el BASE pre-tarea para hacer `review-package BASE HEAD`. **Jamás uses `HEAD~1` como BASE** porque una tarea puede tener varios commits.

### Durante el dispatch
- Tirá al implementer **solo** el contexto de UNA tarea — no la historia de tareas previas.
- Pasale paths a archivos en lugar de pegar contenido en el prompt (los briefs y reports viven en `.git/sdd/`).
- No le digas al reviewer qué no flagear — dejá que encuentre lo que encuentre.

### Después del review
- Si hay Critical/Important: despachar UN fix subagente (no uno por finding).
- Si el fix toca tests, el fix-agent re-corre los tests cubrientes y los reporta. Después re-despachar reviewer.
- Si hay solo Minor: registrarlos en el ledger y pasar a la siguiente. Se triagéan en el review final.
- Si hay ⚠️ Cannot verify from diff: **vos** los resolvés (tenés el plan, el reviewer no).

### Conflictos plan vs. constraints
- Si un finding contradice texto literal del plan: presentárselo al usuario. No corrijas unilateralmente.

---

## 8. Recovery / troubleshooting

### Si la sesión se corta a la mitad de una tarea
1. `cat .git/sdd/progress.md` para ver hasta dónde llegó.
2. `git log --oneline -5` para ver si el último commit del implementer entró.
3. Si entró pero no figura en el ledger: chequear si hubo review aprobado. Si sí, agregar la línea al ledger. Si no, generar `review-package` y despachar reviewer.
4. Si NO entró: chequear `git status` por archivos sin commitear, decidir si re-despachar la tarea o levantar del estado parcial.

### Si Docker no está corriendo
```bash
cd /home/mva/medicia-laboral
docker compose up -d
sleep 10
docker compose ps   # esperar a "healthy" en postgres y minio
```

### Si `uv` no está en PATH
```bash
export PATH="$HOME/.local/bin:$PATH"
uv --version
```
Y agregarlo al `~/.bashrc` si querés persistencia.

### Si `pnpm` no está instalado (lo va a necesitar Task 0.5)
```bash
curl -fsSL https://get.pnpm.io/install.sh | sh -
source ~/.bashrc
pnpm --version
```

### Si los tests con testcontainers fallan
- Verificá que Docker daemon esté corriendo (`docker info`).
- Testcontainers levanta su propio postgres efímero, no usa el del compose. Si está lento, paciencia (primera vez puede tardar 30 s).

---

## 9. Atajos / cheatsheet

```bash
# Working directory siempre
cd /home/mva/medicia-laboral

# Skill base
SKILL=/root/.claude/plugins/cache/claude-plugins-official/superpowers/6.0.2/skills/subagent-driven-development
PLAN=docs/superpowers/plans/2026-06-18-medicia-laboral-implementation.md

# Ver estado
cat .git/sdd/progress.md
git log --oneline -10
git status

# Extraer brief de la tarea X.Y
"$SKILL/scripts/task-brief" "$PLAN" X.Y

# Generar paquete de review
"$SKILL/scripts/review-package" <base-sha> <head-sha>

# Anotar tarea completa en ledger
echo "Task X.Y: complete (commits <base7>..<head7>, review APPROVED)" >> .git/sdd/progress.md
```

---

## 10. Plan completo — secuencia de fases y tareas

Cada tarea está en el plan con todos los pasos detallados. Lista para tracking:

- **Fase 0 — Scaffolding**: 0.1 ✅, 0.2 ✅, 0.3 ✅, **0.4 ← acá**, 0.5, 0.6
- **Fase 1 — Backend core**: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 1.10
- **Fase 2 — Auth + usuarios**: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7
- **Fase 3 — Catálogos**: 3.1, 3.2, 3.3, 3.4, 3.5
- **Fase 4 — Empleados**: 4.1
- **Fase 5 — Adjuntos MinIO**: 5.1 (migración diferida a 6.1)
- **Fase 6 — Licencias**: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8
- **Fase 7 — Reportes**: 7.1
- **Fase 8 — Frontend foundation**: 8.1, 8.2, 8.3, 8.4
- **Fase 9 — Frontend features**: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6
- **Fase 10 — E2E Playwright**: 10.1, 10.2
- **Fase 11 — Portabilidad**: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6
- **Fase 12 — Producción**: 12.1, 12.2, 12.3, 12.4, 12.5
- **Final whole-branch review** + `superpowers:finishing-a-development-branch`

Cuando termines TODAS las tareas, despachá el final code reviewer con `opus` usando el template `../requesting-code-review/code-reviewer.md` del skill `superpowers:requesting-code-review`, y después invocá la skill `superpowers:finishing-a-development-branch` para cerrar.

---

## 11. Convenciones que el implementer DEBE respetar

Las tareas heredan estas reglas (están en el spec y en el plan, pero las repito acá para no perderlas):

- **TDD obligatorio** donde el brief lo indica (RED → GREEN → REFACTOR).
- **Módulo backend = `router.py` + `service.py` + `repository.py` + `models.py` + `schemas.py`** (capa fina en router, lógica en service, queries en repository).
- **Sin lógica de negocio en routers** — solo orquestación.
- **RBAC en routers** via `Depends(require_role(...))`, no en services.
- **Datos sensibles (diagnóstico, observaciones)** ocultos a rol `rrhh` en el `router` antes de serializar.
- **Auditoría es append-only a nivel DB** — al crear la tabla, agregar `REVOKE UPDATE, DELETE`.
- **Topes versionados:** cada edición crea nueva fila y cierra la anterior (`vigente_hasta = today - 1`). Nunca `UPDATE` in-place.
- **UUID v7** para entidades de dominio (ordenable por tiempo).
- **Conventional commits** (`feat:`, `fix:`, `docs:`, `chore:`, `test:`, `build:`, `ci:`).
- **Sin `git add -A`** en commits de tarea (el implementer puede traer cambios involuntarios del entorno).

---

## 12. Memoria persistente del usuario

El usuario tiene memoria de auto-memoria en `/root/.claude/projects/-home-mva/memory/`. Hay tres entradas relevantes ya escritas:

- `project_medicia_laboral.md` — descripción del proyecto.
- `feedback_medicia_laboral_portabilidad.md` — portabilidad es requisito de primer nivel.
- `MEMORY.md` — índice general.

No tenés que reescribirlas. Si encontrás algo nuevo digno de memoria (decisión técnica importante del usuario, preferencia inesperada), agregalo siguiendo el formato del directorio.

---

## Cierre

El plan está bien definido y los subagentes se manejan solos con los briefs. Tu trabajo es coordinar: extraer brief, registrar BASE, despachar implementer, generar review-package, despachar reviewer, anotar en ledger, repetir.

**Empezá por Task 0.4.** El BASE es `4d96d73`. El brief lo extraés con `scripts/task-brief docs/superpowers/plans/2026-06-18-medicia-laboral-implementation.md 0.4`.

Mucha suerte. 🛠️
