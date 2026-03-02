# Finance Advisor — Bootstrap Design

**Date:** 2026-03-02
**Status:** Approved

## Overview

Personal finance advisor app. Users upload CIBC bank CSVs, get AI-powered spending analysis, budget tracking, goal management, and conversational financial coaching.

## Tech Stack

- **Frontend:** React 18 + TypeScript + Vite + Tailwind CSS 4 + shadcn/ui
- **Backend:** Python 3.12 + FastAPI + SQLAlchemy 2.0 + Alembic
- **Database:** PostgreSQL 16
- **AI:** Anthropic Claude API (claude-sonnet-4-20250514)
- **Infra:** Docker Compose (3 services), GitHub Actions CI, pre-commit hooks

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│   Frontend   │────▶│   Backend    │────▶│  PostgreSQL   │
│  React/Vite  │◀────│   FastAPI    │◀────│     16        │
│  :5173       │     │  :8000       │     │  :5432        │
└─────────────┘     └──────┬───────┘     └──────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │ Anthropic API │
                    │  Claude       │
                    └──────────────┘
```

### Backend Layers

- **Routers** — thin HTTP handlers, delegate to services
- **Services** — business logic (CSV parsing, AI advisor, report generation)
- **Models** — SQLAlchemy ORM, UUID PKs, JSON columns for flexible data
- **Schemas** — Pydantic validation for requests/responses
- **Utils** — auth (JWT), transaction categorization

### Frontend Layers

- **Pages** — Login, Register, Onboarding, Dashboard, Transactions, Goals, Chat
- **Components** — shadcn/ui primitives + app-specific components
- **Hooks** — data fetching, auth state
- **Lib** — API client, utilities

## CI Pipeline

GitHub Actions on push to any branch + PRs to main:

1. **Lint** — ruff (backend), eslint (frontend)
2. **Type check** — mypy (backend), tsc --noEmit (frontend)
3. **Test** — pytest (backend), vitest (frontend)
4. **Build** — Vite build verification
5. **Docker** — docker compose build verification

Branch protection on `main` requiring CI pass.

## Pre-commit Hooks

Using the `pre-commit` framework:

- **ruff** — Python linting + formatting
- **ruff-format** — Python formatting check
- **eslint** — TypeScript/React linting
- **TypeScript check** — tsc --noEmit on frontend

## Database Models

6 tables: `users`, `user_profiles`, `transactions`, `monthly_reports`, `goals`, `chat_messages`. UUID string PKs. JSON columns for flexible schema fields. Composite indexes on (user_id, month_key).

## MVP Scope

In: auth, onboarding, CSV upload, dashboard, budget tracking, month comparison, AI analysis, goals, chat.
Out: mobile, bank API, multi-user households, receipts, notifications, export.

## Issue Breakdown Strategy

5 epics, ~15-20 issues, ordered by dependency:

1. **Project Skeleton** — repo, Docker, CI, pre-commit
2. **Auth & Data Layer** — models, migrations, JWT auth, seed data
3. **Core Features** — CSV upload, categorization, transactions view
4. **Dashboard & Reports** — spending breakdown, budget tracking, month comparison, AI analysis
5. **AI & Goals** — chat interface, goal tracking, onboarding flow
