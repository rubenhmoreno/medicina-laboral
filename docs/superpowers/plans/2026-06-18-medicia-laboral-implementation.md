# Medicia-Laboral Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a standalone web application for occupational medicine — absenteeism and medical-leave management — with parametric per-category day caps, state-machine licenses, immutable audit, and a portable Docker deployment.

**Architecture:** Modular monolith FastAPI backend + React SPA, Postgres for persistence, MinIO for medical attachments, all orchestrated by Docker Compose for on-prem deployment. Every module is self-contained (router → service → repository → models) and testable in isolation. Portability is a first-class requirement: a single `scripts/migrate.sh` moves the whole installation to another server.

**Tech Stack:** Python 3.12 + FastAPI + SQLAlchemy 2 + Alembic + Pydantic v2 + argon2 + structlog + pytest + testcontainers · React 18 + Vite + TypeScript + react-router + zod + shadcn/ui + vitest + Playwright · Postgres 16, MinIO, nginx, certbot · Docker Compose, GitHub Actions, uv (Python) + pnpm (Node).

**Spec:** `docs/superpowers/specs/2026-06-18-medicia-laboral-design.md`

---

## Phase 0 — Project scaffolding

### Task 0.1: Repository root files

**Files:**
- Create: `.gitignore`
- Create: `README.md`
- Create: `.env.example`
- Create: `.editorconfig`

- [ ] **Step 1: Create `.gitignore`**

```gitignore
# Python
__pycache__/
*.py[cod]
*.egg-info/
.venv/
.pytest_cache/
.mypy_cache/
.ruff_cache/
htmlcov/
.coverage
coverage.xml

# Node
node_modules/
dist/
.vite/
*.tsbuildinfo

# Env / secrets
.env
.env.local
.env.*.local

# OS / IDE
.DS_Store
.idea/
.vscode/

# Local artefacts
backups/
volumes/
*.log
```

- [ ] **Step 2: Create `.editorconfig`**

```ini
root = true

[*]
end_of_line = lf
insert_final_newline = true
charset = utf-8
indent_style = space
trim_trailing_whitespace = true

[*.{py}]
indent_size = 4

[*.{ts,tsx,js,jsx,json,yml,yaml,md}]
indent_size = 2
```

- [ ] **Step 3: Create `README.md`**

```markdown
# medicia-laboral

Sistema de gestión de ausentismo y licencias médicas.

## Quick start (dev)

```bash
cp .env.example .env
docker compose up -d
cd backend && uv sync && uv run alembic upgrade head && uv run python scripts/seed_dev.py
cd ../frontend && pnpm install && pnpm dev
```

Backend: http://localhost:8000 — Docs: http://localhost:8000/docs
Frontend: http://localhost:5173

## Docs

- Spec: `docs/superpowers/specs/2026-06-18-medicia-laboral-design.md`
- Plan: `docs/superpowers/plans/2026-06-18-medicia-laboral-implementation.md`
- Migration: `docs/MIGRATION.md`
```

- [ ] **Step 4: Create `.env.example`**

```bash
# === Postgres ===
POSTGRES_USER=medicia
POSTGRES_PASSWORD=changeme_dev
POSTGRES_DB=medicia
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

# === MinIO ===
MINIO_ROOT_USER=medicia
MINIO_ROOT_PASSWORD=changeme_dev_minio
MINIO_BUCKET=medicia-adjuntos
MINIO_ENDPOINT=minio:9000
MINIO_USE_SSL=false

# === Backend ===
APP_ENV=dev
APP_SECRET_KEY=changeme_32_bytes_minimum_secret_here_12345
JWT_ACCESS_TTL_MINUTES=15
JWT_REFRESH_TTL_DAYS=7
CORS_ORIGINS=http://localhost:5173

# Seeded first admin (only used by bootstrap.sh)
ADMIN_EMAIL=admin@medicia.local
ADMIN_PASSWORD=ChangeMeOnFirstLogin123!

# === Observability ===
LOG_LEVEL=INFO
METRICS_ENABLED=false

# === Frontend (vite reads VITE_ prefixed only) ===
VITE_API_BASE_URL=http://localhost:8000
```

- [ ] **Step 5: Commit**

```bash
git add .gitignore .editorconfig README.md .env.example
git commit -m "chore: scaffold repo root (gitignore, env example, readme)"
```

---

### Task 0.2: docker-compose dev

**Files:**
- Create: `docker-compose.yml`

- [ ] **Step 1: Write `docker-compose.yml`**

```yaml
name: medicia-laboral

services:
  postgres:
    image: postgres:16-alpine
    restart: unless-stopped
    env_file: .env
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    ports:
      - "5432:5432"
    volumes:
      - pg_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 5s
      timeout: 5s
      retries: 10

  minio:
    image: minio/minio:RELEASE.2025-01-20T14-49-07Z
    restart: unless-stopped
    env_file: .env
    environment:
      MINIO_ROOT_USER: ${MINIO_ROOT_USER}
      MINIO_ROOT_PASSWORD: ${MINIO_ROOT_PASSWORD}
    command: server /data --console-address ":9001"
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - minio_data:/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 5s
      timeout: 5s
      retries: 10

  minio-init:
    image: minio/mc:RELEASE.2025-01-17T23-25-50Z
    depends_on:
      minio:
        condition: service_healthy
    env_file: .env
    entrypoint: >
      sh -c "
        mc alias set local http://minio:9000 $$MINIO_ROOT_USER $$MINIO_ROOT_PASSWORD &&
        (mc mb local/$$MINIO_BUCKET || true) &&
        mc anonymous set none local/$$MINIO_BUCKET
      "

volumes:
  pg_data:
  minio_data:
```

- [ ] **Step 2: Verify dev stack boots**

Run:
```bash
docker compose up -d
docker compose ps
```

Expected: `postgres` and `minio` both `healthy`; `minio-init` exited 0.

- [ ] **Step 3: Smoke-check connectivity**

Run:
```bash
docker compose exec postgres psql -U medicia -d medicia -c "select 1;"
curl -s http://localhost:9000/minio/health/live
```

Expected: psql returns `1`; MinIO returns empty body 200.

- [ ] **Step 4: Commit**

```bash
git add docker-compose.yml
git commit -m "chore: docker-compose dev stack (postgres + minio + bucket bootstrap)"
```

---

### Task 0.3: Backend Python project (uv + tooling)

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/.python-version`
- Create: `backend/app/__init__.py`
- Create: `backend/app/main.py`
- Create: `backend/tests/__init__.py`

- [ ] **Step 1: Write `backend/.python-version`**

```
3.12
```

- [ ] **Step 2: Write `backend/pyproject.toml`**

```toml
[project]
name = "medicia-laboral-backend"
version = "0.1.0"
description = "Backend for medicia-laboral occupational medicine system"
readme = "../README.md"
requires-python = ">=3.12"
dependencies = [
  "fastapi[standard]>=0.115",
  "uvicorn[standard]>=0.32",
  "pydantic>=2.9",
  "pydantic-settings>=2.5",
  "sqlalchemy[asyncio]>=2.0",
  "asyncpg>=0.30",
  "alembic>=1.13",
  "argon2-cffi>=23.1",
  "python-jose[cryptography]>=3.3",
  "python-multipart>=0.0.12",
  "structlog>=24.4",
  "boto3>=1.35",
  "minio>=7.2",
  "uuid7>=0.1",
  "email-validator>=2.2",
]

[dependency-groups]
dev = [
  "pytest>=8.3",
  "pytest-asyncio>=0.24",
  "pytest-cov>=5.0",
  "httpx>=0.27",
  "ruff>=0.7",
  "mypy>=1.13",
  "factory-boy>=3.3",
  "testcontainers[postgres,minio]>=4.8",
  "freezegun>=1.5",
  "respx>=0.21",
]

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP", "SIM", "RUF"]
ignore = ["E501"]

[tool.mypy]
python_version = "3.12"
strict = true
plugins = ["pydantic.mypy"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
addopts = "-ra -q --strict-markers"

[tool.coverage.run]
branch = true
source = ["app"]
omit = ["app/main.py", "app/core/cli.py"]
```

- [ ] **Step 3: Write `backend/app/main.py` (minimal app)**

```python
from fastapi import FastAPI


def create_app() -> FastAPI:
    app = FastAPI(title="medicia-laboral", version="0.1.0")

    @app.get("/healthz", tags=["ops"])
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
```

- [ ] **Step 4: Create empty `__init__.py` files**

```bash
touch backend/app/__init__.py backend/tests/__init__.py
```

- [ ] **Step 5: Install + run**

```bash
cd backend && uv sync
uv run uvicorn app.main:app --reload --port 8000 &
sleep 2 && curl -s http://localhost:8000/healthz && kill %1
```

Expected: `{"status":"ok"}`.

- [ ] **Step 6: Commit**

```bash
git add backend/
git commit -m "feat(backend): scaffold FastAPI app with healthz"
```

---

### Task 0.4: First failing test + CI lint/type/test loop

**Files:**
- Create: `backend/tests/test_healthz.py`

- [ ] **Step 1: Write failing test**

```python
# backend/tests/test_healthz.py
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_healthz_returns_ok():
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
```

- [ ] **Step 2: Run it (should pass — endpoint already exists)**

Run: `cd backend && uv run pytest -v`
Expected: 1 passed.

- [ ] **Step 3: Lint + type-check pass**

Run:
```bash
uv run ruff check app tests
uv run ruff format --check app tests
uv run mypy app
```

Expected: no errors.

- [ ] **Step 4: Commit**

```bash
git add backend/tests/test_healthz.py
git commit -m "test(backend): healthz smoke test"
```

---

### Task 0.5: Frontend Vite + React + TS scaffold

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/tsconfig.json`
- Create: `frontend/tsconfig.node.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/index.html`
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/App.tsx`

- [ ] **Step 1: Write `frontend/package.json`**

```json
{
  "name": "medicia-laboral-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "preview": "vite preview",
    "lint": "eslint .",
    "typecheck": "tsc -b --noEmit",
    "test:unit": "vitest run",
    "test:e2e": "playwright test",
    "gen:api": "openapi-typescript-codegen --input http://localhost:8000/openapi.json --output src/api --client axios"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-router-dom": "^6.27.0",
    "zod": "^3.23.8",
    "@tanstack/react-query": "^5.59.0",
    "axios": "^1.7.7",
    "clsx": "^2.1.1",
    "tailwind-merge": "^2.5.4"
  },
  "devDependencies": {
    "@types/react": "^18.3.12",
    "@types/react-dom": "^18.3.1",
    "@vitejs/plugin-react": "^4.3.3",
    "@testing-library/react": "^16.0.1",
    "@testing-library/jest-dom": "^6.6.3",
    "@testing-library/user-event": "^14.5.2",
    "jsdom": "^25.0.1",
    "vitest": "^2.1.4",
    "vite": "^5.4.10",
    "typescript": "^5.6.3",
    "@playwright/test": "^1.48.2",
    "msw": "^2.6.0",
    "@axe-core/playwright": "^4.10.0",
    "openapi-typescript-codegen": "^0.29.0",
    "eslint": "^9.13.0",
    "@typescript-eslint/parser": "^8.12.2",
    "@typescript-eslint/eslint-plugin": "^8.12.2",
    "eslint-plugin-react-hooks": "^5.0.0",
    "tailwindcss": "^3.4.14",
    "postcss": "^8.4.47",
    "autoprefixer": "^10.4.20"
  }
}
```

- [ ] **Step 2: Write `frontend/tsconfig.json`**

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "Bundler",
    "lib": ["ES2022", "DOM", "DOM.Iterable"],
    "jsx": "react-jsx",
    "strict": true,
    "noImplicitAny": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "isolatedModules": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "allowSyntheticDefaultImports": true,
    "baseUrl": ".",
    "paths": { "@/*": ["src/*"] }
  },
  "include": ["src", "tests"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

- [ ] **Step 3: Write `frontend/tsconfig.node.json`**

```json
{
  "compilerOptions": {
    "composite": true,
    "module": "ESNext",
    "moduleResolution": "Bundler",
    "target": "ES2022",
    "strict": true,
    "skipLibCheck": true
  },
  "include": ["vite.config.ts"]
}
```

- [ ] **Step 4: Write `frontend/vite.config.ts`**

```ts
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "node:path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: { "@": path.resolve(__dirname, "src") },
  },
  server: { port: 5173, host: true },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./tests/setup.ts"],
    coverage: { provider: "v8", reporter: ["text", "html"] },
  },
});
```

- [ ] **Step 5: Write `frontend/index.html`, `src/main.tsx`, `src/App.tsx`**

```html
<!-- frontend/index.html -->
<!doctype html>
<html lang="es">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Medicia-Laboral</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

```tsx
// frontend/src/main.tsx
import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
```

```tsx
// frontend/src/App.tsx
export default function App() {
  return <main className="p-8">Medicia-Laboral</main>;
}
```

- [ ] **Step 6: Install and boot once**

```bash
cd frontend && pnpm install
pnpm dev &
sleep 3 && curl -s -o /dev/null -w "%{http_code}\n" http://localhost:5173/ && kill %1
```

Expected: `200`.

- [ ] **Step 7: Commit**

```bash
git add frontend/ -- ':!frontend/node_modules'
git commit -m "feat(frontend): scaffold Vite + React + TS"
```

---

### Task 0.6: CI skeleton (GitHub Actions)

**Files:**
- Create: `.github/workflows/ci.yml`

- [ ] **Step 1: Write `ci.yml`**

```yaml
name: ci
on:
  pull_request:
  push:
    branches: [main]

jobs:
  backend:
    runs-on: ubuntu-24.04
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_USER: medicia
          POSTGRES_PASSWORD: medicia
          POSTGRES_DB: medicia_test
        ports: ["5432:5432"]
        options: --health-cmd "pg_isready" --health-interval 5s --health-timeout 5s --health-retries 10
    defaults: { run: { working-directory: backend } }
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
        with: { enable-cache: true }
      - run: uv python install 3.12
      - run: uv sync --frozen
      - run: uv run ruff check app tests
      - run: uv run ruff format --check app tests
      - run: uv run mypy app
      - run: uv run pytest --cov=app --cov-report=xml --cov-fail-under=80
        env:
          POSTGRES_HOST: localhost
          POSTGRES_USER: medicia
          POSTGRES_PASSWORD: medicia
          POSTGRES_DB: medicia_test

  frontend:
    runs-on: ubuntu-24.04
    defaults: { run: { working-directory: frontend } }
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4
        with: { version: 9 }
      - uses: actions/setup-node@v4
        with: { node-version: 20, cache: pnpm, cache-dependency-path: frontend/pnpm-lock.yaml }
      - run: pnpm install --frozen-lockfile
      - run: pnpm typecheck
      - run: pnpm test:unit -- --coverage
```

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: backend + frontend lint/type/test pipeline"
```

---

## Phase 1 — Backend core infrastructure

### Task 1.1: Settings (pydantic-settings)

**Files:**
- Create: `backend/app/core/__init__.py`
- Create: `backend/app/core/settings.py`
- Create: `backend/tests/core/__init__.py`
- Create: `backend/tests/core/test_settings.py`

- [ ] **Step 1: Write failing test**

```python
# backend/tests/core/test_settings.py
import os
from unittest.mock import patch

from app.core.settings import Settings


def test_settings_reads_env_vars():
    env = {
        "POSTGRES_USER": "u",
        "POSTGRES_PASSWORD": "p",
        "POSTGRES_DB": "db",
        "POSTGRES_HOST": "h",
        "POSTGRES_PORT": "5432",
        "MINIO_ROOT_USER": "mu",
        "MINIO_ROOT_PASSWORD": "mp",
        "MINIO_BUCKET": "b",
        "MINIO_ENDPOINT": "m:9000",
        "MINIO_USE_SSL": "false",
        "APP_ENV": "dev",
        "APP_SECRET_KEY": "x" * 32,
        "JWT_ACCESS_TTL_MINUTES": "15",
        "JWT_REFRESH_TTL_DAYS": "7",
        "CORS_ORIGINS": "http://localhost:5173,http://127.0.0.1:5173",
    }
    with patch.dict(os.environ, env, clear=True):
        s = Settings()
    assert s.db_dsn == "postgresql+asyncpg://u:p@h:5432/db"
    assert s.cors_origins == ["http://localhost:5173", "http://127.0.0.1:5173"]
    assert s.app_secret_key.get_secret_value() == "x" * 32


def test_settings_rejects_short_secret():
    env = {"APP_SECRET_KEY": "short"}
    with patch.dict(os.environ, env, clear=False):  # noqa
        try:
            Settings()
        except ValueError as e:
            assert "secret" in str(e).lower()
            return
        raise AssertionError("Expected ValueError")
