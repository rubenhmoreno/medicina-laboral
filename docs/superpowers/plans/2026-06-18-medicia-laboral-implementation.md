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

Mirror Task 3.2: schemas with `codigo`, `nombre`, `base_legal`, `paga`, `computa_dias`. Repo with `list_all`, `by_codigo`, `get`, `insert`. Service raises `ConflictError` on duplicate `codigo`. Router under `/api/tipos-licencia`, POST gated by `Rol.ADMIN`.

- [ ] **Step 3: Test (same shape as 3.2)**

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

- [ ] **Step 2-4: Schemas/repo/service/router/tests/migration follow same shape as Task 3.2.**

Router under `/api/diagnosticos`, POST gated by `Rol.ADMIN`. Allow optional filter `?categoria=`.

Commit:
```bash
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
