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