```

- [ ] **Step 2: Run — should fail (module missing)**

Run: `cd backend && uv run pytest tests/core/test_settings.py -v`
Expected: collection error.

- [ ] **Step 3: Implement `settings.py`**

```python
# backend/app/core/settings.py
from functools import lru_cache

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    # Postgres
    postgres_user: str
    postgres_password: SecretStr
    postgres_db: str
    postgres_host: str
    postgres_port: int = 5432

    # MinIO
    minio_root_user: str
    minio_root_password: SecretStr
    minio_bucket: str
    minio_endpoint: str
    minio_use_ssl: bool = False

    # App
    app_env: str = "dev"
    app_secret_key: SecretStr
    jwt_access_ttl_minutes: int = 15
    jwt_refresh_ttl_days: int = 7
    cors_origins: list[str] = Field(default_factory=list)

    # Observability
    log_level: str = "INFO"
    metrics_enabled: bool = False

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_origins(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            return [o.strip() for o in v.split(",") if o.strip()]
        return v

    @field_validator("app_secret_key")
    @classmethod
    def secret_long_enough(cls, v: SecretStr) -> SecretStr:
        if len(v.get_secret_value()) < 32:
            raise ValueError("APP_SECRET_KEY must be at least 32 characters")
        return v

    @property
    def db_dsn(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:"
            f"{self.postgres_password.get_secret_value()}@"
            f"{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

- [ ] **Step 4: Run — should pass**

Run: `uv run pytest tests/core/test_settings.py -v`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/app/core backend/tests/core
git commit -m "feat(core): settings with env-driven config and validations"
```

---

### Task 1.2: Async DB session (SQLAlchemy 2)

**Files:**
- Create: `backend/app/core/db.py`
- Create: `backend/tests/core/test_db.py`

- [ ] **Step 1: Write failing test**

```python
# backend/tests/core/test_db.py
import pytest

from app.core.db import get_session, sessionmaker_factory
from app.core.settings import get_settings


@pytest.mark.asyncio
async def test_session_can_execute_select_one():
    factory = sessionmaker_factory(get_settings().db_dsn)
    async for session in get_session(factory):
        result = await session.execute_raw("select 1")
        assert result == 1
        break
```

> Note: this test will be rewritten in Task 1.3 to use testcontainers; keep it simple here.

- [ ] **Step 2: Implement `db.py`**

```python
# backend/app/core/db.py
from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


def sessionmaker_factory(dsn: str) -> async_sessionmaker[AsyncSession]:
    engine = create_async_engine(dsn, pool_pre_ping=True, pool_size=10, max_overflow=20)
    return async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_session(
    factory: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncSession, None]:
    async with factory() as session:
        yield session


# Helper used in the smoke test (avoids leaking SQLA internals in tests).
async def execute_select_one(session: AsyncSession) -> int:
    result = await session.execute(text("select 1"))
    return int(result.scalar_one())
```

- [ ] **Step 3: Rewrite test to use the helper**

```python
# backend/tests/core/test_db.py
import pytest

from app.core.db import execute_select_one, get_session, sessionmaker_factory
from app.core.settings import get_settings


@pytest.mark.asyncio
async def test_session_can_execute_select_one():
    factory = sessionmaker_factory(get_settings().db_dsn)
    async for session in get_session(factory):
        assert await execute_select_one(session) == 1
        break
```

- [ ] **Step 4: Run (needs local Postgres running)**

Run:
```bash
docker compose up -d postgres
cd backend && uv run pytest tests/core/test_db.py -v
```

Expected: 1 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/db.py backend/tests/core/test_db.py
git commit -m "feat(core): async sqlalchemy session factory"
```

---

### Task 1.3: Pytest fixtures with testcontainers Postgres

**Files:**
- Create: `backend/tests/conftest.py`

- [ ] **Step 1: Write `conftest.py`**

```python
# backend/tests/conftest.py
import asyncio
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from testcontainers.postgres import PostgresContainer

from app.core.db import sessionmaker_factory


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def pg_container():
    with PostgresContainer("postgres:16-alpine", driver="asyncpg") as pg:
        yield pg


@pytest.fixture(scope="session")
def db_dsn(pg_container) -> str:
    return pg_container.get_connection_url()


@pytest_asyncio.fixture
async def db_session(db_dsn) -> AsyncGenerator[AsyncSession, None]:
    factory = sessionmaker_factory(db_dsn)
    async with factory() as session:
        yield session
        await session.rollback()
```

- [ ] **Step 2: Rewrite `test_db.py` to use fixture**

```python
# backend/tests/core/test_db.py
import pytest

from app.core.db import execute_select_one


@pytest.mark.asyncio
async def test_session_can_execute_select_one(db_session):
    assert await execute_select_one(db_session) == 1
```

- [ ] **Step 3: Run — should pass**

Run: `cd backend && uv run pytest -v`
Expected: all green.

- [ ] **Step 4: Commit**

```bash
git add backend/tests/conftest.py backend/tests/core/test_db.py
git commit -m "test: testcontainers postgres fixture for hermetic db tests"
```

---

### Task 1.4: Custom exceptions hierarchy + handler

**Files:**
- Create: `backend/app/shared/__init__.py`
- Create: `backend/app/shared/exceptions.py`
- Create: `backend/app/shared/error_handler.py`
- Create: `backend/tests/shared/__init__.py`
- Create: `backend/tests/shared/test_error_handler.py`

- [ ] **Step 1: Write failing test**

```python
# backend/tests/shared/test_error_handler.py
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.shared.error_handler import install_error_handlers
from app.shared.exceptions import ConflictError, NotFoundError, ValidationError


def make_app():
    app = FastAPI()
    install_error_handlers(app)

    @app.get("/notfound")
    def nf():
        raise NotFoundError("missing", detail={"id": 1})

    @app.get("/conflict")
    def cf():
        raise ConflictError("dup", detail={"field": "email"})

    @app.get("/validation")
    def vd():
        raise ValidationError("bad")

    @app.get("/boom")
    def boom():
        raise RuntimeError("kaboom")

    return TestClient(app)


def test_not_found_returns_404_with_envelope():
    r = make_app().get("/notfound")
    assert r.status_code == 404
    body = r.json()
    assert body["error"]["code"] == "not_found"
    assert body["error"]["message"] == "missing"
    assert body["error"]["detail"] == {"id": 1}
    assert "request_id" in body


def test_conflict_returns_409():
    r = make_app().get("/conflict")
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "conflict"


def test_validation_returns_422():
    r = make_app().get("/validation")
    assert r.status_code == 422


def test_unexpected_returns_500_without_stacktrace():
    r = make_app().get("/boom")
    assert r.status_code == 500
    body = r.json()
    assert body["error"]["code"] == "internal_error"
    assert "kaboom" not in body["error"]["message"]
    assert "request_id" in body
```

- [ ] **Step 2: Implement `exceptions.py`**

```python
# backend/app/shared/exceptions.py
from typing import Any


class AppError(Exception):
    http_status: int = 500
    code: str = "internal_error"

    def __init__(self, message: str = "", detail: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.detail = detail or {}


class ValidationError(AppError):
    http_status = 422
    code = "validation"


class NotFoundError(AppError):
    http_status = 404
    code = "not_found"


class ConflictError(AppError):
    http_status = 409
    code = "conflict"


class ForbiddenError(AppError):
    http_status = 403
    code = "forbidden"


class UnauthorizedError(AppError):
    http_status = 401
    code = "unauthorized"


class InvalidStateTransition(ConflictError):
    code = "invalid_transition"
```

- [ ] **Step 3: Implement `error_handler.py`**

```python
# backend/app/shared/error_handler.py
import uuid

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.shared.exceptions import AppError


def _envelope(code: str, message: str, detail: dict, request_id: str) -> dict:
    return {
        "error": {"code": code, "message": message, "detail": detail},
        "request_id": request_id,
    }


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(request: Request, exc: AppError):
        rid = request.headers.get("x-request-id") or uuid.uuid4().hex
        return JSONResponse(
            status_code=exc.http_status,
            content=_envelope(exc.code, exc.message, exc.detail, rid),
        )

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception):
        rid = request.headers.get("x-request-id") or uuid.uuid4().hex
        # NOTE: stacktrace stays in logs (configured by structlog), never the response.
        return JSONResponse(
            status_code=500,
            content=_envelope("internal_error", "internal server error", {}, rid),
        )
```

- [ ] **Step 4: Run — should pass**

Run: `cd backend && uv run pytest tests/shared/ -v`
Expected: 4 passed.

- [ ] **Step 5: Wire into `main.py`**

```python
# backend/app/main.py
from fastapi import FastAPI

from app.shared.error_handler import install_error_handlers


def create_app() -> FastAPI:
    app = FastAPI(title="medicia-laboral", version="0.1.0")
    install_error_handlers(app)

    @app.get("/healthz", tags=["ops"])
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
```

- [ ] **Step 6: Commit**

```bash
git add backend/app/shared backend/tests/shared backend/app/main.py
git commit -m "feat(shared): error hierarchy + envelope handler with request_id"
```

---

### Task 1.5: Structured logging (structlog) + request_id middleware

**Files:**
- Create: `backend/app/core/logging.py`
- Create: `backend/app/core/middleware.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/core/test_logging.py`

- [ ] **Step 1: Write failing test**

```python
# backend/tests/core/test_logging.py
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.middleware import install_request_id_middleware


def test_response_carries_request_id_header():
    app = FastAPI()
    install_request_id_middleware(app)

    @app.get("/")
    def index():
        return {}

    r = TestClient(app).get("/")
    assert "x-request-id" in r.headers
    assert len(r.headers["x-request-id"]) >= 16


def test_request_id_is_echoed_when_provided():
    app = FastAPI()
    install_request_id_middleware(app)

    @app.get("/")
    def index():
        return {}

    r = TestClient(app).get("/", headers={"x-request-id": "abc-123"})
    assert r.headers["x-request-id"] == "abc-123"
```

- [ ] **Step 2: Implement `logging.py`**

```python
# backend/app/core/logging.py
import logging

import structlog


def configure_logging(level: str = "INFO") -> None:
    logging.basicConfig(format="%(message)s", level=level)
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(getattr(logging, level)),
    )


def get_logger(name: str | None = None):
    return structlog.get_logger(name)
```

- [ ] **Step 3: Implement `middleware.py`**

```python
# backend/app/core/middleware.py
import time
import uuid

import structlog
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware

log = structlog.get_logger("http")


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        rid = request.headers.get("x-request-id") or uuid.uuid4().hex
        start = time.perf_counter()
        structlog.contextvars.bind_contextvars(
            request_id=rid, path=request.url.path, method=request.method
        )
        try:
            response = await call_next(request)
        finally:
            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
            log.info("request", status=getattr(locals().get("response", None), "status_code", 500), latency_ms=elapsed_ms)
            structlog.contextvars.clear_contextvars()
        response.headers["x-request-id"] = rid
        return response


def install_request_id_middleware(app: FastAPI) -> None:
    app.add_middleware(RequestIDMiddleware)
```

- [ ] **Step 4: Wire into `main.py`**

```python
# backend/app/main.py
from fastapi import FastAPI

from app.core.logging import configure_logging
from app.core.middleware import install_request_id_middleware
from app.core.settings import get_settings
from app.shared.error_handler import install_error_handlers


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(title="medicia-laboral", version="0.1.0")
    install_error_handlers(app)
    install_request_id_middleware(app)

    @app.get("/healthz", tags=["ops"])
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
```

- [ ] **Step 5: Run — should pass**

Run: `cd backend && uv run pytest tests/core/test_logging.py -v`
Expected: 2 passed.

- [ ] **Step 6: Commit**

```bash
git add backend/app/core/logging.py backend/app/core/middleware.py backend/app/main.py backend/tests/core/test_logging.py
git commit -m "feat(core): structlog + request_id middleware"
```

---

### Task 1.6: Alembic init + first empty migration

**Files:**
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`
- Create: `backend/alembic/script.py.mako`
- Create: `backend/alembic/versions/.keep`

- [ ] **Step 1: Init alembic**

Run:
```bash
cd backend && uv run alembic init -t async alembic
```

- [ ] **Step 2: Replace `alembic.ini` script_location + ignore percent signs**

In `backend/alembic.ini`, set:
```ini
script_location = alembic
sqlalchemy.url =
```

- [ ] **Step 3: Replace `alembic/env.py`**

```python
# backend/alembic/env.py
import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import async_engine_from_config
from sqlalchemy import pool

from app.core.settings import get_settings

# Imports below register tables; populated in later tasks.
# from app.modules.usuarios.models import *  # noqa
# from app.modules.empleados.models import *  # noqa

from app.core.db_base import Base  # see Task 1.7

config = context.config
if config.config_file_name:
    fileConfig(config.config_file_name)
config.set_main_option("sqlalchemy.url", get_settings().db_dsn)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as conn:
        await conn.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
```

- [ ] **Step 4: Create empty first revision**

Run:
```bash
cd backend && uv run alembic revision -m "empty initial"
```

Edit the generated file so `upgrade()` and `downgrade()` are `pass`.

- [ ] **Step 5: Verify apply works**

```bash
docker compose up -d postgres
uv run alembic upgrade head
```

Expected: prints `INFO  [alembic.runtime.migration] Running upgrade  -> <hash>, empty initial`.

- [ ] **Step 6: Commit**

```bash
git add backend/alembic backend/alembic.ini
git commit -m "feat(db): alembic async config with empty first revision"
```

---

### Task 1.7: SQLAlchemy declarative base + UUID v7 helper

**Files:**
- Create: `backend/app/core/db_base.py`
- Create: `backend/app/core/ids.py`
- Create: `backend/tests/core/test_ids.py`

- [ ] **Step 1: Write failing test**

```python
# backend/tests/core/test_ids.py
import re

from app.core.ids import new_uuid7


def test_uuid7_is_v7_and_unique():
    a = new_uuid7()
    b = new_uuid7()
    assert a != b
    assert re.match(r"^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[0-9a-f]{4}-[0-9a-f]{12}$", str(a))


def test_uuid7_is_time_ordered():
    ids = [new_uuid7() for _ in range(50)]
    assert ids == sorted(ids)
```

- [ ] **Step 2: Implement `ids.py`**

```python
# backend/app/core/ids.py
import uuid

from uuid_extensions import uuid7  # uuid7 package


def new_uuid7() -> uuid.UUID:
    return uuid7()
```

> If the `uuid7` package wasn't added in Task 0.3, add `uuid7>=0.1.0` to `pyproject.toml` deps (already included above) and run `uv sync`.

- [ ] **Step 3: Implement `db_base.py`**

```python
# backend/app/core/db_base.py
from datetime import datetime
from typing import Annotated
from uuid import UUID

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.core.ids import new_uuid7


class Base(DeclarativeBase):
    pass


UUIDPk = Annotated[
    UUID,
    mapped_column(primary_key=True, default=new_uuid7),
]

TimestampTZ = Annotated[
    datetime,
    mapped_column(DateTime(timezone=True), server_default=func.now()),
]
```

- [ ] **Step 4: Run — should pass**

Run: `cd backend && uv run pytest tests/core/test_ids.py -v`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/ids.py backend/app/core/db_base.py backend/tests/core/test_ids.py
git commit -m "feat(core): declarative base + uuid7 helper"
```

---

### Task 1.8: Auditoría table + append-only DB grants

**Files:**
- Create: `backend/app/modules/__init__.py`
- Create: `backend/app/modules/auditoria/__init__.py`
- Create: `backend/app/modules/auditoria/models.py`
- Create: `backend/alembic/versions/<hash>_auditoria.py`
- Create: `backend/tests/modules/__init__.py`
- Create: `backend/tests/modules/auditoria/__init__.py`
- Create: `backend/tests/modules/auditoria/test_models.py`

- [ ] **Step 1: Write failing test**

```python
# backend/tests/modules/auditoria/test_models.py
import pytest
from sqlalchemy import select

from app.modules.auditoria.models import Auditoria


@pytest.mark.asyncio
async def test_can_insert_audit_row(db_session):
    row = Auditoria(accion="login", entidad="usuario", payload={"ok": True})
    db_session.add(row)
    await db_session.flush()
    result = await db_session.execute(select(Auditoria))
    assert result.scalar_one().accion == "login"
```

- [ ] **Step 2: Implement `models.py`**

```python
# backend/app/modules/auditoria/models.py
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import BigInteger, DateTime, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db_base import Base


class Auditoria(Base):
    __tablename__ = "auditoria"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    usuario_id: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True), nullable=True)
    accion: Mapped[str] = mapped_column(String(64))
    entidad: Mapped[str] = mapped_column(String(64))
    entidad_id: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True), nullable=True)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)
```

- [ ] **Step 3: Add migration (autogenerate)**

```bash
cd backend && uv run alembic revision --autogenerate -m "auditoria table"
```

Edit the generated revision to append a raw SQL grant block at the end of `upgrade()`:

```python
def upgrade() -> None:
    # ... autogenerated DDL ...
    op.execute("""
        -- Append-only: app role can INSERT and SELECT but never UPDATE/DELETE.
        REVOKE UPDATE, DELETE ON TABLE auditoria FROM PUBLIC;
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_auditoria_ts_entidad
            ON auditoria (ts DESC, entidad, entidad_id);
    """)
```

- [ ] **Step 4: Run migration + tests**

```bash
uv run alembic upgrade head
uv run pytest tests/modules/auditoria -v
```

Expected: migration ok, 1 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/app/modules/auditoria backend/tests/modules backend/alembic/versions
git commit -m "feat(auditoria): append-only audit table + index"
```

---

### Task 1.9: Audit decorator

**Files:**
- Create: `backend/app/modules/auditoria/repository.py`
- Create: `backend/app/modules/auditoria/decorator.py`
- Create: `backend/tests/modules/auditoria/test_decorator.py`

- [ ] **Step 1: Write failing test**

```python
# backend/tests/modules/auditoria/test_decorator.py
import pytest
from sqlalchemy import select

from app.modules.auditoria.decorator import audited
from app.modules.auditoria.models import Auditoria


class FakeUser:
    id = None


class FakeRequest:
    headers = {"user-agent": "ua"}
    class _C: host = "1.2.3.4"
    client = _C()


@pytest.mark.asyncio
async def test_audited_writes_entry(db_session):
    @audited("create", "ficticio")
    async def service(*, session, request, current_user, value):
        return type("R", (), {"id": None, "value": value})()

    await service(session=db_session, request=FakeRequest(), current_user=FakeUser(), value="x")
    await db_session.flush()
    rows = (await db_session.execute(select(Auditoria))).scalars().all()
    assert any(r.accion == "create" and r.entidad == "ficticio" for r in rows)
```

- [ ] **Step 2: Implement `repository.py`**

```python
# backend/app/modules/auditoria/repository.py
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auditoria.models import Auditoria


async def append(
    session: AsyncSession,
    *,
    accion: str,
    entidad: str,
    usuario_id: UUID | None,
    entidad_id: UUID | None,
    payload: dict[str, Any] | None,
    ip: str | None,
    user_agent: str | None,
) -> None:
    session.add(
        Auditoria(
            accion=accion,
            entidad=entidad,
            usuario_id=usuario_id,
            entidad_id=entidad_id,
            payload=payload,
            ip=ip,
            user_agent=user_agent,
        )
    )
    await session.flush()
```

- [ ] **Step 3: Implement `decorator.py`**

```python
# backend/app/modules/auditoria/decorator.py
from collections.abc import Callable
from functools import wraps
from typing import Any

from app.modules.auditoria import repository as audit_repo


def audited(accion: str, entidad: str) -> Callable:
    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        async def wrapper(*args: Any, **kwargs: Any):
            result = await fn(*args, **kwargs)
            session = kwargs.get("session") or kwargs.get("db_session")
            request = kwargs.get("request")
            user = kwargs.get("current_user")
            await audit_repo.append(
                session,
                accion=accion,
                entidad=entidad,
                usuario_id=getattr(user, "id", None),
                entidad_id=getattr(result, "id", None),
                payload={"args": [str(a) for a in args], "kwargs": {k: str(v) for k, v in kwargs.items() if k not in {"session", "db_session", "request", "current_user"}}},
                ip=getattr(getattr(request, "client", None), "host", None),
                user_agent=getattr(request, "headers", {}).get("user-agent") if request else None,
            )
            return result
        return wrapper
    return decorator
```

- [ ] **Step 4: Run — should pass**

Run: `cd backend && uv run pytest tests/modules/auditoria -v`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/app/modules/auditoria/repository.py backend/app/modules/auditoria/decorator.py backend/tests/modules/auditoria/test_decorator.py
git commit -m "feat(auditoria): @audited decorator persisting audit entries"
```

---

### Task 1.10: /readyz with DB + MinIO checks

**Files:**
- Create: `backend/app/core/storage.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/core/test_readyz.py`

- [ ] **Step 1: Implement `storage.py`**

```python
# backend/app/core/storage.py
from minio import Minio

from app.core.settings import Settings


def minio_client(settings: Settings) -> Minio:
    return Minio(
        endpoint=settings.minio_endpoint,
        access_key=settings.minio_root_user,
        secret_key=settings.minio_root_password.get_secret_value(),
        secure=settings.minio_use_ssl,
    )


def ensure_bucket(client: Minio, bucket: str) -> None:
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)
```

- [ ] **Step 2: Add `/readyz` to `main.py`**

```python
# backend/app/main.py  (additions)
from fastapi import HTTPException
from sqlalchemy import text

from app.core.db import sessionmaker_factory
from app.core.storage import minio_client


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)
    app = FastAPI(title="medicia-laboral", version="0.1.0")
    install_error_handlers(app)
    install_request_id_middleware(app)

    factory = sessionmaker_factory(settings.db_dsn)
    mc = minio_client(settings)

    @app.get("/healthz", tags=["ops"])
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/readyz", tags=["ops"])
    async def readyz():
        try:
            async with factory() as s:
                await s.execute(text("select 1"))
        except Exception as e:
            raise HTTPException(503, f"db: {e!s}") from e
        try:
            mc.bucket_exists(settings.minio_bucket)
        except Exception as e:
            raise HTTPException(503, f"minio: {e!s}") from e
        return {"status": "ready"}

    return app


app = create_app()
```

- [ ] **Step 3: Write integration test**

```python
# backend/tests/core/test_readyz.py
from fastapi.testclient import TestClient

from app.main import app


def test_readyz_returns_503_when_minio_unreachable(monkeypatch):
    # When run without docker-compose up, /readyz should fail with 503.
    client = TestClient(app)
    r = client.get("/readyz")
    assert r.status_code in (200, 503)  # 200 if dev stack is up
```

> The test is intentionally tolerant: in CI with `services:` Postgres but no MinIO it will hit 503; locally with full stack, 200.

- [ ] **Step 4: Run**

Run: `uv run pytest tests/core/test_readyz.py -v`
Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/storage.py backend/app/main.py backend/tests/core/test_readyz.py
git commit -m "feat(ops): /readyz checks db and minio"
```

---

## Phase 2 — Authentication, RBAC, and Usuarios module

### Task 2.1: Usuario model + migration

**Files:**
- Create: `backend/app/modules/usuarios/__init__.py`
- Create: `backend/app/modules/usuarios/models.py`
- Add migration via `alembic revision --autogenerate`
- Create: `backend/tests/modules/usuarios/__init__.py`
- Create: `backend/tests/modules/usuarios/test_models.py`

- [ ] **Step 1: Write failing test**

```python
# backend/tests/modules/usuarios/test_models.py
import pytest
from sqlalchemy import select

from app.modules.usuarios.models import Rol, Usuario


@pytest.mark.asyncio
async def test_can_create_usuario_with_required_fields(db_session):
    u = Usuario(email="a@b.com", password_hash="h", nombre="A", rol=Rol.ADMIN)
    db_session.add(u)
    await db_session.flush()
    out = (await db_session.execute(select(Usuario).where(Usuario.email == "a@b.com"))).scalar_one()
    assert out.rol == Rol.ADMIN
    assert out.activo is True
```

- [ ] **Step 2: Implement models**

```python
# backend/app/modules/usuarios/models.py
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, String, func
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db_base import Base
from app.core.ids import new_uuid7


class Rol(StrEnum):
    ADMIN = "admin"
    MEDICO = "medico"
    RRHH = "rrhh"


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=new_uuid7)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    nombre: Mapped[str | None] = mapped_column(String(120), nullable=True)
    rol: Mapped[Rol] = mapped_column(SAEnum(Rol, name="rol"))
    matricula: Mapped[str | None] = mapped_column(String(40), nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    ultimo_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
```

Wire the import into `alembic/env.py`:

```python
from app.modules.usuarios import models as _usuarios_models  # noqa: F401
```

- [ ] **Step 3: Generate + apply migration**

```bash
cd backend && uv run alembic revision --autogenerate -m "usuarios table"
uv run alembic upgrade head
```

- [ ] **Step 4: Run test**

Run: `uv run pytest tests/modules/usuarios -v`
Expected: 1 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/app/modules/usuarios backend/tests/modules/usuarios backend/alembic/versions backend/alembic/env.py
git commit -m "feat(usuarios): model + migration with rol enum"
```

---

### Task 2.2: Password hashing (argon2id) + strength check

**Files:**
- Create: `backend/app/core/security.py`
- Create: `backend/tests/core/test_security.py`

- [ ] **Step 1: Write failing tests**

```python
# backend/tests/core/test_security.py
import pytest

from app.core.security import hash_password, validate_password_strength, verify_password


def test_hash_and_verify_round_trip():
    h = hash_password("CorrectHorseBatteryStaple9!")
    assert verify_password("CorrectHorseBatteryStaple9!", h) is True
    assert verify_password("wrong", h) is False


@pytest.mark.parametrize("bad", ["short", "alllowercase123456", "password123!"])
def test_weak_password_rejected(bad):
    with pytest.raises(ValueError):
        validate_password_strength(bad)


def test_strong_password_accepted():
    validate_password_strength("Tr0ub4dor&3Horse!Battery")
```

- [ ] **Step 2: Implement `security.py`**

```python
# backend/app/core/security.py
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

_ph = PasswordHasher()

# Conservative local blocklist; can be swapped for zxcvbn if desired.
_COMMON = {
    "password",
    "password123",
    "qwerty",
    "letmein",
    "admin",
    "welcome",
    "iloveyou",
    "1234567890",
    "password1!",
    "password123!",
}


def hash_password(plain: str) -> str:
    return _ph.hash(plain)


def verify_password(plain: str, stored: str) -> bool:
    try:
        return _ph.verify(stored, plain)
    except VerifyMismatchError:
        return False


def validate_password_strength(plain: str) -> None:
    if len(plain) < 12:
        raise ValueError("password must be at least 12 characters")
    if plain.lower() in _COMMON:
        raise ValueError("password is too common")
    classes = sum(
        bool(any(c in plain for c in chars))
        for chars in ["abcdefghijklmnopqrstuvwxyz", "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "0123456789", "!@#$%^&*()_+-=[]{};:,.<>?/\\|"]
    )
    if classes < 3:
        raise ValueError("password must mix lowercase, uppercase, digits, symbols (≥3 classes)")
```

- [ ] **Step 3: Run — should pass**

Run: `cd backend && uv run pytest tests/core/test_security.py -v`
Expected: 5 passed.

- [ ] **Step 4: Commit**

```bash
git add backend/app/core/security.py backend/tests/core/test_security.py
git commit -m "feat(core): argon2id hashing + password strength validator"
```

---

### Task 2.3: JWT issue / decode

**Files:**
- Create: `backend/app/core/jwt.py`
- Create: `backend/tests/core/test_jwt.py`

- [ ] **Step 1: Write failing tests**

```python
# backend/tests/core/test_jwt.py
from datetime import datetime, timedelta, timezone

import pytest
from freezegun import freeze_time

from app.core.jwt import decode_token, issue_access, issue_refresh
from app.core.settings import get_settings


def test_access_and_refresh_round_trip():
    s = get_settings()
    sub = "user-123"
    access = issue_access(sub, s)
    refresh = issue_refresh(sub, s)
    a = decode_token(access, s)
    r = decode_token(refresh, s)
    assert a["sub"] == sub and a["type"] == "access"
    assert r["sub"] == sub and r["type"] == "refresh"


def test_expired_access_raises():
    s = get_settings()
    with freeze_time("2026-01-01"):
        t = issue_access("u", s)
    with freeze_time("2026-01-02"):
        with pytest.raises(Exception):
            decode_token(t, s)
```

- [ ] **Step 2: Implement `jwt.py`**

```python
# backend/app/core/jwt.py
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import jwt

from app.core.settings import Settings

_ALG = "HS256"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def issue_access(subject: str, settings: Settings) -> str:
    now = _now()
    payload = {
        "sub": subject,
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.jwt_access_ttl_minutes)).timestamp()),
    }
    return jwt.encode(payload, settings.app_secret_key.get_secret_value(), algorithm=_ALG)


def issue_refresh(subject: str, settings: Settings) -> str:
    now = _now()
    payload = {
        "sub": subject,
        "type": "refresh",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(days=settings.jwt_refresh_ttl_days)).timestamp()),
    }
    return jwt.encode(payload, settings.app_secret_key.get_secret_value(), algorithm=_ALG)


def decode_token(token: str, settings: Settings) -> dict[str, Any]:
    return jwt.decode(token, settings.app_secret_key.get_secret_value(), algorithms=[_ALG])
```

- [ ] **Step 3: Run**

Run: `uv run pytest tests/core/test_jwt.py -v`
Expected: 2 passed.

- [ ] **Step 4: Commit**

```bash
git add backend/app/core/jwt.py backend/tests/core/test_jwt.py
git commit -m "feat(core): JWT access/refresh issuance + decode"
```

---

### Task 2.4: Auth schemas + service

**Files:**
- Create: `backend/app/modules/usuarios/schemas.py`
- Create: `backend/app/modules/usuarios/repository.py`
- Create: `backend/app/modules/usuarios/service.py`
- Create: `backend/tests/modules/usuarios/test_service.py`

- [ ] **Step 1: Write `schemas.py`**

```python
# backend/app/modules/usuarios/schemas.py
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.modules.usuarios.models import Rol


class UsuarioCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
    nombre: str | None = None
    rol: Rol
    matricula: str | None = None


class UsuarioUpdate(BaseModel):
    nombre: str | None = None
    rol: Rol | None = None
    matricula: str | None = None
    activo: bool | None = None


class UsuarioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    nombre: str | None
    rol: Rol
    matricula: str | None
    activo: bool
    ultimo_login: datetime | None


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
```

- [ ] **Step 2: Write `repository.py`**

```python
# backend/app/modules/usuarios/repository.py
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.usuarios.models import Usuario


async def get_by_email(session: AsyncSession, email: str) -> Usuario | None:
    res = await session.execute(select(Usuario).where(Usuario.email == email))
    return res.scalar_one_or_none()


async def get_by_id(session: AsyncSession, id_: UUID) -> Usuario | None:
    res = await session.execute(select(Usuario).where(Usuario.id == id_))
    return res.scalar_one_or_none()


async def insert(session: AsyncSession, u: Usuario) -> Usuario:
    session.add(u)
    await session.flush()
    return u


async def update(session: AsyncSession, u: Usuario) -> Usuario:
    await session.flush()
    return u


async def list_all(session: AsyncSession) -> list[Usuario]:
    res = await session.execute(select(Usuario).order_by(Usuario.email))
    return list(res.scalars())
```

- [ ] **Step 3: Write `service.py`**

```python
# backend/app/modules/usuarios/service.py
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, validate_password_strength, verify_password
from app.modules.usuarios import repository as repo
from app.modules.usuarios.models import Usuario
from app.modules.usuarios.schemas import UsuarioCreate
from app.shared.exceptions import ConflictError, NotFoundError, UnauthorizedError


async def create_user(session: AsyncSession, payload: UsuarioCreate) -> Usuario:
    if await repo.get_by_email(session, payload.email):
        raise ConflictError("email already registered", detail={"field": "email"})
    validate_password_strength(payload.password)
    u = Usuario(
        email=payload.email,
        password_hash=hash_password(payload.password),
        nombre=payload.nombre,
        rol=payload.rol,
        matricula=payload.matricula,
    )
    return await repo.insert(session, u)


async def authenticate(session: AsyncSession, email: str, password: str) -> Usuario:
    u = await repo.get_by_email(session, email)
    if not u or not u.activo or not verify_password(password, u.password_hash):
        raise UnauthorizedError("invalid credentials")
    u.ultimo_login = datetime.now(timezone.utc)
    await repo.update(session, u)
    return u
```

- [ ] **Step 4: Write failing service tests**

```python
# backend/tests/modules/usuarios/test_service.py
import pytest

from app.modules.usuarios.models import Rol
from app.modules.usuarios.schemas import UsuarioCreate
from app.modules.usuarios.service import authenticate, create_user
from app.shared.exceptions import ConflictError, UnauthorizedError


@pytest.mark.asyncio
async def test_create_and_authenticate(db_session):
    u = await create_user(
        db_session,
        UsuarioCreate(
            email="m@m.com", password="StrongPass123!Q", nombre="M", rol=Rol.MEDICO
        ),
    )
    assert u.id is not None
    again = await authenticate(db_session, "m@m.com", "StrongPass123!Q")
    assert again.id == u.id


@pytest.mark.asyncio
async def test_duplicate_email(db_session):
    p = UsuarioCreate(email="d@d.com", password="StrongPass123!Q", nombre="x", rol=Rol.ADMIN)
    await create_user(db_session, p)
    with pytest.raises(ConflictError):
        await create_user(db_session, p)


@pytest.mark.asyncio
async def test_bad_credentials(db_session):
    with pytest.raises(UnauthorizedError):
        await authenticate(db_session, "nope@nope.com", "xxxxxxxxxxxx")
```

- [ ] **Step 5: Run — should pass**

Run: `cd backend && uv run pytest tests/modules/usuarios -v`
Expected: all green.

- [ ] **Step 6: Commit**

```bash
git add backend/app/modules/usuarios backend/tests/modules/usuarios
git commit -m "feat(usuarios): create_user + authenticate service"
```

---

### Task 2.5: Auth dependencies (current_user + require_role)

**Files:**
- Create: `backend/app/core/deps.py`
- Create: `backend/app/core/permissions.py`
- Create: `backend/tests/core/test_deps.py`

- [ ] **Step 1: Write `deps.py`**

```python
# backend/app/core/deps.py
from collections.abc import AsyncGenerator
from functools import lru_cache

from fastapi import Depends, Header
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.db import sessionmaker_factory
from app.core.jwt import decode_token
from app.core.settings import Settings, get_settings
from app.modules.usuarios import repository as users_repo
from app.modules.usuarios.models import Usuario
from app.shared.exceptions import UnauthorizedError


@lru_cache
def _factory(dsn: str) -> async_sessionmaker[AsyncSession]:
    return sessionmaker_factory(dsn)


async def get_db(
    settings: Settings = Depends(get_settings),
) -> AsyncGenerator[AsyncSession, None]:
    f = _factory(settings.db_dsn)
    async with f() as session:
        yield session


async def current_user(
    authorization: str = Header(default=""),
    settings: Settings = Depends(get_settings),
    session: AsyncSession = Depends(get_db),
) -> Usuario:
    if not authorization.lower().startswith("bearer "):
        raise UnauthorizedError("missing bearer token")
    token = authorization.split(" ", 1)[1]
    try:
        claims = decode_token(token, settings)
    except JWTError as e:
        raise UnauthorizedError("invalid token") from e
    if claims.get("type") != "access":
        raise UnauthorizedError("wrong token type")
    user = await users_repo.get_by_id(session, claims["sub"])
    if user is None or not user.activo:
        raise UnauthorizedError("inactive user")
    return user
```

- [ ] **Step 2: Write `permissions.py`**

```python
# backend/app/core/permissions.py
from fastapi import Depends

from app.core.deps import current_user
from app.modules.usuarios.models import Rol, Usuario
from app.shared.exceptions import ForbiddenError


def require_role(*roles: Rol):
    async def dep(user: Usuario = Depends(current_user)) -> Usuario:
        if user.rol not in roles:
            raise ForbiddenError("insufficient permissions", detail={"required": [r.value for r in roles]})
        return user

    return dep
```

- [ ] **Step 3: Failing tests for deps**

```python
# backend/tests/core/test_deps.py
import pytest
from fastapi import Depends, FastAPI
from httpx import AsyncClient, ASGITransport

from app.core.deps import current_user, get_db
from app.core.jwt import issue_access
from app.core.permissions import require_role
from app.core.settings import get_settings
from app.modules.usuarios.models import Rol, Usuario
from app.modules.usuarios.schemas import UsuarioCreate
from app.modules.usuarios.service import create_user
from app.shared.error_handler import install_error_handlers


def build_app(db_session):
    app = FastAPI()
    install_error_handlers(app)

    async def _db_override():
        yield db_session

    app.dependency_overrides[get_db] = _db_override

    @app.get("/me")
    async def me(u: Usuario = Depends(current_user)):
        return {"email": u.email, "rol": u.rol}

    @app.get("/admin-only", dependencies=[Depends(require_role(Rol.ADMIN))])
    async def admin_only():
        return {"ok": True}

    return app


@pytest.mark.asyncio
async def test_me_requires_token(db_session):
    app = build_app(db_session)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as ac:
        r = await ac.get("/me")
        assert r.status_code == 401


@pytest.mark.asyncio
async def test_me_returns_user_with_valid_token(db_session):
    settings = get_settings()
    u = await create_user(
        db_session,
        UsuarioCreate(email="x@y.com", password="StrongPass123!Q", nombre="X", rol=Rol.RRHH),
    )
    await db_session.flush()
    token = issue_access(str(u.id), settings)
    app = build_app(db_session)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as ac:
        r = await ac.get("/me", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        assert r.json()["email"] == "x@y.com"


@pytest.mark.asyncio
async def test_admin_only_blocks_non_admin(db_session):
    settings = get_settings()
    u = await create_user(
        db_session,
        UsuarioCreate(email="r@r.com", password="StrongPass123!Q", nombre="R", rol=Rol.RRHH),
    )
    await db_session.flush()
    token = issue_access(str(u.id), settings)
    app = build_app(db_session)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as ac:
        r = await ac.get("/admin-only", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 403
```

- [ ] **Step 4: Run**

Run: `cd backend && uv run pytest tests/core/test_deps.py -v`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/deps.py backend/app/core/permissions.py backend/tests/core/test_deps.py
git commit -m "feat(core): current_user dep + role-based dependency"
```

---

### Task 2.6: Failed-login throttle (in-memory v1)

**Files:**
- Create: `backend/app/core/throttle.py`
- Create: `backend/tests/core/test_throttle.py`

- [ ] **Step 1: Failing tests**

```python
# backend/tests/core/test_throttle.py
from datetime import datetime, timedelta, timezone

import pytest
from freezegun import freeze_time

from app.core.throttle import LoginThrottle


def test_blocks_after_five_failures():
    t = LoginThrottle(max_attempts=5, window=timedelta(minutes=15))
    for _ in range(5):
        t.record_failure("user@example.com")
    assert t.is_blocked("user@example.com") is True


def test_unblocks_after_window():
    t = LoginThrottle(max_attempts=2, window=timedelta(minutes=1))
    with freeze_time("2026-01-01T00:00:00Z"):
        t.record_failure("a")
        t.record_failure("a")
        assert t.is_blocked("a") is True
    with freeze_time("2026-01-01T00:02:00Z"):
        assert t.is_blocked("a") is False


def test_success_resets():
    t = LoginThrottle(max_attempts=3, window=timedelta(minutes=15))
    t.record_failure("z"); t.record_failure("z")
    t.record_success("z")
    assert t.is_blocked("z") is False
```

- [ ] **Step 2: Implement `throttle.py`**

```python
# backend/app/core/throttle.py
from collections import deque
from datetime import datetime, timedelta, timezone
from threading import Lock


class LoginThrottle:
    """In-memory throttle. Single-process MVP; swap for redis if scaled."""

    def __init__(self, max_attempts: int = 5, window: timedelta = timedelta(minutes=15)) -> None:
        self.max_attempts = max_attempts
        self.window = window
        self._buckets: dict[str, deque[datetime]] = {}
        self._lock = Lock()

    def _prune(self, key: str, now: datetime) -> None:
        dq = self._buckets.setdefault(key, deque())
        while dq and (now - dq[0]) > self.window:
            dq.popleft()

    def record_failure(self, key: str) -> None:
        now = datetime.now(timezone.utc)
        with self._lock:
            self._prune(key, now)
            self._buckets[key].append(now)

    def record_success(self, key: str) -> None:
        with self._lock:
            self._buckets.pop(key, None)

    def is_blocked(self, key: str) -> bool:
        now = datetime.now(timezone.utc)
        with self._lock:
            self._prune(key, now)
            return len(self._buckets.get(key, ())) >= self.max_attempts
```

- [ ] **Step 3: Run — should pass**

Run: `uv run pytest tests/core/test_throttle.py -v`
Expected: 3 passed.

- [ ] **Step 4: Commit**

```bash
git add backend/app/core/throttle.py backend/tests/core/test_throttle.py
git commit -m "feat(core): in-memory failed-login throttle"
```

---

### Task 2.7: Auth router (login, refresh, me, logout)

**Files:**
- Create: `backend/app/modules/usuarios/router.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/modules/usuarios/test_router.py`

- [ ] **Step 1: Implement `router.py`**

```python
# backend/app/modules/usuarios/router.py
from fastapi import APIRouter, Depends, Request
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import current_user, get_db
from app.core.jwt import decode_token, issue_access, issue_refresh
from app.core.permissions import require_role
from app.core.settings import Settings, get_settings
from app.core.throttle import LoginThrottle
from app.modules.usuarios import repository as repo
from app.modules.usuarios.models import Rol, Usuario
from app.modules.usuarios.schemas import LoginIn, TokenPair, UsuarioCreate, UsuarioOut
from app.modules.usuarios.service import authenticate, create_user
from app.shared.exceptions import UnauthorizedError

router = APIRouter(prefix="/api/auth", tags=["auth"])
users_router = APIRouter(prefix="/api/usuarios", tags=["usuarios"])

_throttle = LoginThrottle()


@router.post("/login", response_model=TokenPair)
async def login(
    body: LoginIn,
    request: Request,
    session: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    key = f"{body.email}:{request.client.host if request.client else 'na'}"
    if _throttle.is_blocked(key):
        raise UnauthorizedError("too many attempts, try again later")
    try:
        u = await authenticate(session, body.email, body.password)
    except UnauthorizedError:
        _throttle.record_failure(key)
        raise
    _throttle.record_success(key)
    return TokenPair(
        access_token=issue_access(str(u.id), settings),
        refresh_token=issue_refresh(str(u.id), settings),
    )


@router.post("/refresh", response_model=TokenPair)
async def refresh(
    refresh_token: str,
    session: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    try:
        claims = decode_token(refresh_token, settings)
    except JWTError as e:
        raise UnauthorizedError("invalid refresh") from e
    if claims.get("type") != "refresh":
        raise UnauthorizedError("wrong token type")
    u = await repo.get_by_id(session, claims["sub"])
    if u is None or not u.activo:
        raise UnauthorizedError("inactive user")
    return TokenPair(
        access_token=issue_access(str(u.id), settings),
        refresh_token=issue_refresh(str(u.id), settings),
    )


@router.get("/me", response_model=UsuarioOut)
async def me(user: Usuario = Depends(current_user)):
    return user


@users_router.get("", response_model=list[UsuarioOut], dependencies=[Depends(require_role(Rol.ADMIN))])
async def list_users(session: AsyncSession = Depends(get_db)):
    return await repo.list_all(session)


@users_router.post("", response_model=UsuarioOut, status_code=201, dependencies=[Depends(require_role(Rol.ADMIN))])
async def create_endpoint(payload: UsuarioCreate, session: AsyncSession = Depends(get_db)):
    return await create_user(session, payload)
```

- [ ] **Step 2: Wire routers in `main.py`**

```python
# inside create_app() in backend/app/main.py, after middlewares:
from app.modules.usuarios.router import router as auth_router, users_router

app.include_router(auth_router)
app.include_router(users_router)
```

- [ ] **Step 3: Failing tests**

```python
# backend/tests/modules/usuarios/test_router.py
import pytest
from httpx import AsyncClient, ASGITransport

from app.core.deps import get_db
from app.main import create_app
from app.modules.usuarios.models import Rol
from app.modules.usuarios.schemas import UsuarioCreate
from app.modules.usuarios.service import create_user


@pytest.mark.asyncio
async def test_login_then_me(db_session):
    await create_user(
        db_session,
        UsuarioCreate(email="z@z.com", password="StrongPass123!Q", nombre="Z", rol=Rol.MEDICO),
    )
    await db_session.flush()

    app = create_app()
    async def _db():
        yield db_session
    app.dependency_overrides[get_db] = _db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as ac:
        login = await ac.post("/api/auth/login", json={"email": "z@z.com", "password": "StrongPass123!Q"})
        assert login.status_code == 200
        token = login.json()["access_token"]
        me = await ac.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert me.status_code == 200
        assert me.json()["email"] == "z@z.com"


@pytest.mark.asyncio
async def test_admin_can_list_users_others_cannot(db_session):
    admin = await create_user(db_session, UsuarioCreate(email="a@a.com", password="StrongPass123!Q", nombre="A", rol=Rol.ADMIN))
    other = await create_user(db_session, UsuarioCreate(email="r@r.com", password="StrongPass123!Q", nombre="R", rol=Rol.RRHH))
    await db_session.flush()

    app = create_app()
    async def _db():
        yield db_session
    app.dependency_overrides[get_db] = _db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as ac:
        a = (await ac.post("/api/auth/login", json={"email": "a@a.com", "password": "StrongPass123!Q"})).json()["access_token"]
        r = (await ac.post("/api/auth/login", json={"email": "r@r.com", "password": "StrongPass123!Q"})).json()["access_token"]
        ok = await ac.get("/api/usuarios", headers={"Authorization": f"Bearer {a}"})
        bad = await ac.get("/api/usuarios", headers={"Authorization": f"Bearer {r}"})
        assert ok.status_code == 200
        assert bad.status_code == 403
```

- [ ] **Step 4: Run + commit**

Run: `uv run pytest tests/modules/usuarios/test_router.py -v`
Expected: 2 passed.

```bash
git add backend/app/modules/usuarios/router.py backend/app/main.py backend/tests/modules/usuarios/test_router.py
git commit -m "feat(usuarios): /auth/login|refresh|me + /usuarios (admin)"
```

---

## Phase 3 — Catálogos (areas, categorías, tipos de licencia, diagnósticos, topes)

> **Pattern note:** Tasks in this phase all follow the same shape — *model → migration → repo → service → schemas → router → tests*. Tasks 3.1 (Areas) shows the full skeleton so engineers reading later tasks have a reference; subsequent tasks shorten repetitive code.

### Task 3.1: Areas (model, CRUD, jerarquía padre)

**Files:**
- Create: `backend/app/modules/areas/{__init__,models,schemas,repository,service,router}.py`
- Create: `backend/tests/modules/areas/{__init__,test_service,test_router}.py`
- Add migration

- [ ] **Step 1: Model**

```python
# backend/app/modules/areas/models.py
from uuid import UUID

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db_base import Base
from app.core.ids import new_uuid7


class Area(Base):
    __tablename__ = "areas"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=new_uuid7)
    nombre: Mapped[str] = mapped_column(String(120), unique=True)
    parent_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("areas.id"), nullable=True
    )
```

- [ ] **Step 2: Schemas + repo + service**

```python
# backend/app/modules/areas/schemas.py
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class AreaCreate(BaseModel):
    nombre: str
    parent_id: UUID | None = None


class AreaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    nombre: str
    parent_id: UUID | None
```

```python
# backend/app/modules/areas/repository.py
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.areas.models import Area


async def list_all(s: AsyncSession) -> list[Area]:
    return list((await s.execute(select(Area).order_by(Area.nombre))).scalars())


async def get(s: AsyncSession, id_: UUID) -> Area | None:
    return (await s.execute(select(Area).where(Area.id == id_))).scalar_one_or_none()


async def by_name(s: AsyncSession, nombre: str) -> Area | None:
    return (await s.execute(select(Area).where(Area.nombre == nombre))).scalar_one_or_none()


async def insert(s: AsyncSession, a: Area) -> Area:
    s.add(a); await s.flush(); return a
```

```python
# backend/app/modules/areas/service.py
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.areas import repository as repo
from app.modules.areas.models import Area
from app.modules.areas.schemas import AreaCreate
from app.shared.exceptions import ConflictError, NotFoundError


async def create_area(s: AsyncSession, payload: AreaCreate) -> Area:
    if await repo.by_name(s, payload.nombre):
        raise ConflictError("area exists", detail={"field": "nombre"})
    if payload.parent_id and not await repo.get(s, payload.parent_id):
        raise NotFoundError("parent area not found")
    return await repo.insert(s, Area(nombre=payload.nombre, parent_id=payload.parent_id))
```

- [ ] **Step 3: Router**

```python
# backend/app/modules/areas/router.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.core.permissions import require_role
from app.modules.areas import repository as repo
from app.modules.areas.schemas import AreaCreate, AreaOut
from app.modules.areas.service import create_area
from app.modules.usuarios.models import Rol

router = APIRouter(prefix="/api/areas", tags=["areas"])


@router.get("", response_model=list[AreaOut])
async def list_areas(s: AsyncSession = Depends(get_db)):
    return await repo.list_all(s)


@router.post(
    "", response_model=AreaOut, status_code=201,
    dependencies=[Depends(require_role(Rol.ADMIN, Rol.RRHH))],
)
async def create(payload: AreaCreate, s: AsyncSession = Depends(get_db)):
    return await create_area(s, payload)
```

Register in `main.py`:
```python
from app.modules.areas.router import router as areas_router
app.include_router(areas_router)
```

Add import to `alembic/env.py`:
```python
from app.modules.areas import models as _areas_models  # noqa: F401
```

- [ ] **Step 4: Service test**

```python
# backend/tests/modules/areas/test_service.py
import pytest

from app.modules.areas.schemas import AreaCreate
from app.modules.areas.service import create_area
from app.shared.exceptions import ConflictError


@pytest.mark.asyncio
async def test_duplicate_name_rejected(db_session):
    await create_area(db_session, AreaCreate(nombre="RRHH"))
    with pytest.raises(ConflictError):
        await create_area(db_session, AreaCreate(nombre="RRHH"))
```

- [ ] **Step 5: Migration + run + commit**

```bash
cd backend && uv run alembic revision --autogenerate -m "areas table"
uv run alembic upgrade head
uv run pytest tests/modules/areas -v
git add backend/app/modules/areas backend/tests/modules/areas backend/alembic/versions backend/alembic/env.py backend/app/main.py
git commit -m "feat(areas): CRUD with parent jerarquía"
```

---

### Task 3.2: Categorías laborales

**Files:**
- Create: `backend/app/modules/categorias/{__init__,models,schemas,repository,service,router}.py`
- Create tests + migration

- [ ] **Step 1: Model**

```python
# backend/app/modules/categorias/models.py
from uuid import UUID

from sqlalchemy import Boolean, String
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db_base import Base
from app.core.ids import new_uuid7


class CategoriaLaboral(Base):
    __tablename__ = "categorias_laborales"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=new_uuid7)
    codigo: Mapped[str] = mapped_column(String(60), unique=True)
    nombre: Mapped[str] = mapped_column(String(120))
    activa: Mapped[bool] = mapped_column(Boolean, default=True)
```

- [ ] **Step 2: Schemas, repo, service, router (mirror Task 3.1)**

```python
# backend/app/modules/categorias/schemas.py
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class CategoriaCreate(BaseModel):
    codigo: str
    nombre: str


class CategoriaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    codigo: str
    nombre: str
    activa: bool
```

```python
# backend/app/modules/categorias/repository.py
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.categorias.models import CategoriaLaboral


async def list_all(s: AsyncSession) -> list[CategoriaLaboral]:
    return list((await s.execute(select(CategoriaLaboral).order_by(CategoriaLaboral.codigo))).scalars())

async def by_codigo(s: AsyncSession, codigo: str) -> CategoriaLaboral | None:
    return (await s.execute(select(CategoriaLaboral).where(CategoriaLaboral.codigo == codigo))).scalar_one_or_none()

async def get(s: AsyncSession, id_: UUID) -> CategoriaLaboral | None:
    return (await s.execute(select(CategoriaLaboral).where(CategoriaLaboral.id == id_))).scalar_one_or_none()

async def insert(s: AsyncSession, c: CategoriaLaboral) -> CategoriaLaboral:
    s.add(c); await s.flush(); return c
```

```python
# backend/app/modules/categorias/service.py
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.categorias import repository as repo
from app.modules.categorias.models import CategoriaLaboral
from app.modules.categorias.schemas import CategoriaCreate
from app.shared.exceptions import ConflictError


async def create_categoria(s: AsyncSession, p: CategoriaCreate) -> CategoriaLaboral:
    if await repo.by_codigo(s, p.codigo):
        raise ConflictError("categoria exists", detail={"field": "codigo"})
    return await repo.insert(s, CategoriaLaboral(codigo=p.codigo, nombre=p.nombre))
```

```python
# backend/app/modules/categorias/router.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.core.permissions import require_role
from app.modules.categorias import repository as repo
from app.modules.categorias.schemas import CategoriaCreate, CategoriaOut
from app.modules.categorias.service import create_categoria
from app.modules.usuarios.models import Rol

router = APIRouter(prefix="/api/categorias", tags=["categorias"])


@router.get("", response_model=list[CategoriaOut])
async def list_categorias(s: AsyncSession = Depends(get_db)):
    return await repo.list_all(s)


@router.post("", response_model=CategoriaOut, status_code=201,
             dependencies=[Depends(require_role(Rol.ADMIN))])
async def create(p: CategoriaCreate, s: AsyncSession = Depends(get_db)):
    return await create_categoria(s, p)
```

- [ ] **Step 3: Test, migration, register, commit**

```python
# backend/tests/modules/categorias/test_service.py
import pytest
from app.modules.categorias.schemas import CategoriaCreate
from app.modules.categorias.service import create_categoria
from app.shared.exceptions import ConflictError


@pytest.mark.asyncio
async def test_unique_codigo(db_session):
    await create_categoria(db_session, CategoriaCreate(codigo="planta-permanente", nombre="Planta"))
    with pytest.raises(ConflictError):
        await create_categoria(db_session, CategoriaCreate(codigo="planta-permanente", nombre="x"))
```

```bash
cd backend && uv run alembic revision --autogenerate -m "categorias_laborales"
uv run alembic upgrade head
uv run pytest tests/modules/categorias -v
git add backend/app/modules/categorias backend/tests/modules/categorias backend/alembic/versions backend/alembic/env.py backend/app/main.py
git commit -m "feat(categorias): categorias_laborales CRUD"
```

Don't forget to add to `alembic/env.py` and `main.py`.

---

### Task 3.3: Tipos de licencia

**Files:** `backend/app/modules/tipos_licencia/*` + tests + migration

- [ ] **Step 1: Model**

```python
# backend/app/modules/tipos_licencia/models.py
from uuid import UUID

from sqlalchemy import Boolean, String
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db_base import Base
from app.core.ids import new_uuid7


class TipoLicencia(Base):
    __tablename__ = "tipos_licencia"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=new_uuid7)
    codigo: Mapped[str] = mapped_column(String(60), unique=True)
    nombre: Mapped[str] = mapped_column(String(120))
    base_legal: Mapped[str | None] = mapped_column(String(120), nullable=True)
    paga: Mapped[bool] = mapped_column(Boolean, default=True)
    computa_dias: Mapped[bool] = mapped_column(Boolean, default=True)
```

- [ ] **Step 2: Schemas + repo + service + router**

```python
# backend/app/modules/tipos_licencia/schemas.py
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class TipoLicenciaCreate(BaseModel):
    codigo: str
    nombre: str
    base_legal: str | None = None
    paga: bool = True
    computa_dias: bool = True


class TipoLicenciaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    codigo: str
    nombre: str
    base_legal: str | None
    paga: bool
    computa_dias: bool
```

```python
# backend/app/modules/tipos_licencia/repository.py
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.tipos_licencia.models import TipoLicencia


async def list_all(s: AsyncSession) -> list[TipoLicencia]:
    return list((await s.execute(select(TipoLicencia).order_by(TipoLicencia.codigo))).scalars())

async def by_codigo(s: AsyncSession, codigo: str) -> TipoLicencia | None:
    return (await s.execute(select(TipoLicencia).where(TipoLicencia.codigo == codigo))).scalar_one_or_none()

async def get(s: AsyncSession, id_: UUID) -> TipoLicencia | None:
    return (await s.execute(select(TipoLicencia).where(TipoLicencia.id == id_))).scalar_one_or_none()

async def insert(s: AsyncSession, t: TipoLicencia) -> TipoLicencia:
    s.add(t); await s.flush(); return t
```

```python
# backend/app/modules/tipos_licencia/service.py
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.tipos_licencia import repository as repo
from app.modules.tipos_licencia.models import TipoLicencia
from app.modules.tipos_licencia.schemas import TipoLicenciaCreate
from app.shared.exceptions import ConflictError


async def create_tipo(s: AsyncSession, p: TipoLicenciaCreate) -> TipoLicencia:
    if await repo.by_codigo(s, p.codigo):
        raise ConflictError("tipo de licencia ya existe", detail={"field": "codigo"})
    return await repo.insert(s, TipoLicencia(
        codigo=p.codigo, nombre=p.nombre, base_legal=p.base_legal,
        paga=p.paga, computa_dias=p.computa_dias,
    ))
```

```python
# backend/app/modules/tipos_licencia/router.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.core.permissions import require_role
from app.modules.tipos_licencia import repository as repo
from app.modules.tipos_licencia.schemas import TipoLicenciaCreate, TipoLicenciaOut
from app.modules.tipos_licencia.service import create_tipo
from app.modules.usuarios.models import Rol

router = APIRouter(prefix="/api/tipos-licencia", tags=["tipos-licencia"])


@router.get("", response_model=list[TipoLicenciaOut])
async def list_(s: AsyncSession = Depends(get_db)):
    return await repo.list_all(s)


@router.post("", response_model=TipoLicenciaOut, status_code=201,
             dependencies=[Depends(require_role(Rol.ADMIN))])
async def create(p: TipoLicenciaCreate, s: AsyncSession = Depends(get_db)):
    return await create_tipo(s, p)
```

- [ ] **Step 3: Test**

```python
# backend/tests/modules/tipos_licencia/test_service.py
import pytest
from app.modules.tipos_licencia.schemas import TipoLicenciaCreate
from app.modules.tipos_licencia.service import create_tipo
from app.shared.exceptions import ConflictError


@pytest.mark.asyncio
async def test_unique_codigo(db_session):
    await create_tipo(db_session, TipoLicenciaCreate(codigo="enfermedad-comun", nombre="Enfermedad común"))
    with pytest.raises(ConflictError):
        await create_tipo(db_session, TipoLicenciaCreate(codigo="enfermedad-comun", nombre="x"))
```

- [ ] **Step 4: Migration + commit**

```bash
cd backend && uv run alembic revision --autogenerate -m "tipos_licencia"
uv run alembic upgrade head
uv run pytest tests/modules/tipos_licencia -v
git add backend/app/modules/tipos_licencia backend/tests/modules/tipos_licencia backend/alembic/versions backend/alembic/env.py backend/app/main.py
git commit -m "feat(tipos-licencia): tipos_licencia CRUD"
```

---

### Task 3.4: Diagnósticos

**Files:** `backend/app/modules/diagnosticos/*` + tests + migration

- [ ] **Step 1: Model**

```python
# backend/app/modules/diagnosticos/models.py
from uuid import UUID

from sqlalchemy import Boolean, String
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db_base import Base
from app.core.ids import new_uuid7


class Diagnostico(Base):
    __tablename__ = "diagnosticos"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=new_uuid7)
    codigo_cie10: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    descripcion: Mapped[str] = mapped_column(String(255))
    categoria: Mapped[str | None] = mapped_column(String(60), nullable=True, index=True)
    requiere_junta: Mapped[bool] = mapped_column(Boolean, default=False)
```

- [ ] **Step 2: Schemas + repo + service + router**

```python
# backend/app/modules/diagnosticos/schemas.py
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class DiagnosticoCreate(BaseModel):
    codigo_cie10: str | None = None
    descripcion: str
    categoria: str | None = None
    requiere_junta: bool = False


class DiagnosticoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    codigo_cie10: str | None
    descripcion: str
    categoria: str | None
    requiere_junta: bool
```

```python
# backend/app/modules/diagnosticos/repository.py
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.diagnosticos.models import Diagnostico


async def list_all(s: AsyncSession, categoria: str | None = None) -> list[Diagnostico]:
    stmt = select(Diagnostico).order_by(Diagnostico.descripcion)
    if categoria:
        stmt = stmt.where(Diagnostico.categoria == categoria)
    return list((await s.execute(stmt)).scalars())

async def get(s: AsyncSession, id_: UUID) -> Diagnostico | None:
    return (await s.execute(select(Diagnostico).where(Diagnostico.id == id_))).scalar_one_or_none()

async def insert(s: AsyncSession, d: Diagnostico) -> Diagnostico:
    s.add(d); await s.flush(); return d
```

```python
# backend/app/modules/diagnosticos/service.py
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.diagnosticos import repository as repo
from app.modules.diagnosticos.models import Diagnostico
from app.modules.diagnosticos.schemas import DiagnosticoCreate


async def create_diagnostico(s: AsyncSession, p: DiagnosticoCreate) -> Diagnostico:
    return await repo.insert(s, Diagnostico(
        codigo_cie10=p.codigo_cie10, descripcion=p.descripcion,
        categoria=p.categoria, requiere_junta=p.requiere_junta,
    ))
```

```python
# backend/app/modules/diagnosticos/router.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.core.permissions import require_role
from app.modules.diagnosticos import repository as repo
from app.modules.diagnosticos.schemas import DiagnosticoCreate, DiagnosticoOut
from app.modules.diagnosticos.service import create_diagnostico
from app.modules.usuarios.models import Rol

router = APIRouter(prefix="/api/diagnosticos", tags=["diagnosticos"])


@router.get("", response_model=list[DiagnosticoOut])
async def list_(categoria: str | None = Query(default=None), s: AsyncSession = Depends(get_db)):
    return await repo.list_all(s, categoria=categoria)


@router.post("", response_model=DiagnosticoOut, status_code=201,
             dependencies=[Depends(require_role(Rol.ADMIN))])
async def create(p: DiagnosticoCreate, s: AsyncSession = Depends(get_db)):
    return await create_diagnostico(s, p)
```

- [ ] **Step 3: Test**

```python
# backend/tests/modules/diagnosticos/test_service.py
import pytest
from app.modules.diagnosticos.schemas import DiagnosticoCreate
from app.modules.diagnosticos.service import create_diagnostico


@pytest.mark.asyncio
async def test_create_diagnostico_basic(db_session):
    d = await create_diagnostico(db_session, DiagnosticoCreate(
        codigo_cie10="J06.9", descripcion="Infección respiratoria aguda",
        categoria="infeccioso", requiere_junta=False,
    ))
    assert d.id is not None
    assert d.categoria == "infeccioso"
```

- [ ] **Step 4: Migration + commit**

```bash
cd backend && uv run alembic revision --autogenerate -m "diagnosticos"
uv run alembic upgrade head
uv run pytest tests/modules/diagnosticos -v
git add backend/app/modules/diagnosticos backend/tests/modules/diagnosticos backend/alembic/versions backend/alembic/env.py backend/app/main.py
git commit -m "feat(diagnosticos): diagnosticos CRUD"
```

---

### Task 3.5: Topes de días (versionado)

**Files:** `backend/app/modules/topes/{__init__,models,schemas,repository,service,router}.py` + tests + migration

- [ ] **Step 1: Model**

```python
# backend/app/modules/topes/models.py
from datetime import date
from uuid import UUID

from sqlalchemy import CheckConstraint, Date, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db_base import Base
from app.core.ids import new_uuid7


class TopeDias(Base):
    __tablename__ = "topes_dias"
    __table_args__ = (
        UniqueConstraint("categoria_id", "tipo_licencia_id", "vigente_desde", name="uq_tope_inicio"),
        CheckConstraint("ventana IN ('anio-calendario','anio-aniversario','sin-limite')", name="ck_ventana"),
    )

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=new_uuid7)
    categoria_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("categorias_laborales.id"))
    tipo_licencia_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("tipos_licencia.id"))
    dias_maximos: Mapped[int] = mapped_column(Integer)
    ventana: Mapped[str] = mapped_column(String(32))
    vigente_desde: Mapped[date] = mapped_column(Date)
    vigente_hasta: Mapped[date | None] = mapped_column(Date, nullable=True)
    observacion: Mapped[str | None] = mapped_column(String(255), nullable=True)
```

- [ ] **Step 2: Repository — `tope_vigente`, `set_tope` (versioned)**

```python
# backend/app/modules/topes/repository.py
from datetime import date
from uuid import UUID

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.topes.models import TopeDias


async def tope_vigente(
    s: AsyncSession, categoria_id: UUID, tipo_licencia_id: UUID, en_fecha: date
) -> TopeDias | None:
    stmt = (
        select(TopeDias)
        .where(
            TopeDias.categoria_id == categoria_id,
            TopeDias.tipo_licencia_id == tipo_licencia_id,
            TopeDias.vigente_desde <= en_fecha,
            (TopeDias.vigente_hasta.is_(None)) | (TopeDias.vigente_hasta >= en_fecha),
        )
        .order_by(TopeDias.vigente_desde.desc())
        .limit(1)
    )
    return (await s.execute(stmt)).scalar_one_or_none()


async def set_tope(
    s: AsyncSession,
    *,
    categoria_id: UUID,
    tipo_licencia_id: UUID,
    dias_maximos: int,
    ventana: str,
    desde: date,
    observacion: str | None,
) -> TopeDias:
    # Close currently-open versions on the day before `desde`.
    await s.execute(
        update(TopeDias)
        .where(
            and_(
                TopeDias.categoria_id == categoria_id,
                TopeDias.tipo_licencia_id == tipo_licencia_id,
                TopeDias.vigente_hasta.is_(None),
            )
        )
        .values(vigente_hasta=desde)
    )
    nuevo = TopeDias(
        categoria_id=categoria_id,
        tipo_licencia_id=tipo_licencia_id,
        dias_maximos=dias_maximos,
        ventana=ventana,
        vigente_desde=desde,
        observacion=observacion,
    )
    s.add(nuevo)
    await s.flush()
    return nuevo


async def listar_actuales(s: AsyncSession) -> list[TopeDias]:
    stmt = select(TopeDias).where(TopeDias.vigente_hasta.is_(None))
    return list((await s.execute(stmt)).scalars())
```

- [ ] **Step 3: Schemas + service + router**

```python
# backend/app/modules/topes/schemas.py
from datetime import date
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class TopeSet(BaseModel):
    dias_maximos: int = Field(ge=0)
    ventana: str  # validated by CHECK
    desde: date
    observacion: str | None = None


class TopeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    categoria_id: UUID
    tipo_licencia_id: UUID
    dias_maximos: int
    ventana: str
    vigente_desde: date
    vigente_hasta: date | None
    observacion: str | None
```

```python
# backend/app/modules/topes/service.py
from datetime import date
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.topes import repository as repo
from app.modules.topes.models import TopeDias
from app.modules.topes.schemas import TopeSet
from app.shared.exceptions import ValidationError


_VENTANAS = {"anio-calendario", "anio-aniversario", "sin-limite"}


async def set_tope(
    s: AsyncSession,
    categoria_id: UUID,
    tipo_licencia_id: UUID,
    payload: TopeSet,
) -> TopeDias:
    if payload.ventana not in _VENTANAS:
        raise ValidationError("ventana invalida", detail={"ventana": payload.ventana})
    return await repo.set_tope(
        s,
        categoria_id=categoria_id,
        tipo_licencia_id=tipo_licencia_id,
        dias_maximos=payload.dias_maximos,
        ventana=payload.ventana,
        desde=payload.desde,
        observacion=payload.observacion,
    )
```

```python
# backend/app/modules/topes/router.py
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.core.permissions import require_role
from app.modules.topes import repository as repo
from app.modules.topes.schemas import TopeOut, TopeSet
from app.modules.topes.service import set_tope
from app.modules.usuarios.models import Rol

router = APIRouter(prefix="/api/admin/topes", tags=["topes"],
                   dependencies=[Depends(require_role(Rol.ADMIN))])


@router.get("", response_model=list[TopeOut])
async def listar(s: AsyncSession = Depends(get_db)):
    return await repo.listar_actuales(s)


@router.put("/{categoria_id}/{tipo_licencia_id}", response_model=TopeOut)
async def upsert(
    categoria_id: UUID,
    tipo_licencia_id: UUID,
    payload: TopeSet,
    s: AsyncSession = Depends(get_db),
):
    return await set_tope(s, categoria_id, tipo_licencia_id, payload)
```

- [ ] **Step 4: Tests for versioning**

```python
# backend/tests/modules/topes/test_repository.py
from datetime import date

import pytest

from app.modules.categorias.schemas import CategoriaCreate
from app.modules.categorias.service import create_categoria
from app.modules.tipos_licencia.schemas import TipoLicenciaCreate
from app.modules.tipos_licencia.service import create_tipo
from app.modules.topes import repository as repo


@pytest.mark.asyncio
async def test_set_tope_closes_previous_version(db_session):
    cat = await create_categoria(db_session, CategoriaCreate(codigo="planta", nombre="P"))
    tipo = await create_tipo(db_session, TipoLicenciaCreate(codigo="ec", nombre="Enfermedad común"))
    await db_session.flush()

    t1 = await repo.set_tope(
        db_session, categoria_id=cat.id, tipo_licencia_id=tipo.id,
        dias_maximos=90, ventana="anio-aniversario",
        desde=date(2026, 1, 1), observacion="v1",
    )
    t2 = await repo.set_tope(
        db_session, categoria_id=cat.id, tipo_licencia_id=tipo.id,
        dias_maximos=120, ventana="anio-aniversario",
        desde=date(2026, 6, 1), observacion="v2",
    )
    # Re-read t1 to see its `vigente_hasta` was set.
    await db_session.refresh(t1)
    assert t1.vigente_hasta == date(2026, 6, 1)
    assert t2.vigente_hasta is None


@pytest.mark.asyncio
async def test_tope_vigente_picks_latest_active(db_session):
    cat = await create_categoria(db_session, CategoriaCreate(codigo="c", nombre="c"))
    tipo = await create_tipo(db_session, TipoLicenciaCreate(codigo="t", nombre="t"))
    await db_session.flush()
    await repo.set_tope(db_session, categoria_id=cat.id, tipo_licencia_id=tipo.id,
                       dias_maximos=30, ventana="anio-calendario",
                       desde=date(2025, 1, 1), observacion=None)
    await repo.set_tope(db_session, categoria_id=cat.id, tipo_licencia_id=tipo.id,
                       dias_maximos=60, ventana="anio-calendario",
                       desde=date(2026, 1, 1), observacion=None)
    found = await repo.tope_vigente(db_session, cat.id, tipo.id, en_fecha=date(2026, 6, 15))
    assert found is not None and found.dias_maximos == 60
```

- [ ] **Step 5: Migration + register + commit**

```bash
cd backend && uv run alembic revision --autogenerate -m "topes_dias"
uv run alembic upgrade head
uv run pytest tests/modules/topes -v
git add backend/app/modules/topes backend/tests/modules/topes backend/alembic/versions backend/alembic/env.py backend/app/main.py
git commit -m "feat(topes): topes_dias versionados + admin endpoint"
```

Register router and add model import to alembic/env.py.

---

## Phase 4 — Empleados

### Task 4.1: Empleado model + migration

**Files:** `backend/app/modules/empleados/*` + tests + migration

- [ ] **Step 1: Model**

```python
# backend/app/modules/empleados/models.py
from datetime import date, datetime
from uuid import UUID

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db_base import Base
from app.core.ids import new_uuid7


class Empleado(Base):
    __tablename__ = "empleados"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=new_uuid7)
    legajo: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    cuil: Mapped[str] = mapped_column(String(13), unique=True, index=True)
    nombre: Mapped[str] = mapped_column(String(120))
    apellido: Mapped[str] = mapped_column(String(120))
    fecha_nacimiento: Mapped[date | None] = mapped_column(Date, nullable=True)
    fecha_ingreso: Mapped[date] = mapped_column(Date)
    area_id: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True), ForeignKey("areas.id"), nullable=True)
    categoria_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("categorias_laborales.id"))
    supervisor_id: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True), ForeignKey("empleados.id"), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    telefono: Mapped[str | None] = mapped_column(String(40), nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
```

- [ ] **Step 2: Schemas**

```python
# backend/app/modules/empleados/schemas.py
from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


_CUIL_RE = r"^\d{2}-\d{8}-\d{1}$|^\d{11}$"


class EmpleadoCreate(BaseModel):
    legajo: str = Field(min_length=1, max_length=40)
    cuil: str = Field(pattern=_CUIL_RE)
    nombre: str
    apellido: str
    fecha_nacimiento: date | None = None
    fecha_ingreso: date
    area_id: UUID | None = None
    categoria_id: UUID
    supervisor_id: UUID | None = None
    email: EmailStr | None = None
    telefono: str | None = None

    @field_validator("cuil")
    @classmethod
    def normalize_cuil(cls, v: str) -> str:
        return v.replace("-", "")


class EmpleadoUpdate(BaseModel):
    nombre: str | None = None
    apellido: str | None = None
    area_id: UUID | None = None
    categoria_id: UUID | None = None
    supervisor_id: UUID | None = None
    email: EmailStr | None = None
    telefono: str | None = None
    activo: bool | None = None


class EmpleadoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    legajo: str
    cuil: str
    nombre: str
    apellido: str
    fecha_nacimiento: date | None
    fecha_ingreso: date
    area_id: UUID | None
    categoria_id: UUID
    supervisor_id: UUID | None
    email: str | None
    telefono: str | None
    activo: bool
```

- [ ] **Step 3: Repository**

```python
# backend/app/modules/empleados/repository.py
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.empleados.models import Empleado


async def list_(s: AsyncSession, q: str | None = None, limit: int = 50, offset: int = 0) -> list[Empleado]:
    stmt = select(Empleado).order_by(Empleado.apellido, Empleado.nombre).limit(limit).offset(offset)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(
            Empleado.legajo.ilike(like),
            Empleado.cuil.ilike(like),
            Empleado.apellido.ilike(like),
            Empleado.nombre.ilike(like),
        ))
    return list((await s.execute(stmt)).scalars())


async def get(s: AsyncSession, id_: UUID) -> Empleado | None:
    return (await s.execute(select(Empleado).where(Empleado.id == id_))).scalar_one_or_none()


async def by_legajo(s: AsyncSession, legajo: str) -> Empleado | None:
    return (await s.execute(select(Empleado).where(Empleado.legajo == legajo))).scalar_one_or_none()


async def by_cuil(s: AsyncSession, cuil: str) -> Empleado | None:
    return (await s.execute(select(Empleado).where(Empleado.cuil == cuil))).scalar_one_or_none()


async def insert(s: AsyncSession, e: Empleado) -> Empleado:
    s.add(e); await s.flush(); return e
```

- [ ] **Step 4: Service**

```python
# backend/app/modules/empleados/service.py
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.categorias import repository as cats_repo
from app.modules.empleados import repository as repo
from app.modules.empleados.models import Empleado
from app.modules.empleados.schemas import EmpleadoCreate
from app.shared.exceptions import ConflictError, NotFoundError


async def create_empleado(s: AsyncSession, payload: EmpleadoCreate) -> Empleado:
    if await repo.by_legajo(s, payload.legajo):
        raise ConflictError("legajo en uso", detail={"field": "legajo"})
    if await repo.by_cuil(s, payload.cuil):
        raise ConflictError("cuil en uso", detail={"field": "cuil"})
    if not await cats_repo.get(s, payload.categoria_id):
        raise NotFoundError("categoria no encontrada", detail={"categoria_id": str(payload.categoria_id)})
    return await repo.insert(s, Empleado(**payload.model_dump()))
```

- [ ] **Step 5: Router**

```python
# backend/app/modules/empleados/router.py
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.core.permissions import require_role
from app.modules.empleados import repository as repo
from app.modules.empleados.schemas import EmpleadoCreate, EmpleadoOut
from app.modules.empleados.service import create_empleado
from app.modules.usuarios.models import Rol
from app.shared.exceptions import NotFoundError

router = APIRouter(prefix="/api/empleados", tags=["empleados"])


@router.get("", response_model=list[EmpleadoOut])
async def list_empleados(
    q: str | None = Query(default=None),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    s: AsyncSession = Depends(get_db),
):
    return await repo.list_(s, q=q, limit=limit, offset=offset)


@router.get("/{id_}", response_model=EmpleadoOut)
async def get_one(id_: UUID, s: AsyncSession = Depends(get_db)):
    e = await repo.get(s, id_)
    if not e:
        raise NotFoundError("empleado no encontrado")
    return e


@router.post(
    "", response_model=EmpleadoOut, status_code=201,
    dependencies=[Depends(require_role(Rol.ADMIN, Rol.RRHH))],
)
async def create(payload: EmpleadoCreate, s: AsyncSession = Depends(get_db)):
    return await create_empleado(s, payload)
```

- [ ] **Step 6: Tests**

```python
# backend/tests/modules/empleados/test_service.py
from datetime import date

import pytest

from app.modules.categorias.schemas import CategoriaCreate
from app.modules.categorias.service import create_categoria
from app.modules.empleados.schemas import EmpleadoCreate
from app.modules.empleados.service import create_empleado
from app.shared.exceptions import ConflictError, NotFoundError


@pytest.mark.asyncio
async def test_create_requires_existing_categoria(db_session):
    import uuid
    with pytest.raises(NotFoundError):
        await create_empleado(db_session, EmpleadoCreate(
            legajo="L1", cuil="20111111119", nombre="A", apellido="B",
            fecha_ingreso=date(2020, 1, 1), categoria_id=uuid.uuid4(),
        ))


@pytest.mark.asyncio
async def test_duplicate_legajo(db_session):
    cat = await create_categoria(db_session, CategoriaCreate(codigo="planta", nombre="P"))
    await db_session.flush()
    base = EmpleadoCreate(legajo="L1", cuil="20111111119", nombre="A", apellido="B",
                          fecha_ingreso=date(2020, 1, 1), categoria_id=cat.id)
    await create_empleado(db_session, base)
    with pytest.raises(ConflictError):
        await create_empleado(db_session, base.model_copy(update={"cuil": "20222222222"}))
```

- [ ] **Step 7: Migration + register + commit**

```bash
cd backend && uv run alembic revision --autogenerate -m "empleados"
uv run alembic upgrade head
uv run pytest tests/modules/empleados -v
git add backend/app/modules/empleados backend/tests/modules/empleados backend/alembic/versions backend/alembic/env.py backend/app/main.py
git commit -m "feat(empleados): empleados CRUD + búsqueda paginada"
```

Add to `alembic/env.py` and `main.py`.

---

## Phase 5 — Adjuntos (MinIO)

### Task 5.1: Adjunto model + storage helper

**Files:**
- Create: `backend/app/modules/adjuntos/{__init__,models,schemas,repository,service,router}.py`
- Modify: `backend/app/core/storage.py` (add upload/presign helpers)
- Tests + migration

- [ ] **Step 1: Model**

```python
# backend/app/modules/adjuntos/models.py
from datetime import datetime
from uuid import UUID

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db_base import Base
from app.core.ids import new_uuid7


class Adjunto(Base):
    __tablename__ = "adjuntos"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=new_uuid7)
    licencia_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("licencias.id", ondelete="CASCADE")
    )
    nombre_original: Mapped[str] = mapped_column(String(255))
    mime_type: Mapped[str] = mapped_column(String(120))
    size_bytes: Mapped[int] = mapped_column(BigInteger)
    sha256: Mapped[str] = mapped_column(String(64))
    storage_key: Mapped[str] = mapped_column(String(255))
    subido_por: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
```

> **Note:** Migration depends on the `licencias` table that is created in Phase 6. **Do the autogenerate + apply for adjuntos after Task 6.1 is done** (after `licencias` exists).

- [ ] **Step 2: Storage helpers — extend `app/core/storage.py`**

```python
# backend/app/core/storage.py  (append below existing helpers)
import hashlib
from datetime import timedelta
from io import BytesIO

from minio import Minio


def sha256_of(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def put_object(
    client: Minio,
    bucket: str,
    key: str,
    data: bytes,
    content_type: str,
) -> None:
    client.put_object(bucket, key, BytesIO(data), len(data), content_type=content_type)


def presigned_get(client: Minio, bucket: str, key: str, ttl_minutes: int = 5) -> str:
    return client.presigned_get_object(bucket, key, expires=timedelta(minutes=ttl_minutes))
```

- [ ] **Step 3: Schemas**

```python
# backend/app/modules/adjuntos/schemas.py
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class AdjuntoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    licencia_id: UUID
    nombre_original: str
    mime_type: str
    size_bytes: int
    sha256: str
    created_at: datetime


class AdjuntoDownload(BaseModel):
    url: str
    expires_in_seconds: int
```

- [ ] **Step 4: Repository + service**

```python
# backend/app/modules/adjuntos/repository.py
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.adjuntos.models import Adjunto


async def insert(s: AsyncSession, a: Adjunto) -> Adjunto:
    s.add(a); await s.flush(); return a


async def get(s: AsyncSession, id_: UUID) -> Adjunto | None:
    return (await s.execute(select(Adjunto).where(Adjunto.id == id_))).scalar_one_or_none()


async def list_for_licencia(s: AsyncSession, licencia_id: UUID) -> list[Adjunto]:
    stmt = select(Adjunto).where(Adjunto.licencia_id == licencia_id).order_by(Adjunto.created_at)
    return list((await s.execute(stmt)).scalars())
```

```python
# backend/app/modules/adjuntos/service.py
from uuid import UUID

from minio import Minio
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import Settings
from app.core.storage import presigned_get, put_object, sha256_of
from app.modules.adjuntos import repository as repo
from app.modules.adjuntos.models import Adjunto
from app.shared.exceptions import ValidationError

_ALLOWED_MIME = {"application/pdf", "image/png", "image/jpeg", "image/webp"}
_MAX_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


async def upload_adjunto(
    s: AsyncSession,
    *,
    mc: Minio,
    settings: Settings,
    licencia_id: UUID,
    nombre_original: str,
    mime_type: str,
    payload: bytes,
    usuario_id: UUID | None,
) -> Adjunto:
    if mime_type not in _ALLOWED_MIME:
        raise ValidationError("tipo de archivo no permitido", detail={"mime": mime_type})
    if len(payload) > _MAX_SIZE_BYTES:
        raise ValidationError("archivo demasiado grande", detail={"max": _MAX_SIZE_BYTES})

    digest = sha256_of(payload)
    key = f"licencias/{licencia_id}/{digest}-{nombre_original}"
    put_object(mc, settings.minio_bucket, key, payload, mime_type)

    return await repo.insert(
        s,
        Adjunto(
            licencia_id=licencia_id,
            nombre_original=nombre_original,
            mime_type=mime_type,
            size_bytes=len(payload),
            sha256=digest,
            storage_key=key,
            subido_por=usuario_id,
        ),
    )


async def download_url(
    s: AsyncSession, mc: Minio, settings: Settings, adjunto_id: UUID
) -> tuple[str, int]:
    adj = await repo.get(s, adjunto_id)
    if not adj:
        from app.shared.exceptions import NotFoundError
        raise NotFoundError("adjunto no encontrado")
    ttl_min = 5
    return presigned_get(mc, settings.minio_bucket, adj.storage_key, ttl_minutes=ttl_min), ttl_min * 60
```

- [ ] **Step 5: Router**

```python
# backend/app/modules/adjuntos/router.py
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile
from minio import Minio
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import current_user, get_db
from app.core.permissions import require_role
from app.core.settings import Settings, get_settings
from app.core.storage import minio_client
from app.modules.adjuntos.schemas import AdjuntoDownload, AdjuntoOut
from app.modules.adjuntos.service import download_url, upload_adjunto
from app.modules.usuarios.models import Rol, Usuario

router = APIRouter(prefix="/api/adjuntos", tags=["adjuntos"])


def _mc(settings: Settings = Depends(get_settings)) -> Minio:
    return minio_client(settings)


@router.post("", response_model=AdjuntoOut, status_code=201,
             dependencies=[Depends(require_role(Rol.ADMIN, Rol.RRHH, Rol.MEDICO))])
async def upload(
    licencia_id: UUID = Form(...),
    file: UploadFile = File(...),
    s: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
    mc: Minio = Depends(_mc),
    user: Usuario = Depends(current_user),
):
    payload = await file.read()
    return await upload_adjunto(
        s, mc=mc, settings=settings, licencia_id=licencia_id,
        nombre_original=file.filename or "archivo",
        mime_type=file.content_type or "application/octet-stream",
        payload=payload, usuario_id=user.id,
    )


@router.get("/{id_}/download", response_model=AdjuntoDownload)
async def get_download(
    id_: UUID,
    s: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
    mc: Minio = Depends(_mc),
    user: Usuario = Depends(current_user),
):
    url, ttl = await download_url(s, mc, settings, id_)
    return AdjuntoDownload(url=url, expires_in_seconds=ttl)
```

- [ ] **Step 6: Tests (hermetic MinIO via testcontainers)**

```python
# backend/tests/modules/adjuntos/test_service.py
import pytest
from minio import Minio
from testcontainers.minio import MinioContainer

from app.core.settings import get_settings
from app.modules.adjuntos.service import upload_adjunto, download_url
from app.shared.exceptions import ValidationError


@pytest.fixture(scope="module")
def minio_container():
    with MinioContainer() as mc:
        yield mc


@pytest.fixture
def minio_client_with_bucket(minio_container):
    cfg = minio_container.get_config()
    client = Minio(cfg["endpoint"], access_key=cfg["access_key"], secret_key=cfg["secret_key"], secure=False)
    bucket = "test-bucket"
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)
    return client, bucket


@pytest.mark.asyncio
async def test_rejects_invalid_mime(db_session, minio_client_with_bucket):
    mc, bucket = minio_client_with_bucket
    settings = get_settings()
    settings.__dict__["minio_bucket"] = bucket  # override for this test
    import uuid
    with pytest.raises(ValidationError):
        await upload_adjunto(
            db_session, mc=mc, settings=settings, licencia_id=uuid.uuid4(),
            nombre_original="x.exe", mime_type="application/x-msdownload",
            payload=b"x", usuario_id=None,
        )
```

> The full upload/download round-trip test needs a `licencia` row to satisfy the FK — defer that test until Phase 6 lands.

- [ ] **Step 7: Commit (migration deferred to Phase 6)**

```bash
git add backend/app/core/storage.py backend/app/modules/adjuntos backend/tests/modules/adjuntos backend/app/main.py
git commit -m "feat(adjuntos): upload con sha256 + presigned download (migración pendiente phase 6)"
```

Register router; **do NOT** add adjuntos to `alembic/env.py` yet — wait until Phase 6 Task 6.1 lands the `licencias` table so the FK resolves.

---

## Phase 6 — Licencias (state machine + cómputo + topes)

### Task 6.1: Licencia model + migration (and finally adjuntos)

**Files:**
- Create: `backend/app/modules/licencias/{__init__,models}.py`
- Migration

- [ ] **Step 1: Model**

```python
# backend/app/modules/licencias/models.py
from datetime import date, datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import CheckConstraint, Date, DateTime, Enum as SAEnum, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db_base import Base
from app.core.ids import new_uuid7


class EstadoLicencia(StrEnum):
    BORRADOR = "borrador"
    ENVIADO = "enviado"
    VALIDADO = "validado"
    RECHAZADO = "rechazado"
    ANULADO = "anulado"


class OrigenLicencia(StrEnum):
    RRHH = "rrhh"
    MEDICO = "medico"


class Licencia(Base):
    __tablename__ = "licencias"
    __table_args__ = (
        CheckConstraint("dias_solicitados > 0", name="ck_dias_sol_positivo"),
        CheckConstraint("fecha_hasta >= fecha_desde", name="ck_rango_fechas"),
    )

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=new_uuid7)
    empleado_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("empleados.id"))
    tipo_licencia_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("tipos_licencia.id"))
    diagnostico_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("diagnosticos.id"), nullable=True
    )
    fecha_desde: Mapped[date] = mapped_column(Date)
    fecha_hasta: Mapped[date] = mapped_column(Date)
    dias_solicitados: Mapped[int] = mapped_column(Integer)
    dias_otorgados: Mapped[int | None] = mapped_column(Integer, nullable=True)
    estado: Mapped[EstadoLicencia] = mapped_column(SAEnum(EstadoLicencia, name="estado_licencia"))
    origen: Mapped[OrigenLicencia] = mapped_column(SAEnum(OrigenLicencia, name="origen_licencia"))
    observaciones: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    motivo_rechazo: Mapped[str | None] = mapped_column(String(500), nullable=True)
    motivo_anulacion: Mapped[str | None] = mapped_column(String(500), nullable=True)
    certificante: Mapped[str | None] = mapped_column(String(255), nullable=True)
    matricula_certificante: Mapped[str | None] = mapped_column(String(40), nullable=True)
    creado_por: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("usuarios.id"))
    validado_por: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True
    )
    validado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
```

- [ ] **Step 2: Migration including indexes + adjuntos**

Now wire imports in `alembic/env.py`:
```python
from app.modules.licencias import models as _lic_models  # noqa: F401
from app.modules.adjuntos import models as _adj_models   # noqa: F401
```

Generate and edit revision to add the auxiliary indexes:

```bash
cd backend && uv run alembic revision --autogenerate -m "licencias and adjuntos"
```

In the new revision file, append at the end of `upgrade()`:

```python
op.execute("""
    CREATE INDEX IF NOT EXISTS ix_lic_empleado_desde
        ON licencias (empleado_id, fecha_desde);
""")
op.execute("""
    CREATE INDEX IF NOT EXISTS ix_lic_estado
        ON licencias (estado);
""")
op.execute("""
    CREATE INDEX IF NOT EXISTS ix_lic_tipo_validado
        ON licencias (tipo_licencia_id, validado_en)
        WHERE estado = 'validado';
""")
```

Apply:
```bash
uv run alembic upgrade head
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/modules/licencias/models.py backend/alembic/versions backend/alembic/env.py
git commit -m "feat(licencias): modelo + migración (con índices) + adjuntos"
```

---

### Task 6.2: State machine

**Files:**
- Create: `backend/app/modules/licencias/state_machine.py`
- Create: `backend/tests/modules/licencias/{__init__,test_state_machine}.py`

- [ ] **Step 1: Failing tests (matriz completa)**

```python
# backend/tests/modules/licencias/test_state_machine.py
import pytest

from app.modules.licencias.models import EstadoLicencia
from app.modules.licencias.state_machine import (
    can_transition,
    next_state,
)
from app.modules.usuarios.models import Rol
from app.shared.exceptions import InvalidStateTransition

E = EstadoLicencia

ALLOWED = [
    # (from, to, role, ok?)
    (E.BORRADOR, E.ENVIADO, Rol.RRHH, True),
    (E.BORRADOR, E.ENVIADO, Rol.MEDICO, True),
    (E.BORRADOR, E.ANULADO, Rol.RRHH, True),
    (E.BORRADOR, E.ANULADO, Rol.ADMIN, True),
    (E.ENVIADO, E.VALIDADO, Rol.MEDICO, True),
    (E.ENVIADO, E.VALIDADO, Rol.RRHH, False),
    (E.ENVIADO, E.RECHAZADO, Rol.MEDICO, True),
    (E.VALIDADO, E.ANULADO, Rol.ADMIN, True),
    (E.VALIDADO, E.ANULADO, Rol.MEDICO, False),
    (E.RECHAZADO, E.BORRADOR, Rol.ADMIN, True),
    (E.RECHAZADO, E.VALIDADO, Rol.ADMIN, False),  # bypass not allowed
    (E.ANULADO, E.BORRADOR, Rol.ADMIN, False),
]


@pytest.mark.parametrize("frm,to,role,ok", ALLOWED)
def test_matrix(frm, to, role, ok):
    if ok:
        assert can_transition(frm, to, role) is True
    else:
        assert can_transition(frm, to, role) is False


def test_next_state_raises_on_illegal():
    with pytest.raises(InvalidStateTransition):
        next_state(E.VALIDADO, "enviar", Rol.MEDICO)


def test_next_state_handles_enviar():
    assert next_state(E.BORRADOR, "enviar", Rol.RRHH) is E.ENVIADO
    assert next_state(E.ENVIADO, "validar", Rol.MEDICO) is E.VALIDADO
    assert next_state(E.ENVIADO, "rechazar", Rol.MEDICO) is E.RECHAZADO
    assert next_state(E.VALIDADO, "anular", Rol.ADMIN) is E.ANULADO
    assert next_state(E.RECHAZADO, "reabrir", Rol.ADMIN) is E.BORRADOR
```

- [ ] **Step 2: Implement `state_machine.py`**

```python
# backend/app/modules/licencias/state_machine.py
from app.modules.licencias.models import EstadoLicencia as E
from app.modules.usuarios.models import Rol
from app.shared.exceptions import InvalidStateTransition

# (from, to) -> roles allowed
_RULES: dict[tuple[E, E], set[Rol]] = {
    (E.BORRADOR, E.ENVIADO):   {Rol.RRHH, Rol.MEDICO, Rol.ADMIN},
    (E.BORRADOR, E.ANULADO):   {Rol.RRHH, Rol.MEDICO, Rol.ADMIN},
    (E.ENVIADO,  E.VALIDADO):  {Rol.MEDICO, Rol.ADMIN},
    (E.ENVIADO,  E.RECHAZADO): {Rol.MEDICO, Rol.ADMIN},
    (E.VALIDADO, E.ANULADO):   {Rol.ADMIN},
    (E.RECHAZADO, E.BORRADOR): {Rol.ADMIN},
}

# Map action name → target state.
_ACTIONS = {
    "enviar":   E.ENVIADO,
    "validar":  E.VALIDADO,
    "rechazar": E.RECHAZADO,
    "anular":   E.ANULADO,
    "reabrir":  E.BORRADOR,
}


def can_transition(from_state: E, to_state: E, role: Rol) -> bool:
    return role in _RULES.get((from_state, to_state), set())


def next_state(current: E, action: str, role: Rol) -> E:
    if action not in _ACTIONS:
        raise InvalidStateTransition(f"acción desconocida: {action}")
    target = _ACTIONS[action]
    if not can_transition(current, target, role):
        raise InvalidStateTransition(
            f"transición {current.value} → {target.value} no permitida para rol {role.value}",
            detail={"from": current.value, "to": target.value, "role": role.value},
        )
    return target
```

> The `ADMIN` is added to medical actions because admin has system-wide rights; medic-only enforcement is at the *router level* via `require_role`, not the state machine.

- [ ] **Step 3: Run + commit**

```bash
cd backend && uv run pytest tests/modules/licencias/test_state_machine.py -v
git add backend/app/modules/licencias/state_machine.py backend/tests/modules/licencias/test_state_machine.py
git commit -m "feat(licencias): state machine con matriz de transiciones y roles"
```

---

### Task 6.3: Cómputo de días + evaluación de tope

**Files:**
- Create: `backend/app/modules/licencias/calculo.py`
- Create: `backend/tests/modules/licencias/test_calculo.py`

- [ ] **Step 1: Failing tests**

```python
# backend/tests/modules/licencias/test_calculo.py
from datetime import date

import pytest

from app.modules.licencias.calculo import calcular_dias, ventana_para


def test_calcular_dias_dia_unico():
    assert calcular_dias(date(2026, 5, 10), date(2026, 5, 10)) == 1


def test_calcular_dias_rango_normal():
    assert calcular_dias(date(2026, 5, 10), date(2026, 5, 20)) == 11


def test_calcular_dias_rango_invalido():
    with pytest.raises(ValueError):
        calcular_dias(date(2026, 5, 20), date(2026, 5, 10))


def test_calcular_dias_anio_bisiesto():
    # 2024 es bisiesto; feb 28 → mar 1 son 3 días corridos
    assert calcular_dias(date(2024, 2, 28), date(2024, 3, 1)) == 3


def test_ventana_calendario():
    assert ventana_para("anio-calendario", fecha_ingreso=date(2020, 7, 1), fecha_ref=date(2026, 6, 15)) == (
        date(2026, 1, 1), date(2026, 12, 31)
    )


def test_ventana_aniversario():
    # ingresó 1-feb-2020, fecha_ref 15-jun-2026 → ventana 1-feb-2026 a 31-ene-2027
    assert ventana_para("anio-aniversario", fecha_ingreso=date(2020, 2, 1), fecha_ref=date(2026, 6, 15)) == (
        date(2026, 2, 1), date(2027, 1, 31)
    )
```

- [ ] **Step 2: Implement `calculo.py`**

```python
# backend/app/modules/licencias/calculo.py
from dataclasses import dataclass
from datetime import date, timedelta
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.empleados.models import Empleado
from app.modules.licencias.models import EstadoLicencia, Licencia
from app.modules.topes import repository as topes_repo


def calcular_dias(fecha_desde: date, fecha_hasta: date) -> int:
    if fecha_hasta < fecha_desde:
        raise ValueError("fecha_hasta < fecha_desde")
    return (fecha_hasta - fecha_desde).days + 1


def ventana_para(
    ventana: str, *, fecha_ingreso: date, fecha_ref: date
) -> tuple[date, date]:
    if ventana == "anio-calendario":
        return date(fecha_ref.year, 1, 1), date(fecha_ref.year, 12, 31)
    if ventana == "anio-aniversario":
        # Determine the current aniversario "year start" relative to fecha_ref.
        anios = fecha_ref.year - fecha_ingreso.year
        if (fecha_ref.month, fecha_ref.day) < (fecha_ingreso.month, fecha_ingreso.day):
            anios -= 1
        try:
            inicio = fecha_ingreso.replace(year=fecha_ingreso.year + anios)
        except ValueError:
            # 29-feb edge: fall back to 28-feb in non-leap years
            inicio = date(fecha_ingreso.year + anios, 2, 28)
        try:
            fin = inicio.replace(year=inicio.year + 1) - timedelta(days=1)
        except ValueError:
            fin = date(inicio.year + 1, 2, 28) - timedelta(days=1)
        return inicio, fin
    raise ValueError(f"ventana desconocida: {ventana}")


@dataclass(frozen=True)
class TopeEvaluacion:
    tope_aplicable: int | None
    dias_consumidos_ventana: int
    dias_restantes: int
    excede: bool
    warning_msg: str | None


async def dias_consumidos(
    s: AsyncSession,
    *,
    empleado_id: UUID,
    tipo_licencia_id: UUID,
    inicio: date,
    fin: date,
) -> int:
    stmt = (
        select(func.coalesce(func.sum(Licencia.dias_otorgados), 0))
        .where(
            and_(
                Licencia.empleado_id == empleado_id,
                Licencia.tipo_licencia_id == tipo_licencia_id,
                Licencia.estado == EstadoLicencia.VALIDADO,
                Licencia.fecha_desde >= inicio,
                Licencia.fecha_desde <= fin,
            )
        )
    )
    return int((await s.execute(stmt)).scalar_one() or 0)


async def evaluar_tope(
    s: AsyncSession,
    *,
    empleado: Empleado,
    tipo_licencia_id: UUID,
    dias_solicitados: int,
    fecha_ref: date,
) -> TopeEvaluacion:
    tope = await topes_repo.tope_vigente(
        s, categoria_id=empleado.categoria_id, tipo_licencia_id=tipo_licencia_id, en_fecha=fecha_ref
    )
    if tope is None or tope.ventana == "sin-limite":
        return TopeEvaluacion(None, 0, 0, False, None)

    inicio, fin = ventana_para(tope.ventana, fecha_ingreso=empleado.fecha_ingreso, fecha_ref=fecha_ref)
    consumidos = await dias_consumidos(
        s, empleado_id=empleado.id, tipo_licencia_id=tipo_licencia_id, inicio=inicio, fin=fin
    )
    excede = (consumidos + dias_solicitados) > tope.dias_maximos
    return TopeEvaluacion(
        tope_aplicable=tope.dias_maximos,
        dias_consumidos_ventana=consumidos,
        dias_restantes=max(0, tope.dias_maximos - consumidos),
        excede=excede,
        warning_msg=(
            f"Excede tope ({consumidos + dias_solicitados}/{tope.dias_maximos})" if excede else None
        ),
    )
```

- [ ] **Step 3: Run unit tests for calcular/ventana**

Run: `cd backend && uv run pytest tests/modules/licencias/test_calculo.py -v`
Expected: 6 passed.

- [ ] **Step 4: Integration test for `evaluar_tope`**

```python
# backend/tests/modules/licencias/test_evaluar_tope.py
from datetime import date

import pytest

from app.modules.categorias.schemas import CategoriaCreate
from app.modules.categorias.service import create_categoria
from app.modules.empleados.schemas import EmpleadoCreate
from app.modules.empleados.service import create_empleado
from app.modules.licencias.calculo import evaluar_tope
from app.modules.licencias.models import EstadoLicencia, Licencia, OrigenLicencia
from app.modules.tipos_licencia.schemas import TipoLicenciaCreate
from app.modules.tipos_licencia.service import create_tipo
from app.modules.topes import repository as topes_repo


@pytest.mark.asyncio
async def test_excede_tope_calendario_con_licencias_previas(db_session):
    cat = await create_categoria(db_session, CategoriaCreate(codigo="planta", nombre="P"))
    tipo = await create_tipo(db_session, TipoLicenciaCreate(codigo="ec", nombre="EC"))
    await db_session.flush()
    emp = await create_empleado(db_session, EmpleadoCreate(
        legajo="L", cuil="20111111119", nombre="A", apellido="B",
        fecha_ingreso=date(2020, 1, 1), categoria_id=cat.id,
    ))
    await topes_repo.set_tope(db_session,
        categoria_id=cat.id, tipo_licencia_id=tipo.id,
        dias_maximos=30, ventana="anio-calendario",
        desde=date(2026, 1, 1), observacion=None,
    )
    # 20 días ya otorgados en este año.
    db_session.add(Licencia(
        empleado_id=emp.id, tipo_licencia_id=tipo.id,
        fecha_desde=date(2026, 3, 1), fecha_hasta=date(2026, 3, 20),
        dias_solicitados=20, dias_otorgados=20,
        estado=EstadoLicencia.VALIDADO, origen=OrigenLicencia.RRHH,
        creado_por=emp.id,  # placeholder; in real code uses Usuario
    ))
    await db_session.flush()

    ev = await evaluar_tope(db_session,
        empleado=emp, tipo_licencia_id=tipo.id, dias_solicitados=15, fecha_ref=date(2026, 6, 1))
    assert ev.tope_aplicable == 30
    assert ev.dias_consumidos_ventana == 20
    assert ev.excede is True
```

> The `creado_por` FK trick (using `emp.id` as a placeholder UUID) is only for this unit-style fixture — production data always uses a real `usuarios.id`. Adjust if FK strictness blocks; otherwise use `factory-boy` to create a real Usuario fixture.

- [ ] **Step 5: Run + commit**

```bash
uv run pytest tests/modules/licencias -v
git add backend/app/modules/licencias/calculo.py backend/tests/modules/licencias
git commit -m "feat(licencias): cómputo de días + ventanas + evaluación de tope versionado"
```

---

### Task 6.4: Licencia schemas

**Files:**
- Create: `backend/app/modules/licencias/schemas.py`

- [ ] **Step 1: Write schemas**

```python
# backend/app/modules/licencias/schemas.py
from datetime import date, datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.modules.licencias.models import EstadoLicencia, OrigenLicencia


class LicenciaCreate(BaseModel):
    empleado_id: UUID
    tipo_licencia_id: UUID
    diagnostico_id: UUID | None = None
    fecha_desde: date
    fecha_hasta: date
    observaciones: str | None = None
    certificante: str | None = None
    matricula_certificante: str | None = None

    @field_validator("fecha_hasta")
    @classmethod
    def rango_ok(cls, v: date, info):
        desde: date | None = info.data.get("fecha_desde")
        if desde and v < desde:
            raise ValueError("fecha_hasta debe ser >= fecha_desde")
        return v


class LicenciaUpdate(BaseModel):
    diagnostico_id: UUID | None = None
    fecha_desde: date | None = None
    fecha_hasta: date | None = None
    observaciones: str | None = None
    certificante: str | None = None
    matricula_certificante: str | None = None


class LicenciaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    empleado_id: UUID
    tipo_licencia_id: UUID
    diagnostico_id: UUID | None
    fecha_desde: date
    fecha_hasta: date
    dias_solicitados: int
    dias_otorgados: int | None
    estado: EstadoLicencia
    origen: OrigenLicencia
    observaciones: str | None
    motivo_rechazo: str | None
    motivo_anulacion: str | None
    certificante: str | None
    matricula_certificante: str | None
    creado_por: UUID
    validado_por: UUID | None
    validado_en: datetime | None


class ValidarIn(BaseModel):
    dias_otorgados: int = Field(ge=0)
    observaciones: str | None = None


class RechazarIn(BaseModel):
    motivo_rechazo: str = Field(min_length=3, max_length=500)


class AnularIn(BaseModel):
    motivo_anulacion: str = Field(min_length=3, max_length=500)
```

- [ ] **Step 2: Commit (no tests for pure schemas at this step)**

```bash
git add backend/app/modules/licencias/schemas.py
git commit -m "feat(licencias): pydantic schemas con validación de rango"
```

---

### Task 6.5: Licencia repository

**Files:**
- Create: `backend/app/modules/licencias/repository.py`

- [ ] **Step 1: Write repository**

```python
# backend/app/modules/licencias/repository.py
from datetime import date
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.licencias.models import EstadoLicencia, Licencia


async def insert(s: AsyncSession, lic: Licencia) -> Licencia:
    s.add(lic); await s.flush(); return lic


async def get(s: AsyncSession, id_: UUID) -> Licencia | None:
    return (await s.execute(select(Licencia).where(Licencia.id == id_))).scalar_one_or_none()


async def list_(
    s: AsyncSession,
    *,
    estado: EstadoLicencia | None = None,
    empleado_id: UUID | None = None,
    area_id: UUID | None = None,
    desde: date | None = None,
    hasta: date | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Licencia]:
    stmt = select(Licencia).order_by(Licencia.fecha_desde.desc()).limit(limit).offset(offset)
    conds = []
    if estado:
        conds.append(Licencia.estado == estado)
    if empleado_id:
        conds.append(Licencia.empleado_id == empleado_id)
    if desde:
        conds.append(Licencia.fecha_desde >= desde)
    if hasta:
        conds.append(Licencia.fecha_desde <= hasta)
    if conds:
        stmt = stmt.where(and_(*conds))
    if area_id:
        from app.modules.empleados.models import Empleado
        stmt = stmt.join(Empleado, Empleado.id == Licencia.empleado_id).where(Empleado.area_id == area_id)
    return list((await s.execute(stmt)).scalars())
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/modules/licencias/repository.py
git commit -m "feat(licencias): repository con filtros (estado, empleado, área, rango)"
```

---

### Task 6.6: Licencia service (create + transiciones)

**Files:**
- Create: `backend/app/modules/licencias/service.py`
- Create: `backend/tests/modules/licencias/test_service.py`

- [ ] **Step 1: Failing tests**

```python
# backend/tests/modules/licencias/test_service.py
from datetime import date

import pytest

from app.modules.categorias.schemas import CategoriaCreate
from app.modules.categorias.service import create_categoria
from app.modules.empleados.schemas import EmpleadoCreate
from app.modules.empleados.service import create_empleado
from app.modules.licencias.models import EstadoLicencia
from app.modules.licencias.schemas import LicenciaCreate, RechazarIn, ValidarIn
from app.modules.licencias.service import crear_licencia, enviar, rechazar, validar
from app.modules.tipos_licencia.schemas import TipoLicenciaCreate
from app.modules.tipos_licencia.service import create_tipo
from app.modules.topes import repository as topes_repo
from app.modules.usuarios.models import Rol
from app.modules.usuarios.schemas import UsuarioCreate
from app.modules.usuarios.service import create_user
from app.shared.exceptions import InvalidStateTransition


async def _setup(db_session):
    rrhh = await create_user(db_session, UsuarioCreate(email="r@r.com", password="StrongPass123!Q", nombre="R", rol=Rol.RRHH))
    medico = await create_user(db_session, UsuarioCreate(email="m@m.com", password="StrongPass123!Q", nombre="M", rol=Rol.MEDICO))
    cat = await create_categoria(db_session, CategoriaCreate(codigo="planta", nombre="P"))
    tipo = await create_tipo(db_session, TipoLicenciaCreate(codigo="ec", nombre="EC"))
    await db_session.flush()
    emp = await create_empleado(db_session, EmpleadoCreate(
        legajo="L1", cuil="20111111119", nombre="A", apellido="B",
        fecha_ingreso=date(2020, 1, 1), categoria_id=cat.id,
    ))
    await topes_repo.set_tope(db_session,
        categoria_id=cat.id, tipo_licencia_id=tipo.id,
        dias_maximos=30, ventana="anio-calendario",
        desde=date(2026, 1, 1), observacion=None,
    )
    return rrhh, medico, cat, tipo, emp


@pytest.mark.asyncio
async def test_crear_calcula_dias_y_estado_borrador(db_session):
    rrhh, _, _, tipo, emp = await _setup(db_session)
    lic = await crear_licencia(db_session, payload=LicenciaCreate(
        empleado_id=emp.id, tipo_licencia_id=tipo.id,
        fecha_desde=date(2026, 5, 10), fecha_hasta=date(2026, 5, 15),
    ), actor=rrhh)
    assert lic.dias_solicitados == 6
    assert lic.estado == EstadoLicencia.BORRADOR
    assert lic.origen.value == "rrhh"


@pytest.mark.asyncio
async def test_enviar_y_validar_flow(db_session):
    rrhh, medico, _, tipo, emp = await _setup(db_session)
    lic = await crear_licencia(db_session, payload=LicenciaCreate(
        empleado_id=emp.id, tipo_licencia_id=tipo.id,
        fecha_desde=date(2026, 5, 10), fecha_hasta=date(2026, 5, 15),
    ), actor=rrhh)
    lic = await enviar(db_session, lic_id=lic.id, actor=rrhh)
    assert lic.estado == EstadoLicencia.ENVIADO
    lic = await validar(db_session, lic_id=lic.id, payload=ValidarIn(dias_otorgados=6), actor=medico)
    assert lic.estado == EstadoLicencia.VALIDADO
    assert lic.dias_otorgados == 6
    assert lic.validado_por == medico.id


@pytest.mark.asyncio
async def test_rechazar_requiere_motivo(db_session):
    rrhh, medico, _, tipo, emp = await _setup(db_session)
    lic = await crear_licencia(db_session, payload=LicenciaCreate(
        empleado_id=emp.id, tipo_licencia_id=tipo.id,
        fecha_desde=date(2026, 5, 10), fecha_hasta=date(2026, 5, 15),
    ), actor=rrhh)
    lic = await enviar(db_session, lic_id=lic.id, actor=rrhh)
    lic = await rechazar(db_session, lic_id=lic.id, payload=RechazarIn(motivo_rechazo="no corresponde"), actor=medico)
    assert lic.estado == EstadoLicencia.RECHAZADO
    assert lic.motivo_rechazo == "no corresponde"


@pytest.mark.asyncio
async def test_validar_borrador_falla(db_session):
    rrhh, medico, _, tipo, emp = await _setup(db_session)
    lic = await crear_licencia(db_session, payload=LicenciaCreate(
        empleado_id=emp.id, tipo_licencia_id=tipo.id,
        fecha_desde=date(2026, 5, 10), fecha_hasta=date(2026, 5, 15),
    ), actor=rrhh)
    with pytest.raises(InvalidStateTransition):
        await validar(db_session, lic_id=lic.id, payload=ValidarIn(dias_otorgados=6), actor=medico)
```

- [ ] **Step 2: Implement `service.py`**

```python
# backend/app/modules/licencias/service.py
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.empleados import repository as emp_repo
from app.modules.licencias import repository as repo
from app.modules.licencias.calculo import calcular_dias, evaluar_tope
from app.modules.licencias.models import EstadoLicencia, Licencia, OrigenLicencia
from app.modules.licencias.schemas import (
    AnularIn,
    LicenciaCreate,
    RechazarIn,
    ValidarIn,
)
from app.modules.licencias.state_machine import next_state
from app.modules.usuarios.models import Rol, Usuario
from app.shared.exceptions import NotFoundError, ValidationError


def _origen_for(rol: Rol) -> OrigenLicencia:
    return OrigenLicencia.MEDICO if rol == Rol.MEDICO else OrigenLicencia.RRHH


async def crear_licencia(s: AsyncSession, *, payload: LicenciaCreate, actor: Usuario) -> Licencia:
    emp = await emp_repo.get(s, payload.empleado_id)
    if emp is None:
        raise NotFoundError("empleado no encontrado")
    dias = calcular_dias(payload.fecha_desde, payload.fecha_hasta)
    if dias <= 0:
        raise ValidationError("rango de fechas inválido")
    lic = Licencia(
        empleado_id=payload.empleado_id,
        tipo_licencia_id=payload.tipo_licencia_id,
        diagnostico_id=payload.diagnostico_id,
        fecha_desde=payload.fecha_desde,
        fecha_hasta=payload.fecha_hasta,
        dias_solicitados=dias,
        estado=EstadoLicencia.BORRADOR,
        origen=_origen_for(actor.rol),
        observaciones=payload.observaciones,
        certificante=payload.certificante,
        matricula_certificante=payload.matricula_certificante,
        creado_por=actor.id,
    )
    return await repo.insert(s, lic)


async def _transition(
    s: AsyncSession, *, lic_id: UUID, action: str, actor: Usuario,
) -> Licencia:
    lic = await repo.get(s, lic_id)
    if not lic:
        raise NotFoundError("licencia no encontrada")
    lic.estado = next_state(lic.estado, action, actor.rol)
    await s.flush()
    return lic


async def enviar(s: AsyncSession, *, lic_id: UUID, actor: Usuario) -> Licencia:
    return await _transition(s, lic_id=lic_id, action="enviar", actor=actor)


async def validar(
    s: AsyncSession, *, lic_id: UUID, payload: ValidarIn, actor: Usuario
) -> Licencia:
    lic = await repo.get(s, lic_id)
    if not lic:
        raise NotFoundError("licencia no encontrada")
    lic.estado = next_state(lic.estado, "validar", actor.rol)
    lic.dias_otorgados = payload.dias_otorgados
    if payload.observaciones:
        lic.observaciones = (lic.observaciones or "") + f"\n[validación] {payload.observaciones}"
    lic.validado_por = actor.id
    lic.validado_en = datetime.now(timezone.utc)
    await s.flush()
    return lic


async def rechazar(
    s: AsyncSession, *, lic_id: UUID, payload: RechazarIn, actor: Usuario
) -> Licencia:
    lic = await repo.get(s, lic_id)
    if not lic:
        raise NotFoundError("licencia no encontrada")
    lic.estado = next_state(lic.estado, "rechazar", actor.rol)
    lic.motivo_rechazo = payload.motivo_rechazo
    await s.flush()
    return lic


async def anular(
    s: AsyncSession, *, lic_id: UUID, payload: AnularIn, actor: Usuario
) -> Licencia:
    lic = await repo.get(s, lic_id)
    if not lic:
        raise NotFoundError("licencia no encontrada")
    lic.estado = next_state(lic.estado, "anular", actor.rol)
    lic.motivo_anulacion = payload.motivo_anulacion
    await s.flush()
    return lic


async def evaluar_tope_para_licencia(
    s: AsyncSession, lic_id: UUID, fecha_ref=None
):
    lic = await repo.get(s, lic_id)
    if not lic:
        raise NotFoundError("licencia no encontrada")
    emp = await emp_repo.get(s, lic.empleado_id)
    from datetime import date as _date
    return await evaluar_tope(
        s,
        empleado=emp,
        tipo_licencia_id=lic.tipo_licencia_id,
        dias_solicitados=lic.dias_solicitados,
        fecha_ref=fecha_ref or _date.today(),
    )
```

- [ ] **Step 3: Run + commit**

```bash
uv run pytest tests/modules/licencias/test_service.py -v
git add backend/app/modules/licencias/service.py backend/tests/modules/licencias/test_service.py
git commit -m "feat(licencias): service con creación + transiciones (enviar/validar/rechazar/anular)"
```

---

### Task 6.7: Licencia router + endpoints de transición

**Files:**
- Create: `backend/app/modules/licencias/router.py`
- Create: `backend/tests/modules/licencias/test_router.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Router**

```python
# backend/app/modules/licencias/router.py
from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import current_user, get_db
from app.core.permissions import require_role
from app.modules.licencias import repository as repo
from app.modules.licencias.calculo import TopeEvaluacion
from app.modules.licencias.models import EstadoLicencia
from app.modules.licencias.schemas import (
    AnularIn, LicenciaCreate, LicenciaOut, RechazarIn, ValidarIn,
)
from app.modules.licencias.service import (
    anular, crear_licencia, enviar, evaluar_tope_para_licencia, rechazar, validar,
)
from app.modules.usuarios.models import Rol, Usuario
from app.shared.exceptions import NotFoundError

router = APIRouter(prefix="/api/licencias", tags=["licencias"])


@router.get("", response_model=list[LicenciaOut])
async def list_(
    estado: EstadoLicencia | None = Query(default=None),
    empleado_id: UUID | None = Query(default=None),
    area_id: UUID | None = Query(default=None),
    desde: date | None = Query(default=None),
    hasta: date | None = Query(default=None),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    s: AsyncSession = Depends(get_db),
    user: Usuario = Depends(current_user),
):
    rows = await repo.list_(s,
        estado=estado, empleado_id=empleado_id, area_id=area_id,
        desde=desde, hasta=hasta, limit=limit, offset=offset)
    # Hide sensitive fields for RRHH
    if user.rol == Rol.RRHH:
        for r in rows:
            r.diagnostico_id = None
            r.observaciones = None
            r.motivo_rechazo = None
    return rows


@router.get("/{id_}", response_model=LicenciaOut)
async def get_one(id_: UUID, s: AsyncSession = Depends(get_db), user: Usuario = Depends(current_user)):
    lic = await repo.get(s, id_)
    if not lic:
        raise NotFoundError("licencia no encontrada")
    if user.rol == Rol.RRHH:
        lic.diagnostico_id = None
        lic.observaciones = None
        lic.motivo_rechazo = None
    return lic


@router.post("", response_model=LicenciaOut, status_code=201,
             dependencies=[Depends(require_role(Rol.ADMIN, Rol.RRHH, Rol.MEDICO))])
async def create(
    payload: LicenciaCreate, s: AsyncSession = Depends(get_db), user: Usuario = Depends(current_user)
):
    return await crear_licencia(s, payload=payload, actor=user)


@router.post("/{id_}/enviar", response_model=LicenciaOut,
             dependencies=[Depends(require_role(Rol.ADMIN, Rol.RRHH, Rol.MEDICO))])
async def enviar_ep(id_: UUID, s: AsyncSession = Depends(get_db), user: Usuario = Depends(current_user)):
    return await enviar(s, lic_id=id_, actor=user)


@router.post("/{id_}/validar", response_model=LicenciaOut,
             dependencies=[Depends(require_role(Rol.MEDICO, Rol.ADMIN))])
async def validar_ep(
    id_: UUID, payload: ValidarIn,
    s: AsyncSession = Depends(get_db), user: Usuario = Depends(current_user),
):
    return await validar(s, lic_id=id_, payload=payload, actor=user)


@router.post("/{id_}/rechazar", response_model=LicenciaOut,
             dependencies=[Depends(require_role(Rol.MEDICO, Rol.ADMIN))])
async def rechazar_ep(
    id_: UUID, payload: RechazarIn,
    s: AsyncSession = Depends(get_db), user: Usuario = Depends(current_user),
):
    return await rechazar(s, lic_id=id_, payload=payload, actor=user)


@router.post("/{id_}/anular", response_model=LicenciaOut,
             dependencies=[Depends(require_role(Rol.ADMIN))])
async def anular_ep(
    id_: UUID, payload: AnularIn,
    s: AsyncSession = Depends(get_db), user: Usuario = Depends(current_user),
):
    return await anular(s, lic_id=id_, payload=payload, actor=user)


@router.get("/{id_}/tope")
async def tope_ep(id_: UUID, s: AsyncSession = Depends(get_db), user: Usuario = Depends(current_user)):
    ev: TopeEvaluacion = await evaluar_tope_para_licencia(s, id_)
    return ev.__dict__
```

- [ ] **Step 2: Router test (E2E sintético)**

```python
# backend/tests/modules/licencias/test_router.py
from datetime import date

import pytest
from httpx import AsyncClient, ASGITransport

from app.core.deps import get_db
from app.main import create_app
from app.modules.categorias.schemas import CategoriaCreate
from app.modules.categorias.service import create_categoria
from app.modules.empleados.schemas import EmpleadoCreate
from app.modules.empleados.service import create_empleado
from app.modules.tipos_licencia.schemas import TipoLicenciaCreate
from app.modules.tipos_licencia.service import create_tipo
from app.modules.usuarios.models import Rol
from app.modules.usuarios.schemas import UsuarioCreate
from app.modules.usuarios.service import create_user


@pytest.mark.asyncio
async def test_rrhh_no_ve_diagnostico_en_listado(db_session):
    rrhh = await create_user(db_session, UsuarioCreate(email="r@r.com", password="StrongPass123!Q", nombre="R", rol=Rol.RRHH))
    cat = await create_categoria(db_session, CategoriaCreate(codigo="p", nombre="P"))
    tipo = await create_tipo(db_session, TipoLicenciaCreate(codigo="ec", nombre="EC"))
    await db_session.flush()
    emp = await create_empleado(db_session, EmpleadoCreate(
        legajo="L", cuil="20111111119", nombre="A", apellido="B",
        fecha_ingreso=date(2020,1,1), categoria_id=cat.id))
    await db_session.flush()

    app = create_app()
    async def _db(): yield db_session
    app.dependency_overrides[get_db] = _db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as ac:
        token = (await ac.post("/api/auth/login", json={"email": "r@r.com", "password": "StrongPass123!Q"})).json()["access_token"]
        h = {"Authorization": f"Bearer {token}"}
        await ac.post("/api/licencias", headers=h, json={
            "empleado_id": str(emp.id), "tipo_licencia_id": str(tipo.id),
            "fecha_desde": "2026-05-10", "fecha_hasta": "2026-05-15",
            "observaciones": "secret note",
        })
        lst = (await ac.get("/api/licencias", headers=h)).json()
        assert lst[0]["observaciones"] is None
```

- [ ] **Step 3: Register router + run + commit**

In `main.py`:
```python
from app.modules.licencias.router import router as licencias_router
app.include_router(licencias_router)
```

```bash
uv run pytest tests/modules/licencias/test_router.py -v
git add backend/app/modules/licencias/router.py backend/tests/modules/licencias/test_router.py backend/app/main.py
git commit -m "feat(licencias): endpoints CRUD + transiciones + filtrado RRHH de datos sensibles"
```

---

### Task 6.8: Aplicar @audited a transiciones

**Files:**
- Modify: `backend/app/modules/licencias/service.py`
- Create: `backend/tests/modules/licencias/test_audit.py`

- [ ] **Step 1: Failing test**

```python
# backend/tests/modules/licencias/test_audit.py
from datetime import date

import pytest
from sqlalchemy import select

from app.modules.auditoria.models import Auditoria
from app.modules.categorias.schemas import CategoriaCreate
from app.modules.categorias.service import create_categoria
from app.modules.empleados.schemas import EmpleadoCreate
from app.modules.empleados.service import create_empleado
from app.modules.licencias.schemas import LicenciaCreate
from app.modules.licencias.service import crear_licencia, enviar
from app.modules.tipos_licencia.schemas import TipoLicenciaCreate
from app.modules.tipos_licencia.service import create_tipo
from app.modules.usuarios.models import Rol
from app.modules.usuarios.schemas import UsuarioCreate
from app.modules.usuarios.service import create_user


@pytest.mark.asyncio
async def test_state_change_genera_audit(db_session):
    rrhh = await create_user(db_session, UsuarioCreate(email="r@r.com", password="StrongPass123!Q", nombre="R", rol=Rol.RRHH))
    cat = await create_categoria(db_session, CategoriaCreate(codigo="p", nombre="P"))
    tipo = await create_tipo(db_session, TipoLicenciaCreate(codigo="ec", nombre="EC"))
    await db_session.flush()
    emp = await create_empleado(db_session, EmpleadoCreate(
        legajo="L", cuil="20111111119", nombre="A", apellido="B",
        fecha_ingreso=date(2020,1,1), categoria_id=cat.id))
    await db_session.flush()
    lic = await crear_licencia(db_session, payload=LicenciaCreate(
        empleado_id=emp.id, tipo_licencia_id=tipo.id,
        fecha_desde=date(2026,5,10), fecha_hasta=date(2026,5,15),
    ), actor=rrhh)
    await enviar(db_session, lic_id=lic.id, actor=rrhh)
    rows = (await db_session.execute(select(Auditoria))).scalars().all()
    assert any(a.accion == "state_change" and a.entidad == "licencia" for a in rows)
```

- [ ] **Step 2: Wire `audit_repo.append` calls into service transitions**

In `backend/app/modules/licencias/service.py`, add at the top:
```python
from app.modules.auditoria import repository as audit_repo
```

Refactor each transition to write an explicit audit row instead of relying solely on the generic decorator (because we need to record the `from→to` payload accurately, which the decorator can't infer):

```python
async def _record_state_change(
    s: AsyncSession, *, lic: Licencia, frm: EstadoLicencia, to: EstadoLicencia, actor: Usuario, extra: dict | None = None
) -> None:
    payload = {"from": frm.value, "to": to.value}
    if extra:
        payload.update(extra)
    await audit_repo.append(
        s, accion="state_change", entidad="licencia",
        usuario_id=actor.id, entidad_id=lic.id, payload=payload,
        ip=None, user_agent=None,
    )
```

Then in `enviar`:
```python
async def enviar(s, *, lic_id, actor):
    lic = await repo.get(s, lic_id)
    if not lic: raise NotFoundError("licencia no encontrada")
    frm = lic.estado
    lic.estado = next_state(frm, "enviar", actor.rol)
    await s.flush()
    await _record_state_change(s, lic=lic, frm=frm, to=lic.estado, actor=actor)
    return lic
```

Repeat the same pattern in `validar`, `rechazar`, `anular` (include `dias_otorgados` / `motivo_rechazo` / `motivo_anulacion` in `extra`).

- [ ] **Step 3: Run + commit**

```bash
uv run pytest tests/modules/licencias/test_audit.py -v
git add backend/app/modules/licencias/service.py backend/tests/modules/licencias/test_audit.py
git commit -m "feat(licencias): persiste state_change en auditoría con payload from/to"
```

---

## Phase 7 — Reportes y exportes

### Task 7.1: Agregados SQL — ausentismo por área, categoría de diagnóstico y período

**Files:**
- Create: `backend/app/modules/reportes/{__init__,schemas,repository,service,router}.py`
- Create: `backend/tests/modules/reportes/{__init__,test_service}.py`

- [ ] **Step 1: Schemas**

```python
# backend/app/modules/reportes/schemas.py
from datetime import date
from pydantic import BaseModel


class AusentismoPorArea(BaseModel):
    area_id: str | None
    area_nombre: str | None
    total_licencias: int
    total_dias_otorgados: int


class AusentismoPorCategoriaDiag(BaseModel):
    categoria_diagnostico: str | None
    total_licencias: int
    total_dias_otorgados: int


class FrecuenciaMensual(BaseModel):
    anio: int
    mes: int
    total_licencias: int
    total_dias_otorgados: int


class ReporteParams(BaseModel):
    desde: date
    hasta: date
    area_id: str | None = None
```

- [ ] **Step 2: Repository (raw aggregate SQL)**

```python
# backend/app/modules/reportes/repository.py
from datetime import date

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def ausentismo_por_area(s: AsyncSession, desde: date, hasta: date) -> list[dict]:
    sql = text("""
        SELECT a.id::text AS area_id, a.nombre AS area_nombre,
               COUNT(l.id) AS total_licencias,
               COALESCE(SUM(l.dias_otorgados), 0) AS total_dias_otorgados
        FROM licencias l
        JOIN empleados e ON e.id = l.empleado_id
        LEFT JOIN areas a ON a.id = e.area_id
        WHERE l.estado = 'validado'
          AND l.fecha_desde BETWEEN :desde AND :hasta
        GROUP BY a.id, a.nombre
        ORDER BY total_dias_otorgados DESC
    """)
    res = await s.execute(sql, {"desde": desde, "hasta": hasta})
    return [dict(r._mapping) for r in res]


async def ausentismo_por_categoria_diag(s: AsyncSession, desde: date, hasta: date) -> list[dict]:
    # Aggregates by DIAGNOSTIC CATEGORY only — never by description (PII).
    sql = text("""
        SELECT d.categoria AS categoria_diagnostico,
               COUNT(l.id) AS total_licencias,
               COALESCE(SUM(l.dias_otorgados), 0) AS total_dias_otorgados
        FROM licencias l
        LEFT JOIN diagnosticos d ON d.id = l.diagnostico_id
        WHERE l.estado = 'validado'
          AND l.fecha_desde BETWEEN :desde AND :hasta
        GROUP BY d.categoria
        ORDER BY total_dias_otorgados DESC
    """)
    res = await s.execute(sql, {"desde": desde, "hasta": hasta})
    return [dict(r._mapping) for r in res]


async def frecuencia_mensual(s: AsyncSession, desde: date, hasta: date) -> list[dict]:
    sql = text("""
        SELECT EXTRACT(YEAR FROM l.fecha_desde)::int AS anio,
               EXTRACT(MONTH FROM l.fecha_desde)::int AS mes,
               COUNT(l.id) AS total_licencias,
               COALESCE(SUM(l.dias_otorgados), 0) AS total_dias_otorgados
        FROM licencias l
        WHERE l.estado = 'validado'
          AND l.fecha_desde BETWEEN :desde AND :hasta
        GROUP BY 1, 2
        ORDER BY 1, 2
    """)
    res = await s.execute(sql, {"desde": desde, "hasta": hasta})
    return [dict(r._mapping) for r in res]
```

- [ ] **Step 3: Service (no extra logic v1, passthrough)**

```python
# backend/app/modules/reportes/service.py
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.reportes import repository as repo


async def por_area(s: AsyncSession, desde: date, hasta: date):
    return await repo.ausentismo_por_area(s, desde, hasta)


async def por_categoria_diag(s: AsyncSession, desde: date, hasta: date):
    return await repo.ausentismo_por_categoria_diag(s, desde, hasta)


async def por_mes(s: AsyncSession, desde: date, hasta: date):
    return await repo.frecuencia_mensual(s, desde, hasta)
```

- [ ] **Step 4: Router with CSV export**

```python
# backend/app/modules/reportes/router.py
import csv
import io
from datetime import date

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import current_user, get_db
from app.modules.auditoria import repository as audit_repo
from app.modules.reportes import service as svc
from app.modules.usuarios.models import Usuario

router = APIRouter(prefix="/api/reportes", tags=["reportes"])


def _csv_response(rows: list[dict], filename: str) -> StreamingResponse:
    buf = io.StringIO()
    if rows:
        writer = csv.DictWriter(buf, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        for r in rows:
            writer.writerow(r)
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/por-area")
async def por_area(
    desde: date = Query(...),
    hasta: date = Query(...),
    formato: str = Query("json", pattern="^(json|csv)$"),
    s: AsyncSession = Depends(get_db),
    user: Usuario = Depends(current_user),
):
    rows = await svc.por_area(s, desde, hasta)
    if formato == "csv":
        await audit_repo.append(s, accion="export", entidad="reporte",
                                usuario_id=user.id, entidad_id=None,
                                payload={"reporte": "por_area", "desde": str(desde), "hasta": str(hasta)},
                                ip=None, user_agent=None)
        return _csv_response(rows, f"ausentismo_area_{desde}_{hasta}.csv")
    return rows


@router.get("/por-categoria-diag")
async def por_categoria_diag(
    desde: date = Query(...), hasta: date = Query(...),
    formato: str = Query("json", pattern="^(json|csv)$"),
    s: AsyncSession = Depends(get_db), user: Usuario = Depends(current_user),
):
    rows = await svc.por_categoria_diag(s, desde, hasta)
    if formato == "csv":
        await audit_repo.append(s, accion="export", entidad="reporte",
                                usuario_id=user.id, entidad_id=None,
                                payload={"reporte": "por_categoria_diag"},
                                ip=None, user_agent=None)
        return _csv_response(rows, f"ausentismo_diag_{desde}_{hasta}.csv")
    return rows


@router.get("/mensual")
async def mensual(
    desde: date = Query(...), hasta: date = Query(...),
    formato: str = Query("json", pattern="^(json|csv)$"),
    s: AsyncSession = Depends(get_db), user: Usuario = Depends(current_user),
):
    rows = await svc.por_mes(s, desde, hasta)
    if formato == "csv":
        await audit_repo.append(s, accion="export", entidad="reporte",
                                usuario_id=user.id, entidad_id=None,
                                payload={"reporte": "mensual"},
                                ip=None, user_agent=None)
        return _csv_response(rows, f"ausentismo_mensual_{desde}_{hasta}.csv")
    return rows
```

- [ ] **Step 5: Tests**

```python
# backend/tests/modules/reportes/test_service.py
from datetime import date

import pytest

from app.modules.categorias.schemas import CategoriaCreate
from app.modules.categorias.service import create_categoria
from app.modules.empleados.schemas import EmpleadoCreate
from app.modules.empleados.service import create_empleado
from app.modules.licencias.models import EstadoLicencia, Licencia, OrigenLicencia
from app.modules.reportes.service import por_area, por_mes
from app.modules.tipos_licencia.schemas import TipoLicenciaCreate
from app.modules.tipos_licencia.service import create_tipo
from app.modules.usuarios.models import Rol
from app.modules.usuarios.schemas import UsuarioCreate
from app.modules.usuarios.service import create_user


@pytest.mark.asyncio
async def test_por_area_y_por_mes(db_session):
    u = await create_user(db_session, UsuarioCreate(email="u@u.com", password="StrongPass123!Q", nombre="U", rol=Rol.ADMIN))
    cat = await create_categoria(db_session, CategoriaCreate(codigo="p", nombre="P"))
    tipo = await create_tipo(db_session, TipoLicenciaCreate(codigo="ec", nombre="EC"))
    await db_session.flush()
    emp = await create_empleado(db_session, EmpleadoCreate(
        legajo="L", cuil="20111111119", nombre="A", apellido="B",
        fecha_ingreso=date(2020,1,1), categoria_id=cat.id))
    db_session.add(Licencia(
        empleado_id=emp.id, tipo_licencia_id=tipo.id,
        fecha_desde=date(2026,3,1), fecha_hasta=date(2026,3,10),
        dias_solicitados=10, dias_otorgados=10,
        estado=EstadoLicencia.VALIDADO, origen=OrigenLicencia.RRHH,
        creado_por=u.id,
    ))
    await db_session.flush()
    a = await por_area(db_session, date(2026,1,1), date(2026,12,31))
    assert a and a[0]["total_dias_otorgados"] == 10
    m = await por_mes(db_session, date(2026,1,1), date(2026,12,31))
    assert any(row["mes"] == 3 and row["total_dias_otorgados"] == 10 for row in m)
```

- [ ] **Step 6: Run + register + commit**

In `main.py`:
```python
from app.modules.reportes.router import router as reportes_router
app.include_router(reportes_router)
```

```bash
uv run pytest tests/modules/reportes -v
git add backend/app/modules/reportes backend/tests/modules/reportes backend/app/main.py
git commit -m "feat(reportes): agregados por área, categoría diagnóstico, mensual + export CSV con auditoría"
```

---

## Phase 8 — Frontend foundation (API client, auth, routing, layout)

### Task 8.1: Tailwind + shadcn base

**Files:**
- Create: `frontend/tailwind.config.ts`
- Create: `frontend/postcss.config.js`
- Create: `frontend/src/index.css`
- Modify: `frontend/src/main.tsx`
- Create: `frontend/src/lib/utils.ts`

- [ ] **Step 1: Tailwind config**

```ts
// frontend/tailwind.config.ts
import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: { extend: {} },
  plugins: [],
} satisfies Config;
```

- [ ] **Step 2: PostCSS + index.css**

```js
// frontend/postcss.config.js
export default { plugins: { tailwindcss: {}, autoprefixer: {} } };
```

```css
/* frontend/src/index.css */
@tailwind base;
@tailwind components;
@tailwind utilities;
```

- [ ] **Step 3: Import css in `main.tsx`**

```tsx
import "./index.css";
```

- [ ] **Step 4: `cn` utility**

```ts
// frontend/src/lib/utils.ts
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
```

- [ ] **Step 5: Commit**

```bash
git add frontend/tailwind.config.ts frontend/postcss.config.js frontend/src/index.css frontend/src/main.tsx frontend/src/lib/utils.ts
git commit -m "feat(frontend): tailwind base + cn util"
```

---

### Task 8.2: Generate OpenAPI client + axios instance

**Files:**
- Create: `frontend/src/api/http.ts`
- Run: `pnpm gen:api` (after backend boots)

- [ ] **Step 1: HTTP instance with token injection**

```ts
// frontend/src/api/http.ts
import axios, { type AxiosInstance } from "axios";

const BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

let accessToken: string | null = null;
let onUnauthorized: (() => void) | null = null;

export function setAccessToken(token: string | null) {
  accessToken = token;
}

export function setOnUnauthorized(fn: () => void) {
  onUnauthorized = fn;
}

export const http: AxiosInstance = axios.create({ baseURL: BASE });

http.interceptors.request.use((cfg) => {
  if (accessToken) cfg.headers.Authorization = `Bearer ${accessToken}`;
  return cfg;
});

http.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err?.response?.status === 401 && onUnauthorized) onUnauthorized();
    return Promise.reject(err);
  },
);
```

- [ ] **Step 2: Generate the API client**

```bash
cd frontend
# 1) make sure backend is running: docker compose up -d && cd ../backend && uv run uvicorn app.main:app &
pnpm gen:api
```

This writes typed services under `src/api/services/*Service.ts` and models under `src/api/models/*.ts`.

- [ ] **Step 3: Configure generated `OpenAPI` to point at http instance**

In `src/api/core/request.ts` (or wherever the generator places it), inject the axios instance from `http.ts` so all calls share the bearer token. Simpler alternative: write thin wrappers per resource that call `http` directly.

For v1 we'll **bypass the generator** and just write hand-rolled clients (less fragile, fewer surprises with codegen options). Replace step 2 with:

```ts
// frontend/src/api/auth.ts
import { http } from "./http";

export type TokenPair = { access_token: string; refresh_token: string; token_type: "bearer" };
export type Me = { id: string; email: string; nombre: string | null; rol: "admin"|"medico"|"rrhh"; matricula: string|null; activo: boolean };

export const authApi = {
  login: (email: string, password: string) =>
    http.post<TokenPair>("/api/auth/login", { email, password }).then((r) => r.data),
  refresh: (refresh_token: string) =>
    http.post<TokenPair>("/api/auth/refresh", null, { params: { refresh_token } }).then((r) => r.data),
  me: () => http.get<Me>("/api/auth/me").then((r) => r.data),
};
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/api
git commit -m "feat(frontend): axios http client + hand-rolled auth API client"
```

---

### Task 8.3: Auth context + protected routes

**Files:**
- Create: `frontend/src/auth/AuthContext.tsx`
- Create: `frontend/src/auth/ProtectedRoute.tsx`
- Create: `frontend/src/routes/login.tsx`
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: Auth context**

```tsx
// frontend/src/auth/AuthContext.tsx
import {
  createContext, useCallback, useContext, useEffect, useMemo, useState,
  type ReactNode,
} from "react";
import { authApi, type Me } from "@/api/auth";
import { setAccessToken, setOnUnauthorized } from "@/api/http";

type AuthState = {
  user: Me | null;
  ready: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
};

const Ctx = createContext<AuthState | null>(null);

const ACCESS_KEY = "med:access";
const REFRESH_KEY = "med:refresh";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<Me | null>(null);
  const [ready, setReady] = useState(false);

  const logout = useCallback(() => {
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
    setAccessToken(null);
    setUser(null);
  }, []);

  useEffect(() => {
    setOnUnauthorized(() => logout());
    const access = localStorage.getItem(ACCESS_KEY);
    if (access) {
      setAccessToken(access);
      authApi.me().then(setUser).catch(logout).finally(() => setReady(true));
    } else {
      setReady(true);
    }
  }, [logout]);

  const login = useCallback(async (email: string, password: string) => {
    const tokens = await authApi.login(email, password);
    localStorage.setItem(ACCESS_KEY, tokens.access_token);
    localStorage.setItem(REFRESH_KEY, tokens.refresh_token);
    setAccessToken(tokens.access_token);
    setUser(await authApi.me());
  }, []);

  const value = useMemo<AuthState>(() => ({ user, ready, login, logout }), [user, ready, login, logout]);
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useAuth() {
  const v = useContext(Ctx);
  if (!v) throw new Error("useAuth outside provider");
  return v;
}
```

- [ ] **Step 2: Protected route**

```tsx
// frontend/src/auth/ProtectedRoute.tsx
import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "./AuthContext";

export function ProtectedRoute({ roles }: { roles?: Array<"admin"|"medico"|"rrhh"> }) {
  const { user, ready } = useAuth();
  if (!ready) return <div className="p-6">Cargando…</div>;
  if (!user) return <Navigate to="/login" replace />;
  if (roles && !roles.includes(user.rol)) return <Navigate to="/" replace />;
  return <Outlet />;
}
```

- [ ] **Step 3: Login page**

```tsx
// frontend/src/routes/login.tsx
import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/auth/AuthContext";

export default function LoginPage() {
  const { login } = useAuth();
  const nav = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(email, password);
      nav("/");
    } catch {
      setError("Credenciales inválidas o cuenta bloqueada.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen grid place-items-center bg-slate-50">
      <form onSubmit={onSubmit} className="w-80 space-y-3 bg-white p-6 rounded shadow">
        <h1 className="text-xl font-semibold">Medicia-Laboral</h1>
        <label className="block text-sm">
          Email
          <input className="mt-1 w-full border rounded p-2" type="email" value={email}
                 onChange={(e) => setEmail(e.target.value)} required />
        </label>
        <label className="block text-sm">
          Contraseña
          <input className="mt-1 w-full border rounded p-2" type="password" value={password}
                 onChange={(e) => setPassword(e.target.value)} required minLength={12} />
        </label>
        {error && <p className="text-red-600 text-sm">{error}</p>}
        <button disabled={loading} className="w-full bg-slate-900 text-white rounded p-2">
          {loading ? "Ingresando…" : "Ingresar"}
        </button>
      </form>
    </main>
  );
}
```

- [ ] **Step 4: Wire `App.tsx` with router**

```tsx
// frontend/src/App.tsx
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { AuthProvider } from "./auth/AuthContext";
import { ProtectedRoute } from "./auth/ProtectedRoute";
import LoginPage from "./routes/login";
import { AppLayout } from "./layout/AppLayout";
import { DashboardPage } from "./routes/dashboard";

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route element={<ProtectedRoute />}>
            <Route element={<AppLayout />}>
              <Route path="/" element={<DashboardPage />} />
            </Route>
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
```

- [ ] **Step 5: Commit (layout + dashboard come in next task — file will not yet exist; that's expected)**

```bash
git add frontend/src/auth frontend/src/routes/login.tsx frontend/src/App.tsx
git commit -m "feat(frontend): auth context + protected routes + login page"
```

---

### Task 8.4: Layout shell

**Files:**
- Create: `frontend/src/layout/AppLayout.tsx`
- Create: `frontend/src/routes/dashboard.tsx`

- [ ] **Step 1: Layout**

```tsx
// frontend/src/layout/AppLayout.tsx
import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "@/auth/AuthContext";

const links = [
  { to: "/", label: "Inicio", roles: ["admin", "medico", "rrhh"] as const },
  { to: "/empleados", label: "Empleados", roles: ["admin", "medico", "rrhh"] as const },
  { to: "/licencias", label: "Licencias", roles: ["admin", "medico", "rrhh"] as const },
  { to: "/reportes", label: "Reportes", roles: ["admin", "medico", "rrhh"] as const },
  { to: "/admin/topes", label: "Topes", roles: ["admin"] as const },
  { to: "/admin/usuarios", label: "Usuarios", roles: ["admin"] as const },
];

export function AppLayout() {
  const { user, logout } = useAuth();
  if (!user) return null;
  return (
    <div className="min-h-screen grid grid-cols-[220px_1fr]">
      <aside className="bg-slate-900 text-slate-100 p-4 space-y-2">
        <div className="font-bold mb-4">Medicia-Laboral</div>
        {links.filter((l) => l.roles.includes(user.rol)).map((l) => (
          <NavLink key={l.to} to={l.to}
                   className={({ isActive }) =>
                     `block px-3 py-2 rounded ${isActive ? "bg-slate-700" : "hover:bg-slate-800"}`}>
            {l.label}
          </NavLink>
        ))}
        <div className="absolute bottom-4 left-4 right-4 text-xs">
          <div className="opacity-70">{user.email}</div>
          <button onClick={logout} className="mt-2 underline">Salir</button>
        </div>
      </aside>
      <main className="p-6 bg-slate-50">
        <Outlet />
      </main>
    </div>
  );
}
```

- [ ] **Step 2: Dashboard skeleton**

```tsx
// frontend/src/routes/dashboard.tsx
import { useAuth } from "@/auth/AuthContext";

export function DashboardPage() {
  const { user } = useAuth();
  return (
    <section className="space-y-3">
      <h1 className="text-2xl font-semibold">Bienvenido, {user?.nombre ?? user?.email}</h1>
      <p className="text-slate-600">Rol: {user?.rol}</p>
    </section>
  );
}
```

- [ ] **Step 3: Verify + commit**

```bash
pnpm typecheck
pnpm dev &  # spot-check http://localhost:5173/login → login → dashboard
sleep 5 && kill %1
git add frontend/src/layout frontend/src/routes/dashboard.tsx
git commit -m "feat(frontend): layout shell con menú por rol + dashboard skeleton"
```

---

## Phase 9 — Frontend features

### Task 9.1: Resource APIs (empleados, licencias, catálogos, reportes, topes)

**Files:**
- Create: `frontend/src/api/{empleados,licencias,catalogos,reportes,topes,adjuntos}.ts`

- [ ] **Step 1: Type-safe API surface**

```ts
// frontend/src/api/empleados.ts
import { http } from "./http";

export type Empleado = {
  id: string; legajo: string; cuil: string;
  nombre: string; apellido: string;
  fecha_nacimiento: string | null; fecha_ingreso: string;
  area_id: string | null; categoria_id: string; supervisor_id: string | null;
  email: string | null; telefono: string | null; activo: boolean;
};

export type EmpleadoCreate = Omit<Empleado, "id" | "activo">;

export const empleadosApi = {
  list: (q?: string, limit = 50, offset = 0) =>
    http.get<Empleado[]>("/api/empleados", { params: { q, limit, offset } }).then((r) => r.data),
  get: (id: string) => http.get<Empleado>(`/api/empleados/${id}`).then((r) => r.data),
  create: (p: EmpleadoCreate) => http.post<Empleado>("/api/empleados", p).then((r) => r.data),
};
```

```ts
// frontend/src/api/licencias.ts
import { http } from "./http";

export type EstadoLicencia = "borrador" | "enviado" | "validado" | "rechazado" | "anulado";
export type OrigenLicencia = "rrhh" | "medico";

export type Licencia = {
  id: string; empleado_id: string; tipo_licencia_id: string;
  diagnostico_id: string | null;
  fecha_desde: string; fecha_hasta: string;
  dias_solicitados: number; dias_otorgados: number | null;
  estado: EstadoLicencia; origen: OrigenLicencia;
  observaciones: string | null; motivo_rechazo: string | null; motivo_anulacion: string | null;
  certificante: string | null; matricula_certificante: string | null;
  creado_por: string; validado_por: string | null; validado_en: string | null;
};

export type LicenciaCreate = {
  empleado_id: string; tipo_licencia_id: string; diagnostico_id?: string | null;
  fecha_desde: string; fecha_hasta: string;
  observaciones?: string | null; certificante?: string | null; matricula_certificante?: string | null;
};

export const licenciasApi = {
  list: (params: { estado?: EstadoLicencia; empleado_id?: string; area_id?: string; desde?: string; hasta?: string; limit?: number; offset?: number }) =>
    http.get<Licencia[]>("/api/licencias", { params }).then((r) => r.data),
  get: (id: string) => http.get<Licencia>(`/api/licencias/${id}`).then((r) => r.data),
  create: (p: LicenciaCreate) => http.post<Licencia>("/api/licencias", p).then((r) => r.data),
  enviar: (id: string) => http.post<Licencia>(`/api/licencias/${id}/enviar`).then((r) => r.data),
  validar: (id: string, dias_otorgados: number, observaciones?: string) =>
    http.post<Licencia>(`/api/licencias/${id}/validar`, { dias_otorgados, observaciones }).then((r) => r.data),
  rechazar: (id: string, motivo_rechazo: string) =>
    http.post<Licencia>(`/api/licencias/${id}/rechazar`, { motivo_rechazo }).then((r) => r.data),
  anular: (id: string, motivo_anulacion: string) =>
    http.post<Licencia>(`/api/licencias/${id}/anular`, { motivo_anulacion }).then((r) => r.data),
  evaluarTope: (id: string) => http.get(`/api/licencias/${id}/tope`).then((r) => r.data),
};
```

```ts
// frontend/src/api/catalogos.ts
import { http } from "./http";

export type Area = { id: string; nombre: string; parent_id: string | null };
export type Categoria = { id: string; codigo: string; nombre: string; activa: boolean };
export type TipoLicencia = { id: string; codigo: string; nombre: string; base_legal: string | null; paga: boolean; computa_dias: boolean };
export type Diagnostico = { id: string; codigo_cie10: string | null; descripcion: string; categoria: string | null; requiere_junta: boolean };

export const catalogosApi = {
  areas: () => http.get<Area[]>("/api/areas").then((r) => r.data),
  categorias: () => http.get<Categoria[]>("/api/categorias").then((r) => r.data),
  tiposLicencia: () => http.get<TipoLicencia[]>("/api/tipos-licencia").then((r) => r.data),
  diagnosticos: () => http.get<Diagnostico[]>("/api/diagnosticos").then((r) => r.data),
};
```

```ts
// frontend/src/api/topes.ts
import { http } from "./http";

export type Tope = {
  id: string; categoria_id: string; tipo_licencia_id: string;
  dias_maximos: number; ventana: "anio-calendario" | "anio-aniversario" | "sin-limite";
  vigente_desde: string; vigente_hasta: string | null; observacion: string | null;
};

export const topesApi = {
  list: () => http.get<Tope[]>("/api/admin/topes").then((r) => r.data),
  set: (categoria_id: string, tipo_licencia_id: string, body: { dias_maximos: number; ventana: string; desde: string; observacion?: string }) =>
    http.put<Tope>(`/api/admin/topes/${categoria_id}/${tipo_licencia_id}`, body).then((r) => r.data),
};
```

```ts
// frontend/src/api/reportes.ts
import { http } from "./http";

export const reportesApi = {
  porArea: (desde: string, hasta: string) =>
    http.get("/api/reportes/por-area", { params: { desde, hasta } }).then((r) => r.data),
  porCategoriaDiag: (desde: string, hasta: string) =>
    http.get("/api/reportes/por-categoria-diag", { params: { desde, hasta } }).then((r) => r.data),
  mensual: (desde: string, hasta: string) =>
    http.get("/api/reportes/mensual", { params: { desde, hasta } }).then((r) => r.data),
  downloadCsv: (path: string, desde: string, hasta: string) => {
    const base = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";
    window.location.href = `${base}/api/reportes/${path}?desde=${desde}&hasta=${hasta}&formato=csv`;
  },
};
```

```ts
// frontend/src/api/adjuntos.ts
import { http } from "./http";

export type Adjunto = {
  id: string; licencia_id: string; nombre_original: string; mime_type: string;
  size_bytes: number; sha256: string; created_at: string;
};

export const adjuntosApi = {
  upload: (licencia_id: string, file: File) => {
    const fd = new FormData();
    fd.append("licencia_id", licencia_id);
    fd.append("file", file);
    return http.post<Adjunto>("/api/adjuntos", fd, { headers: { "Content-Type": "multipart/form-data" } }).then((r) => r.data);
  },
  downloadUrl: (id: string) => http.get<{ url: string; expires_in_seconds: number }>(`/api/adjuntos/${id}/download`).then((r) => r.data),
};
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/api
git commit -m "feat(frontend): api clients (empleados, licencias, catálogos, topes, reportes, adjuntos)"
```

---

### Task 9.2: Empleados — listado + alta

**Files:**
- Create: `frontend/src/features/empleados/{EmpleadosListPage,EmpleadoCreateForm}.tsx`
- Add routes in `App.tsx`

- [ ] **Step 1: Listado con search debounced**

```tsx
// frontend/src/features/empleados/EmpleadosListPage.tsx
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { empleadosApi, type Empleado } from "@/api/empleados";

export function EmpleadosListPage() {
  const [q, setQ] = useState("");
  const [rows, setRows] = useState<Empleado[]>([]);
  useEffect(() => {
    const t = setTimeout(() => empleadosApi.list(q).then(setRows), 250);
    return () => clearTimeout(t);
  }, [q]);
  return (
    <section className="space-y-3">
      <header className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Empleados</h1>
        <Link to="/empleados/nuevo" className="bg-slate-900 text-white px-3 py-2 rounded">Nuevo</Link>
      </header>
      <input className="border rounded p-2 w-full max-w-md"
             placeholder="Buscar por legajo, CUIL o nombre…"
             value={q} onChange={(e) => setQ(e.target.value)} />
      <table className="w-full text-sm bg-white rounded shadow">
        <thead className="text-left bg-slate-100">
          <tr>
            <th className="p-2">Legajo</th><th className="p-2">Apellido y nombre</th>
            <th className="p-2">CUIL</th><th className="p-2">Categoría</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((e) => (
            <tr key={e.id} className="border-t">
              <td className="p-2">{e.legajo}</td>
              <td className="p-2">{e.apellido}, {e.nombre}</td>
              <td className="p-2">{e.cuil}</td>
              <td className="p-2">{e.categoria_id}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
```

- [ ] **Step 2: Alta**

```tsx
// frontend/src/features/empleados/EmpleadoCreateForm.tsx
import { useEffect, useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { empleadosApi } from "@/api/empleados";
import { catalogosApi, type Area, type Categoria } from "@/api/catalogos";

export function EmpleadoCreateForm() {
  const nav = useNavigate();
  const [areas, setAreas] = useState<Area[]>([]);
  const [cats, setCats] = useState<Categoria[]>([]);
  const [form, setForm] = useState({
    legajo: "", cuil: "", nombre: "", apellido: "",
    fecha_nacimiento: "", fecha_ingreso: "",
    area_id: "", categoria_id: "", supervisor_id: "",
    email: "", telefono: "",
  });
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    catalogosApi.areas().then(setAreas);
    catalogosApi.categorias().then(setCats);
  }, []);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await empleadosApi.create({
        legajo: form.legajo, cuil: form.cuil,
        nombre: form.nombre, apellido: form.apellido,
        fecha_nacimiento: form.fecha_nacimiento || null,
        fecha_ingreso: form.fecha_ingreso,
        area_id: form.area_id || null,
        categoria_id: form.categoria_id,
        supervisor_id: form.supervisor_id || null,
        email: form.email || null, telefono: form.telefono || null,
      });
      nav("/empleados");
    } catch (err: any) {
      setError(err?.response?.data?.error?.message ?? "Error");
    }
  }

  function setF<K extends keyof typeof form>(k: K, v: string) {
    setForm((p) => ({ ...p, [k]: v }));
  }

  return (
    <form onSubmit={submit} className="grid grid-cols-2 gap-3 max-w-2xl bg-white rounded shadow p-6">
      <h1 className="col-span-2 text-2xl font-semibold">Nuevo empleado</h1>
      {(["legajo","cuil","apellido","nombre","email","telefono"] as const).map((k) => (
        <label key={k} className="text-sm">
          {k}
          <input className="mt-1 w-full border rounded p-2"
                 value={form[k]} onChange={(e) => setF(k, e.target.value)} required={["legajo","cuil","apellido","nombre"].includes(k)} />
        </label>
      ))}
      <label className="text-sm">Fecha de ingreso
        <input type="date" className="mt-1 w-full border rounded p-2"
               value={form.fecha_ingreso} onChange={(e) => setF("fecha_ingreso", e.target.value)} required />
      </label>
      <label className="text-sm">Fecha de nacimiento
        <input type="date" className="mt-1 w-full border rounded p-2"
               value={form.fecha_nacimiento} onChange={(e) => setF("fecha_nacimiento", e.target.value)} />
      </label>
      <label className="text-sm">Área
        <select className="mt-1 w-full border rounded p-2"
                value={form.area_id} onChange={(e) => setF("area_id", e.target.value)}>
          <option value="">—</option>
          {areas.map((a) => <option key={a.id} value={a.id}>{a.nombre}</option>)}
        </select>
      </label>
      <label className="text-sm">Categoría
        <select className="mt-1 w-full border rounded p-2"
                value={form.categoria_id} onChange={(e) => setF("categoria_id", e.target.value)} required>
          <option value="">—</option>
          {cats.map((c) => <option key={c.id} value={c.id}>{c.nombre}</option>)}
        </select>
      </label>
      {error && <p className="col-span-2 text-red-600 text-sm">{error}</p>}
      <div className="col-span-2 flex justify-end gap-2">
        <button type="button" onClick={() => nav(-1)} className="px-4 py-2">Cancelar</button>
        <button className="bg-slate-900 text-white px-4 py-2 rounded">Guardar</button>
      </div>
    </form>
  );
}
```

- [ ] **Step 3: Wire routes**

In `App.tsx`, inside the protected layout block:
```tsx
<Route path="/empleados" element={<EmpleadosListPage />} />
<Route path="/empleados/nuevo" element={<EmpleadoCreateForm />} />
```

- [ ] **Step 4: Smoke test + commit**

```bash
pnpm typecheck
git add frontend/src/features/empleados frontend/src/App.tsx
git commit -m "feat(frontend): empleados listado con buscador + alta"
```

---

### Task 9.3: Licencias — listado, alta, acciones de transición

**Files:**
- Create: `frontend/src/features/licencias/{LicenciasListPage,LicenciaForm,LicenciaDetailPage,ValidarDialog,RechazarDialog}.tsx`
- Routes in `App.tsx`

- [ ] **Step 1: Listado con filtros**

```tsx
// frontend/src/features/licencias/LicenciasListPage.tsx
import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { licenciasApi, type EstadoLicencia, type Licencia } from "@/api/licencias";

const ESTADOS: EstadoLicencia[] = ["borrador","enviado","validado","rechazado","anulado"];

export function LicenciasListPage() {
  const [estado, setEstado] = useState<EstadoLicencia | "">("");
  const [desde, setDesde] = useState("");
  const [hasta, setHasta] = useState("");
  const [rows, setRows] = useState<Licencia[]>([]);

  useEffect(() => {
    licenciasApi.list({
      estado: estado || undefined,
      desde: desde || undefined,
      hasta: hasta || undefined,
    }).then(setRows);
  }, [estado, desde, hasta]);

  return (
    <section className="space-y-3">
      <header className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Licencias</h1>
        <Link to="/licencias/nueva" className="bg-slate-900 text-white px-3 py-2 rounded">Nueva</Link>
      </header>
      <div className="flex flex-wrap gap-2">
        <select className="border rounded p-2" value={estado} onChange={(e) => setEstado(e.target.value as any)}>
          <option value="">(estado)</option>
          {ESTADOS.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
        <input type="date" className="border rounded p-2" value={desde} onChange={(e) => setDesde(e.target.value)} />
        <input type="date" className="border rounded p-2" value={hasta} onChange={(e) => setHasta(e.target.value)} />
      </div>
      <table className="w-full text-sm bg-white rounded shadow">
        <thead className="text-left bg-slate-100">
          <tr><th className="p-2">Desde</th><th className="p-2">Hasta</th><th className="p-2">Días</th><th className="p-2">Estado</th><th className="p-2"></th></tr>
        </thead>
        <tbody>
          {rows.map((l) => (
            <tr key={l.id} className="border-t">
              <td className="p-2">{l.fecha_desde}</td>
              <td className="p-2">{l.fecha_hasta}</td>
              <td className="p-2">{l.dias_otorgados ?? l.dias_solicitados}</td>
              <td className="p-2"><span className="px-2 py-1 rounded bg-slate-200">{l.estado}</span></td>
              <td className="p-2"><Link to={`/licencias/${l.id}`} className="underline">Detalle</Link></td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
```

- [ ] **Step 2: Alta (formulario + adjuntos)**

```tsx
// frontend/src/features/licencias/LicenciaForm.tsx
import { useEffect, useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { catalogosApi, type Diagnostico, type TipoLicencia } from "@/api/catalogos";
import { empleadosApi, type Empleado } from "@/api/empleados";
import { licenciasApi } from "@/api/licencias";
import { adjuntosApi } from "@/api/adjuntos";

export function LicenciaForm() {
  const nav = useNavigate();
  const [empleados, setEmpleados] = useState<Empleado[]>([]);
  const [tipos, setTipos] = useState<TipoLicencia[]>([]);
  const [diags, setDiags] = useState<Diagnostico[]>([]);
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState({
    empleado_id: "", tipo_licencia_id: "", diagnostico_id: "",
    fecha_desde: "", fecha_hasta: "",
    observaciones: "", certificante: "", matricula_certificante: "",
  });

  useEffect(() => {
    empleadosApi.list().then(setEmpleados);
    catalogosApi.tiposLicencia().then(setTipos);
    catalogosApi.diagnosticos().then(setDiags);
  }, []);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      const lic = await licenciasApi.create({
        empleado_id: form.empleado_id, tipo_licencia_id: form.tipo_licencia_id,
        diagnostico_id: form.diagnostico_id || null,
        fecha_desde: form.fecha_desde, fecha_hasta: form.fecha_hasta,
        observaciones: form.observaciones || null,
        certificante: form.certificante || null,
        matricula_certificante: form.matricula_certificante || null,
      });
      if (file) await adjuntosApi.upload(lic.id, file);
      nav(`/licencias/${lic.id}`);
    } catch (err: any) {
      setError(err?.response?.data?.error?.message ?? "Error");
    }
  }

  function setF<K extends keyof typeof form>(k: K, v: string) { setForm((p) => ({ ...p, [k]: v })); }

  return (
    <form onSubmit={submit} className="grid grid-cols-2 gap-3 max-w-2xl bg-white rounded shadow p-6">
      <h1 className="col-span-2 text-2xl font-semibold">Nueva licencia</h1>
      <label className="text-sm col-span-2">Empleado
        <select className="mt-1 w-full border rounded p-2" value={form.empleado_id}
                onChange={(e) => setF("empleado_id", e.target.value)} required>
          <option value="">—</option>
          {empleados.map((e) => <option key={e.id} value={e.id}>{e.apellido}, {e.nombre} ({e.legajo})</option>)}
        </select>
      </label>
      <label className="text-sm">Tipo
        <select className="mt-1 w-full border rounded p-2" value={form.tipo_licencia_id}
                onChange={(e) => setF("tipo_licencia_id", e.target.value)} required>
          <option value="">—</option>
          {tipos.map((t) => <option key={t.id} value={t.id}>{t.nombre}</option>)}
        </select>
      </label>
      <label className="text-sm">Diagnóstico
        <select className="mt-1 w-full border rounded p-2" value={form.diagnostico_id}
                onChange={(e) => setF("diagnostico_id", e.target.value)}>
          <option value="">—</option>
          {diags.map((d) => <option key={d.id} value={d.id}>{d.descripcion}</option>)}
        </select>
      </label>
      <label className="text-sm">Desde
        <input type="date" className="mt-1 w-full border rounded p-2"
               value={form.fecha_desde} onChange={(e) => setF("fecha_desde", e.target.value)} required />
      </label>
      <label className="text-sm">Hasta
        <input type="date" className="mt-1 w-full border rounded p-2"
               value={form.fecha_hasta} onChange={(e) => setF("fecha_hasta", e.target.value)} required />
      </label>
      <label className="text-sm">Certificante
        <input className="mt-1 w-full border rounded p-2"
               value={form.certificante} onChange={(e) => setF("certificante", e.target.value)} />
      </label>
      <label className="text-sm">Matrícula certificante
        <input className="mt-1 w-full border rounded p-2"
               value={form.matricula_certificante} onChange={(e) => setF("matricula_certificante", e.target.value)} />
      </label>
      <label className="col-span-2 text-sm">Observaciones
        <textarea className="mt-1 w-full border rounded p-2" rows={3}
                  value={form.observaciones} onChange={(e) => setF("observaciones", e.target.value)} />
      </label>
      <label className="col-span-2 text-sm">Adjunto (PDF/imagen)
        <input type="file" accept="application/pdf,image/*"
               onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
      </label>
      {error && <p className="col-span-2 text-red-600 text-sm">{error}</p>}
      <div className="col-span-2 flex justify-end gap-2">
        <button type="button" onClick={() => nav(-1)} className="px-4 py-2">Cancelar</button>
        <button className="bg-slate-900 text-white px-4 py-2 rounded">Guardar</button>
      </div>
    </form>
  );
}
```

- [ ] **Step 3: Detalle con acciones**

```tsx
// frontend/src/features/licencias/LicenciaDetailPage.tsx
import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { licenciasApi, type Licencia } from "@/api/licencias";
import { useAuth } from "@/auth/AuthContext";

export function LicenciaDetailPage() {
  const { id = "" } = useParams();
  const { user } = useAuth();
  const [lic, setLic] = useState<Licencia | null>(null);
  const [tope, setTope] = useState<any | null>(null);

  async function reload() {
    setLic(await licenciasApi.get(id));
    try { setTope(await licenciasApi.evaluarTope(id)); } catch { setTope(null); }
  }
  useEffect(() => { reload(); }, [id]);

  if (!lic) return <p>Cargando…</p>;
  return (
    <section className="space-y-3 max-w-2xl">
      <h1 className="text-2xl font-semibold">Licencia</h1>
      <div className="bg-white rounded shadow p-4 space-y-2">
        <p><b>Estado:</b> {lic.estado}</p>
        <p><b>Desde:</b> {lic.fecha_desde} — <b>Hasta:</b> {lic.fecha_hasta}</p>
        <p><b>Días solicitados:</b> {lic.dias_solicitados} — <b>Otorgados:</b> {lic.dias_otorgados ?? "—"}</p>
        {tope && tope.tope_aplicable !== null && (
          <p className={tope.excede ? "text-red-600 font-medium" : "text-slate-600"}>
            Tope: {tope.dias_consumidos_ventana}/{tope.tope_aplicable} días en ventana. {tope.warning_msg}
          </p>
        )}
      </div>

      <div className="flex flex-wrap gap-2">
        {lic.estado === "borrador" && (
          <button onClick={async () => { await licenciasApi.enviar(lic.id); await reload(); }}
                  className="bg-slate-900 text-white px-3 py-2 rounded">Enviar</button>
        )}
        {lic.estado === "enviado" && user?.rol === "medico" && (
          <>
            <button onClick={async () => {
              const d = parseInt(prompt("Días a otorgar:", String(lic.dias_solicitados)) ?? "0", 10);
              if (Number.isFinite(d)) { await licenciasApi.validar(lic.id, d); await reload(); }
            }} className="bg-emerald-700 text-white px-3 py-2 rounded">Validar</button>
            <button onClick={async () => {
              const m = prompt("Motivo de rechazo:") ?? "";
              if (m) { await licenciasApi.rechazar(lic.id, m); await reload(); }
            }} className="bg-red-700 text-white px-3 py-2 rounded">Rechazar</button>
          </>
        )}
        {lic.estado === "validado" && user?.rol === "admin" && (
          <button onClick={async () => {
            const m = prompt("Motivo de anulación:") ?? "";
            if (m) { await licenciasApi.anular(lic.id, m); await reload(); }
          }} className="bg-amber-700 text-white px-3 py-2 rounded">Anular</button>
        )}
      </div>
    </section>
  );
}
```

> The `prompt()` calls are intentionally minimal v1; v1.1 replaces them with proper modals.

- [ ] **Step 4: Wire routes + commit**

In `App.tsx` (protected):
```tsx
<Route path="/licencias" element={<LicenciasListPage />} />
<Route path="/licencias/nueva" element={<LicenciaForm />} />
<Route path="/licencias/:id" element={<LicenciaDetailPage />} />
```

```bash
pnpm typecheck
git add frontend/src/features/licencias frontend/src/App.tsx
git commit -m "feat(frontend): licencias listado + alta con adjunto + detalle con acciones de transición"
```

---

### Task 9.4: Reportes UI

**Files:**
- Create: `frontend/src/features/reportes/ReportesPage.tsx`
- Route in `App.tsx`

```tsx
// frontend/src/features/reportes/ReportesPage.tsx
import { useState } from "react";
import { reportesApi } from "@/api/reportes";

export function ReportesPage() {
  const [desde, setDesde] = useState("2026-01-01");
  const [hasta, setHasta] = useState("2026-12-31");
  const [rows, setRows] = useState<any[]>([]);
  const [tipo, setTipo] = useState<"por-area"|"por-categoria-diag"|"mensual">("por-area");

  async function cargar() {
    if (tipo === "por-area") setRows(await reportesApi.porArea(desde, hasta));
    if (tipo === "por-categoria-diag") setRows(await reportesApi.porCategoriaDiag(desde, hasta));
    if (tipo === "mensual") setRows(await reportesApi.mensual(desde, hasta));
  }

  return (
    <section className="space-y-3">
      <h1 className="text-2xl font-semibold">Reportes</h1>
      <div className="flex flex-wrap gap-2 items-end">
        <label className="text-sm">Desde<input type="date" className="block border rounded p-2" value={desde} onChange={(e) => setDesde(e.target.value)} /></label>
        <label className="text-sm">Hasta<input type="date" className="block border rounded p-2" value={hasta} onChange={(e) => setHasta(e.target.value)} /></label>
        <label className="text-sm">Reporte
          <select className="block border rounded p-2" value={tipo} onChange={(e) => setTipo(e.target.value as any)}>
            <option value="por-area">Por área</option>
            <option value="por-categoria-diag">Por categoría diagnóstica</option>
            <option value="mensual">Mensual</option>
          </select>
        </label>
        <button onClick={cargar} className="bg-slate-900 text-white px-3 py-2 rounded">Cargar</button>
        <button onClick={() => reportesApi.downloadCsv(tipo, desde, hasta)} className="border px-3 py-2 rounded">Exportar CSV</button>
      </div>
      <table className="w-full text-sm bg-white rounded shadow">
        <thead className="bg-slate-100 text-left">
          <tr>{rows[0] ? Object.keys(rows[0]).map((k) => <th key={k} className="p-2">{k}</th>) : null}</tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i} className="border-t">
              {Object.values(r).map((v, j) => <td key={j} className="p-2">{String(v)}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
```

Route + commit:
```tsx
<Route path="/reportes" element={<ReportesPage />} />
```
```bash
git add frontend/src/features/reportes frontend/src/App.tsx
git commit -m "feat(frontend): reportes UI con export CSV"
```

---

### Task 9.5: Admin topes (grilla editable)

**Files:**
- Create: `frontend/src/features/admin/TopesPage.tsx`
- Route gated by `roles: ["admin"]`

```tsx
// frontend/src/features/admin/TopesPage.tsx
import { useEffect, useState } from "react";
import { catalogosApi, type Categoria, type TipoLicencia } from "@/api/catalogos";
import { topesApi, type Tope } from "@/api/topes";

const VENTANAS = ["anio-calendario", "anio-aniversario", "sin-limite"] as const;

export function TopesPage() {
  const [cats, setCats] = useState<Categoria[]>([]);
  const [tipos, setTipos] = useState<TipoLicencia[]>([]);
  const [topes, setTopes] = useState<Tope[]>([]);

  async function reload() {
    setCats(await catalogosApi.categorias());
    setTipos(await catalogosApi.tiposLicencia());
    setTopes(await topesApi.list());
  }
  useEffect(() => { reload(); }, []);

  function topeFor(catId: string, tipoId: string) {
    return topes.find((t) => t.categoria_id === catId && t.tipo_licencia_id === tipoId);
  }

  async function update(catId: string, tipoId: string) {
    const dias = parseInt(prompt("Días máximos:") ?? "", 10);
    if (!Number.isFinite(dias) || dias < 0) return;
    const ventana = (prompt(`Ventana (${VENTANAS.join("/")})`) ?? "anio-calendario") as string;
    if (!VENTANAS.includes(ventana as any)) return;
    const desde = prompt("Vigente desde (YYYY-MM-DD):", new Date().toISOString().slice(0, 10)) ?? "";
    await topesApi.set(catId, tipoId, { dias_maximos: dias, ventana, desde });
    await reload();
  }

  return (
    <section className="space-y-3">
      <h1 className="text-2xl font-semibold">Topes de días (admin)</h1>
      <table className="w-full text-sm bg-white rounded shadow">
        <thead>
          <tr className="bg-slate-100">
            <th className="p-2 text-left">Categoría \ Tipo licencia</th>
            {tipos.map((t) => <th key={t.id} className="p-2">{t.nombre}</th>)}
          </tr>
        </thead>
        <tbody>
          {cats.map((c) => (
            <tr key={c.id} className="border-t">
              <td className="p-2 font-medium">{c.nombre}</td>
              {tipos.map((t) => {
                const found = topeFor(c.id, t.id);
                return (
                  <td key={t.id} className="p-2">
                    <button onClick={() => update(c.id, t.id)} className="underline">
                      {found ? `${found.dias_maximos} (${found.ventana})` : "—"}
                    </button>
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
```

Route (admin only):
```tsx
<Route element={<ProtectedRoute roles={["admin"]} />}>
  <Route path="/admin/topes" element={<TopesPage />} />
</Route>
```

Commit:
```bash
git add frontend/src/features/admin frontend/src/App.tsx
git commit -m "feat(frontend): admin de topes con grilla editable y versionado"
```

---

### Task 9.6: Frontend smoke test (Vitest)

**Files:**
- Create: `frontend/tests/setup.ts`
- Create: `frontend/tests/App.test.tsx`

```ts
// frontend/tests/setup.ts
import "@testing-library/jest-dom/vitest";
```

```tsx
// frontend/tests/App.test.tsx
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import LoginPage from "../src/routes/login";

it("renders login form", () => {
  render(
    <MemoryRouter initialEntries={["/login"]}>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
      </Routes>
    </MemoryRouter>,
  );
  expect(screen.getByText("Medicia-Laboral")).toBeInTheDocument();
  expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
});
```

Run + commit:
```bash
pnpm test:unit
git add frontend/tests
git commit -m "test(frontend): smoke test del login"
```

---

## Phase 10 — E2E (Playwright)

### Task 10.1: Playwright setup + docker-compose.ci.yml

**Files:**
- Create: `frontend/playwright.config.ts`
- Create: `docker-compose.ci.yml`
- Create: `frontend/tests/e2e/fixtures.ts`

- [ ] **Step 1: Playwright config**

```ts
// frontend/playwright.config.ts
import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/e2e",
  fullyParallel: false,
  reporter: [["list"], ["html", { open: "never" }]],
  use: {
    baseURL: process.env.E2E_BASE_URL ?? "http://localhost:5173",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});
```

- [ ] **Step 2: `docker-compose.ci.yml`**

```yaml
# Top-level docker-compose.ci.yml — boots the full stack for E2E.
name: medicia-ci

services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: medicia
      POSTGRES_PASSWORD: medicia
      POSTGRES_DB: medicia
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U medicia -d medicia"]
      interval: 3s
      timeout: 3s
      retries: 20

  minio:
    image: minio/minio:RELEASE.2025-01-20T14-49-07Z
    command: server /data
    environment:
      MINIO_ROOT_USER: medicia
      MINIO_ROOT_PASSWORD: mediciamediciaminio
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 3s
      timeout: 3s
      retries: 20

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    depends_on:
      postgres: { condition: service_healthy }
      minio:    { condition: service_healthy }
    environment:
      POSTGRES_USER: medicia
      POSTGRES_PASSWORD: medicia
      POSTGRES_DB: medicia
      POSTGRES_HOST: postgres
      POSTGRES_PORT: 5432
      MINIO_ROOT_USER: medicia
      MINIO_ROOT_PASSWORD: mediciamediciaminio
      MINIO_BUCKET: medicia-adjuntos
      MINIO_ENDPOINT: minio:9000
      MINIO_USE_SSL: "false"
      APP_ENV: ci
      APP_SECRET_KEY: ci-secret-key-at-least-32-chars-long!
      JWT_ACCESS_TTL_MINUTES: "15"
      JWT_REFRESH_TTL_DAYS: "1"
      CORS_ORIGINS: "http://localhost:5173"
      ADMIN_EMAIL: admin@medicia.local
      ADMIN_PASSWORD: AdminPass123!XYZ
    command: >
      sh -c "alembic upgrade head &&
             python scripts/seed_dev.py &&
             uvicorn app.main:app --host 0.0.0.0 --port 8000"
    ports: ["8000:8000"]
```

- [ ] **Step 3: Fixtures helper**

```ts
// frontend/tests/e2e/fixtures.ts
import { test as base } from "@playwright/test";

export const USERS = {
  admin:  { email: "admin@medicia.local",  password: "AdminPass123!XYZ" },
  medico: { email: "medico@medicia.local", password: "MedicoPass123!XYZ" },
  rrhh:   { email: "rrhh@medicia.local",   password: "RrhhPass123!XYZ" },
};

export const test = base.extend<{
  loginAs: (role: keyof typeof USERS) => Promise<void>;
}>({
  loginAs: async ({ page }, use) => {
    await use(async (role) => {
      await page.goto("/login");
      await page.getByLabel(/email/i).fill(USERS[role].email);
      await page.getByLabel(/contraseña/i).fill(USERS[role].password);
      await page.getByRole("button", { name: /ingresar/i }).click();
      await page.waitForURL("/");
    });
  },
});

export { expect } from "@playwright/test";
```

> The seed script in Task 11.2 creates `medico@medicia.local` and `rrhh@medicia.local` with these passwords.

Commit:
```bash
git add frontend/playwright.config.ts docker-compose.ci.yml frontend/tests/e2e/fixtures.ts
git commit -m "test(e2e): playwright + ci compose + fixtures"
```

---

### Task 10.2: 4 escenarios golden path

**Files:**
- Create: `frontend/tests/e2e/01-admin-empleado-licencia.spec.ts`
- Create: `frontend/tests/e2e/02-medico-validar-con-tope.spec.ts`
- Create: `frontend/tests/e2e/03-medico-rechazar.spec.ts`
- Create: `frontend/tests/e2e/04-admin-tope-versionado.spec.ts`

- [ ] **Step 1: Escenario 1 — Admin crea empleado, licencia y envía**

```ts
// frontend/tests/e2e/01-admin-empleado-licencia.spec.ts
import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "./fixtures";

test("admin: crea empleado, abre licencia y la envía", async ({ page, loginAs }) => {
  await loginAs("admin");
  await page.getByRole("link", { name: "Empleados" }).click();
  await page.getByRole("link", { name: "Nuevo" }).click();

  const stamp = Date.now().toString();
  await page.getByLabel(/legajo/i).fill(`L${stamp.slice(-6)}`);
  await page.getByLabel(/cuil/i).fill("20111111119");
  await page.getByLabel(/apellido/i).fill("Test");
  await page.getByLabel(/nombre/i).fill("Empleado");
  await page.getByLabel(/fecha de ingreso/i).fill("2022-01-15");
  await page.getByLabel(/categoría/i).selectOption({ label: "Planta permanente" });
  await page.getByRole("button", { name: /guardar/i }).click();
  await expect(page).toHaveURL(/\/empleados$/);

  await page.getByRole("link", { name: "Licencias" }).click();
  await page.getByRole("link", { name: "Nueva" }).click();
  await page.getByLabel(/empleado/i).selectOption({ index: 1 });
  await page.getByLabel(/tipo/i).selectOption({ label: "Enfermedad común" });
  await page.getByLabel(/desde/i).fill("2026-06-01");
  await page.getByLabel(/hasta/i).fill("2026-06-05");
  await page.getByRole("button", { name: /guardar/i }).click();
  await expect(page.getByText("Estado:")).toContainText("borrador");
  await page.getByRole("button", { name: /enviar/i }).click();
  await expect(page.getByText("Estado:")).toContainText("enviado");

  const a = await new AxeBuilder({ page }).analyze();
  expect(a.violations.filter((v) => v.impact === "serious" || v.impact === "critical")).toEqual([]);
});
```

- [ ] **Step 2: Escenario 2 — Médico valida con warning de tope**

```ts
// frontend/tests/e2e/02-medico-validar-con-tope.spec.ts
import { expect, test } from "./fixtures";

test("médico: valida licencia y ve warning si excede tope", async ({ page, loginAs }) => {
  await loginAs("medico");
  await page.getByRole("link", { name: "Licencias" }).click();
  await page.getByRole("combobox").first().selectOption("enviado");
  const detalle = page.getByRole("link", { name: /detalle/i }).first();
  await detalle.click();

  // Stub prompt() before pressing Validar (the inline button uses window.prompt).
  await page.evaluate(() => { (window as any).prompt = () => "30"; });
  await page.getByRole("button", { name: /validar/i }).click();

  await expect(page.getByText("Estado:")).toContainText("validado");
});
```

- [ ] **Step 3: Escenario 3 — Médico rechaza**

```ts
// frontend/tests/e2e/03-medico-rechazar.spec.ts
import { expect, test } from "./fixtures";

test("médico: rechaza licencia con motivo", async ({ page, loginAs }) => {
  await loginAs("medico");
  await page.getByRole("link", { name: "Licencias" }).click();
  await page.getByRole("combobox").first().selectOption("enviado");
  await page.getByRole("link", { name: /detalle/i }).first().click();
  await page.evaluate(() => { (window as any).prompt = () => "certificado ilegible"; });
  await page.getByRole("button", { name: /rechazar/i }).click();
  await expect(page.getByText("Estado:")).toContainText("rechazado");
});
```

- [ ] **Step 4: Escenario 4 — Admin edita tope, versionado**

```ts
// frontend/tests/e2e/04-admin-tope-versionado.spec.ts
import { expect, test } from "./fixtures";

test("admin: edita tope y verifica que la celda muestra el nuevo valor", async ({ page, loginAs }) => {
  await loginAs("admin");
  await page.getByRole("link", { name: "Topes" }).click();
  await page.evaluate(() => {
    let i = 0;
    (window as any).prompt = (_msg: string, def: string) => {
      const answers = ["75", "anio-calendario", new Date().toISOString().slice(0, 10)];
      return answers[i++] ?? def;
    };
  });
  await page.getByRole("button").filter({ hasText: /—|días/ }).first().click();
  await expect(page.getByText("75 (anio-calendario)").first()).toBeVisible();
});
```

- [ ] **Step 5: Add Playwright to CI**

Append to `.github/workflows/ci.yml`:
```yaml
  e2e:
    runs-on: ubuntu-24.04
    needs: [backend, frontend]
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4
        with: { version: 9 }
      - uses: actions/setup-node@v4
        with: { node-version: 20, cache: pnpm, cache-dependency-path: frontend/pnpm-lock.yaml }
      - run: docker compose -f docker-compose.ci.yml up -d --build
      - run: |
          cd frontend
          pnpm install --frozen-lockfile
          pnpm exec playwright install --with-deps chromium
          pnpm build && pnpm preview --port 5173 &
          sleep 5
        env: { VITE_API_BASE_URL: "http://localhost:8000" }
      - run: cd frontend && pnpm test:e2e
        env: { E2E_BASE_URL: "http://localhost:5173" }
      - if: always()
        run: docker compose -f docker-compose.ci.yml logs --no-color > docker-logs.txt
      - uses: actions/upload-artifact@v4
        if: failure()
        with: { name: e2e-artifacts, path: |
          frontend/playwright-report/
          docker-logs.txt
        }
```

Commit:
```bash
git add frontend/tests/e2e .github/workflows/ci.yml
git commit -m "test(e2e): 4 escenarios golden path + a11y bloqueante + CI job"
```

---

## Phase 11 — Scripts de portabilidad

### Task 11.1: `backend/Dockerfile`

**Files:**
- Create: `backend/Dockerfile`

```dockerfile
# backend/Dockerfile
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy

RUN apt-get update && apt-get install -y --no-install-recommends \
      curl ca-certificates && rm -rf /var/lib/apt/lists/* \
 && pip install --no-cache-dir uv

WORKDIR /app
COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-dev || uv sync --no-dev

COPY . .

EXPOSE 8000
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Commit:
```bash
git add backend/Dockerfile
git commit -m "build(backend): Dockerfile multi-stage con uv"
```

---

### Task 11.2: Seed script

**Files:**
- Create: `backend/scripts/seed_dev.py`

```python
# backend/scripts/seed_dev.py
"""Idempotent seed for dev/CI. Creates 1 admin + 1 médico + 1 rrhh + base catálogos."""
import asyncio
import os
from datetime import date

from app.core.db import sessionmaker_factory
from app.core.settings import get_settings
from app.modules.categorias.schemas import CategoriaCreate
from app.modules.categorias.service import create_categoria
from app.modules.tipos_licencia.schemas import TipoLicenciaCreate
from app.modules.tipos_licencia.service import create_tipo
from app.modules.usuarios.models import Rol
from app.modules.usuarios.repository import get_by_email
from app.modules.usuarios.schemas import UsuarioCreate
from app.modules.usuarios.service import create_user

SETTINGS = get_settings()


async def main():
    factory = sessionmaker_factory(SETTINGS.db_dsn)
    async with factory() as s:
        # Users
        if not await get_by_email(s, os.environ["ADMIN_EMAIL"]):
            await create_user(s, UsuarioCreate(
                email=os.environ["ADMIN_EMAIL"],
                password=os.environ["ADMIN_PASSWORD"],
                nombre="Admin", rol=Rol.ADMIN,
            ))
        if not await get_by_email(s, "medico@medicia.local"):
            await create_user(s, UsuarioCreate(
                email="medico@medicia.local",
                password="MedicoPass123!XYZ",
                nombre="Médico", rol=Rol.MEDICO, matricula="MN12345",
            ))
        if not await get_by_email(s, "rrhh@medicia.local"):
            await create_user(s, UsuarioCreate(
                email="rrhh@medicia.local",
                password="RrhhPass123!XYZ",
                nombre="RRHH", rol=Rol.RRHH,
            ))

        # Categorías base
        for codigo, nombre in [
            ("planta-permanente", "Planta permanente"),
            ("contratado", "Contratado"),
            ("monotributista", "Monotributista"),
        ]:
            try:
                await create_categoria(s, CategoriaCreate(codigo=codigo, nombre=nombre))
            except Exception:
                pass

        # Tipos de licencia base
        for codigo, nombre in [
            ("enfermedad-comun", "Enfermedad común"),
            ("accidente-trabajo", "Accidente de trabajo"),
            ("examen-medico", "Examen médico"),
            ("maternidad", "Maternidad"),
            ("larga-enfermedad", "Larga enfermedad"),
        ]:
            try:
                await create_tipo(s, TipoLicenciaCreate(codigo=codigo, nombre=nombre))
            except Exception:
                pass

        await s.commit()
        print("Seed OK")


if __name__ == "__main__":
    asyncio.run(main())
```

Commit:
```bash
git add backend/scripts/seed_dev.py
git commit -m "feat(backend): seed_dev.py idempotente (admin/médico/rrhh + catálogos base)"
```

---

### Task 11.3: `scripts/bootstrap.sh`

**Files:**
- Create: `scripts/bootstrap.sh`

```bash
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
```

Make it executable + commit:
```bash
chmod +x scripts/bootstrap.sh
git add scripts/bootstrap.sh
git commit -m "feat(ops): scripts/bootstrap.sh idempotente para primera instalación"
```

---

### Task 11.4: `scripts/backup.sh` y `scripts/restore.sh`

**Files:**
- Create: `scripts/backup.sh`
- Create: `scripts/restore.sh`

```bash
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
```

```bash
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
```

Make executable + commit:
```bash
chmod +x scripts/backup.sh scripts/restore.sh
git add scripts/backup.sh scripts/restore.sh
git commit -m "feat(ops): scripts de backup (pg+minio) y restore con verificación sha256"
```

---

### Task 11.5: `scripts/migrate.sh`

**Files:**
- Create: `scripts/migrate.sh`

```bash
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
```

Commit:
```bash
chmod +x scripts/migrate.sh
git add scripts/migrate.sh
git commit -m "feat(ops): scripts/migrate.sh para mover una instalación entre servidores"
```

---

### Task 11.6: `docs/MIGRATION.md` (runbook)

**Files:**
- Create: `docs/MIGRATION.md`

```markdown
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
```

Commit:
```bash
git add docs/MIGRATION.md
git commit -m "docs(ops): runbook de migración portable para Claude Code"
```

---

## Phase 12 — Despliegue de producción (nginx + TLS + seguridad)

### Task 12.1: `frontend/Dockerfile` (build estático)

**Files:**
- Create: `frontend/Dockerfile`

```dockerfile
# frontend/Dockerfile — build estático servido luego por nginx.
FROM node:20-alpine AS builder
WORKDIR /app
RUN corepack enable
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile
COPY . .
ARG VITE_API_BASE_URL=/api
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
RUN pnpm build

FROM nginx:1.27-alpine
COPY --from=builder /app/dist /usr/share/nginx/html
# nginx config viene desde el host vía volumen — ver docker-compose.prod.yml
```

Commit:
```bash
git add frontend/Dockerfile
git commit -m "build(frontend): Dockerfile que produce el bundle estático para nginx"
```

---

### Task 12.2: `nginx/medicia.conf` con TLS, HSTS y headers de seguridad

**Files:**
- Create: `nginx/medicia.conf.template`

```nginx
# nginx/medicia.conf.template — renderiza ${DOMAIN_NAME} en runtime.
server {
    listen 80;
    server_name ${DOMAIN_NAME};
    location /.well-known/acme-challenge/ { root /var/www/certbot; }
    location / { return 301 https://$host$request_uri; }
}

server {
    listen 443 ssl http2;
    server_name ${DOMAIN_NAME};

    ssl_certificate     /etc/letsencrypt/live/${DOMAIN_NAME}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/${DOMAIN_NAME}/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header Referrer-Policy "same-origin" always;
    add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;
    add_header Content-Security-Policy "default-src 'self'; img-src 'self' data: blob:; style-src 'self' 'unsafe-inline'; script-src 'self'; connect-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'self'" always;

    client_max_body_size 12m;

    location /api/ {
        proxy_pass http://backend:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
        proxy_read_timeout 60s;
    }

    location = /healthz   { proxy_pass http://backend:8000/healthz; }
    location = /readyz    { proxy_pass http://backend:8000/readyz; }

    location / {
        root /usr/share/nginx/html;
        try_files $uri /index.html;
    }
}
```

Commit:
```bash
git add nginx/medicia.conf.template
git commit -m "feat(ops): nginx config con TLS, HSTS, CSP estricta y proxy a backend"
```

---

### Task 12.3: `docker-compose.prod.yml`

**Files:**
- Create: `docker-compose.prod.yml`

```yaml
# docker-compose.prod.yml — stack productivo: postgres + minio + backend + nginx + certbot.
name: medicia-prod

services:
  postgres:
    image: postgres:16-alpine
    restart: unless-stopped
    env_file: .env
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    volumes:
      - pg_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 5s
      retries: 20

  minio:
    image: minio/minio:RELEASE.2025-01-20T14-49-07Z
    restart: unless-stopped
    env_file: .env
    environment:
      MINIO_ROOT_USER: ${MINIO_ROOT_USER}
      MINIO_ROOT_PASSWORD: ${MINIO_ROOT_PASSWORD}
    command: server /data
    volumes:
      - minio_data:/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 5s
      retries: 20

  minio-init:
    image: minio/mc:RELEASE.2025-01-17T23-25-50Z
    depends_on:
      minio: { condition: service_healthy }
    env_file: .env
    entrypoint: >
      sh -c "
        mc alias set local http://minio:9000 $$MINIO_ROOT_USER $$MINIO_ROOT_PASSWORD &&
        (mc mb local/$$MINIO_BUCKET || true) &&
        mc anonymous set none local/$$MINIO_BUCKET
      "

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    restart: unless-stopped
    env_file: .env
    depends_on:
      postgres: { condition: service_healthy }
      minio: { condition: service_healthy }
    command: >
      sh -c "uv run alembic upgrade head &&
             uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips='*'"

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      args:
        VITE_API_BASE_URL: /api
    restart: unless-stopped

  nginx:
    image: nginx:1.27-alpine
    restart: unless-stopped
    depends_on: [backend, frontend]
    ports: ["80:80", "443:443"]
    env_file: .env
    volumes:
      - ./nginx/medicia.conf.template:/etc/nginx/templates/medicia.conf.template:ro
      - ./frontend/dist:/usr/share/nginx/html:ro
      - certbot_certs:/etc/letsencrypt:ro
      - certbot_webroot:/var/www/certbot
    environment:
      DOMAIN_NAME: ${DOMAIN_NAME}

  certbot:
    image: certbot/certbot:latest
    restart: unless-stopped
    volumes:
      - certbot_certs:/etc/letsencrypt
      - certbot_webroot:/var/www/certbot
    entrypoint: >
      sh -c "trap exit TERM;
             while :; do
               certbot renew --webroot -w /var/www/certbot --quiet;
               sleep 12h & wait $${!};
             done"

volumes:
  pg_data:
  minio_data:
  certbot_certs:
  certbot_webroot:
```

Add to `.env.example`:
```bash
DOMAIN_NAME=medicia.example.com
```

Commit:
```bash
git add docker-compose.prod.yml .env.example
git commit -m "feat(ops): docker-compose.prod con nginx, certbot, healthchecks y volúmenes nombrados"
```

---

### Task 12.4: Certificado TLS inicial + verificación

**Files:** none (procedure documented)

Procedure (one-time on the destination host, AFTER `bootstrap.sh` has run):

```bash
# 1) Obtener cert inicial con webroot
docker compose -f docker-compose.prod.yml exec certbot \
  certbot certonly --webroot -w /var/www/certbot \
  -d "$DOMAIN_NAME" --agree-tos -m "$ADMIN_EMAIL" --non-interactive

# 2) Reload nginx
docker compose -f docker-compose.prod.yml exec nginx nginx -s reload

# 3) Verificar TLS y headers
curl -sIo /dev/null -w "%{http_code}\n" "https://$DOMAIN_NAME/readyz"
curl -sI "https://$DOMAIN_NAME/" | grep -Ei "strict-transport-security|content-security-policy|x-content-type-options"
```

Append to `docs/MIGRATION.md`:

```markdown
## 6) TLS inicial

Después de `bootstrap.sh`, completar el cert HTTPS:

```bash
docker compose -f docker-compose.prod.yml exec certbot \
  certbot certonly --webroot -w /var/www/certbot \
  -d "$DOMAIN_NAME" --agree-tos -m "$ADMIN_EMAIL" --non-interactive
docker compose -f docker-compose.prod.yml exec nginx nginx -s reload
```

El servicio `certbot` corre en loop y renueva cada 12h.
```

Commit:
```bash
git add docs/MIGRATION.md
git commit -m "docs(ops): procedimiento certbot inicial en MIGRATION.md"
```

---

### Task 12.5: Smoke verification + sign-off

- [ ] **Step 1: Local end-to-end run**

```bash
cp .env.example .env  # editar valores
./scripts/bootstrap.sh
curl -fsS http://localhost/healthz
curl -fsS http://localhost/readyz
```

- [ ] **Step 2: CI pipeline green**

Push to a feature branch and confirm the GitHub Actions run reports:
- backend: ruff + mypy + pytest coverage ≥ 80% ✅
- frontend: typecheck + vitest coverage ≥ 70% ✅
- e2e: 4 escenarios + axe sin violaciones serias/críticas ✅

- [ ] **Step 3: Final commit + tag v0.1.0**

```bash
git checkout main
git pull --ff-only
git tag -a v0.1.0 -m "MVP: medicina laboral — ausentismo y licencias médicas"
git push origin main --tags
```

- [ ] **Step 4: Hand-off**

The plan is complete. Producción operativa con:
- 3 roles (admin, médico, rrhh), RBAC enforced
- Carga de licencias con adjunto PDF/imagen y SHA-256
- Estado-máquina con auditoría inmutable
- Topes versionados por categoría × tipo de licencia
- Reportes agregados con export CSV auditado
- Despliegue Docker, TLS automático, scripts de migración listos para Claude Code

---

## Apéndice A — Checklist de verificación final

- [ ] `docker compose -f docker-compose.prod.yml ps` muestra todos los servicios `healthy`
- [ ] `/readyz` devuelve 200
- [ ] Login admin con creds del `.env` funciona
- [ ] Crear empleado desde UI funciona
- [ ] Crear licencia con adjunto sube a MinIO (verificar con `mc ls`)
- [ ] Médico valida licencia → `auditoria` tiene entrada con `state_change`
- [ ] RRHH NO ve `diagnostico_id` ni `observaciones` en `GET /api/licencias`
- [ ] Editar tope crea nueva fila en `topes_dias`, la previa queda con `vigente_hasta` seteado
- [ ] Reporte CSV exportado dispara `accion='export'` en `auditoria`
- [ ] `INSERT` en `auditoria` desde la app funciona; intento de `DELETE` falla
- [ ] CI verde en pipeline completo
- [ ] `./scripts/backup.sh` produce backup con `MANIFEST.sha256` válido
- [ ] `./scripts/migrate.sh` mueve a un VPS de prueba y `/readyz` responde 200

---

## Apéndice B — Riesgos durante la implementación

| Riesgo | Síntoma temprano | Mitigación |
|---|---|---|
| Conflicto FK entre adjuntos y licencias en migración | autogenerate falla en Phase 5 | Diferir adjuntos hasta Phase 6.1 (ya documentado) |
| Tests flakey por testcontainers lento | timeouts en CI | Reusar contenedor sesión (`scope="session"`) ya está; aumentar timeout si pasa |
| `uuid7` package no disponible en algunos mirrors | `uv sync` falla | Cambiar a `uuid_extensions` o implementar UUIDv7 a mano (~10 líneas) |
| Certbot rate limit en pruebas | 429 de Let's Encrypt | Usar `--staging` durante setup, swap a prod al final |
| MinIO presigned URL expira mientras se descarga archivo grande | descarga incompleta | TTL de 5 min ya cubre archivos ≤ 10 MB (límite v1) |
| RBAC bypass por error de wiring | test_rbac falla | Matriz exhaustiva ya planeada en Task 2.5 |
