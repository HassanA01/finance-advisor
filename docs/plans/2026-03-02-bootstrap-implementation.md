# Finance Advisor Bootstrap — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Scaffold the finance-advisor project with a working Docker stack, CI pipeline, pre-commit hooks, and a full issue backlog on GitHub.

**Architecture:** Three-service Docker Compose (PostgreSQL 16, FastAPI backend, React/Vite frontend). Backend uses SQLAlchemy 2.0 + Alembic. Frontend uses Tailwind CSS 4 + shadcn/ui. GitHub Actions CI validates lint, types, tests, and Docker builds on every push/PR.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy, Alembic, React 18, TypeScript, Vite, Tailwind CSS 4, shadcn/ui, PostgreSQL 16, Docker, GitHub Actions, pre-commit (ruff, eslint)

---

## Task 1: Create GitHub Repo & Init Git

**Files:**
- Create: `.gitignore`

**Step 1: Create the GitHub repo**

```bash
cd /Users/aneeqhassan/Development/FinanceAdvisor
gh repo create finance-advisor --public --description "Personal Finance Advisor — AI-powered spending analysis, budget tracking, and financial coaching" --source . --push=false
```

**Step 2: Initialize git**

```bash
git init
```

**Step 3: Create .gitignore**

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.egg-info/
dist/
build/
.eggs/
*.egg
.venv/
venv/

# Node
node_modules/
dist/

# Environment
.env
.env.local
.env.*.local

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Docker
postgres_data/

# Test / Coverage
.coverage
htmlcov/
.pytest_cache/
coverage/

# Alembic
alembic/versions/__pycache__/
```

**Step 4: Commit**

```bash
git add .gitignore
git commit -m "chore: initialize repository with .gitignore"
```

---

## Task 2: Backend — Dependencies & Dockerfile

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/requirements-dev.txt`
- Create: `backend/Dockerfile`

**Step 1: Create backend directory and requirements.txt**

`backend/requirements.txt`:
```
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
sqlalchemy>=2.0.0
alembic>=1.13.0
psycopg2-binary>=2.9.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
python-multipart>=0.0.9
pyjwt>=2.8.0
pwdlib[argon2]>=0.2.0
anthropic>=0.40.0
pandas>=2.2.0
python-dotenv>=1.0.0
```

`backend/requirements-dev.txt`:
```
-r requirements.txt
pytest>=8.0.0
pytest-asyncio>=0.24.0
httpx>=0.27.0
ruff>=0.8.0
mypy>=1.13.0
```

**Step 2: Create multi-stage Dockerfile**

`backend/Dockerfile`:
```dockerfile
# ---- Dev Stage ----
FROM python:3.12-slim AS dev

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements-dev.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ---- Prod Stage ----
FROM python:3.12-slim AS prod

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

**Step 3: Commit**

```bash
git add backend/
git commit -m "chore: add backend dependencies and Dockerfile"
```

---

## Task 3: Backend — FastAPI App Skeleton

**Files:**
- Create: `backend/app/__init__.py`
- Create: `backend/app/main.py`
- Create: `backend/app/config.py`
- Create: `backend/app/database.py`
- Create: `backend/app/models/__init__.py`
- Create: `backend/app/schemas/__init__.py`
- Create: `backend/app/routers/__init__.py`
- Create: `backend/app/services/__init__.py`
- Create: `backend/app/utils/__init__.py`

**Step 1: Create app/config.py**

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://finance:finance_dev@db:5432/finance_advisor"
    ANTHROPIC_API_KEY: str = ""
    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    class Config:
        env_file = ".env"


settings = Settings()
```

**Step 2: Create app/database.py**

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**Step 3: Create app/main.py**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Finance Advisor API",
    description="Personal finance advisor with AI-powered analysis",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

**Step 4: Create empty __init__.py files**

All `__init__.py` files are empty except `backend/app/models/__init__.py` (populated in Task 4).

**Step 5: Commit**

```bash
git add backend/app/
git commit -m "chore: add FastAPI app skeleton with config and database setup"
```

---

## Task 4: Backend — SQLAlchemy Models

**Files:**
- Create: `backend/app/models/user.py`
- Create: `backend/app/models/transaction.py`
- Create: `backend/app/models/report.py`
- Create: `backend/app/models/goal.py`
- Create: `backend/app/models/chat.py`
- Modify: `backend/app/models/__init__.py`

**Step 1: Create user.py**

```python
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, JSON, String
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")
    monthly_reports = relationship("MonthlyReport", back_populates="user", cascade="all, delete-orphan")
    goals = relationship("Goal", back_populates="user", cascade="all, delete-orphan")
    chat_messages = relationship("ChatMessage", back_populates="user", cascade="all, delete-orphan")


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), unique=True, nullable=False)

    net_monthly_income = Column(Float)
    pay_frequency = Column(String)

    fixed_expenses = Column(JSON, default=dict)
    debts = Column(JSON, default=list)
    budget_targets = Column(JSON, default=dict)
    family_support_recipients = Column(JSON, default=list)

    emergency_fund = Column(Float, default=0)
    risk_tolerance = Column(String, default="medium")

    onboarding_complete = Column(Boolean, default=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="profile")
```

**Step 2: Create transaction.py**

```python
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Index, String

from app.database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)

    date = Column(DateTime, nullable=False)
    description = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    category = Column(String, nullable=False)
    source = Column(String, nullable=False)

    month_key = Column(String, nullable=False, index=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="transactions")

    __table_args__ = (
        Index("idx_user_month", "user_id", "month_key"),
    )
```

**Step 3: Create report.py**

```python
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, JSON, String, Text, UniqueConstraint

from app.database import Base


class MonthlyReport(Base):
    __tablename__ = "monthly_reports"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)

    month_key = Column(String, nullable=False)

    spending = Column(JSON)
    vs_target = Column(JSON)
    vs_prev_month = Column(JSON)

    summary = Column(Text)
    insights = Column(JSON)

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="monthly_reports")

    __table_args__ = (
        UniqueConstraint("user_id", "month_key", name="unique_user_month"),
    )
```

**Step 4: Create goal.py**

```python
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, String

from app.database import Base


class Goal(Base):
    __tablename__ = "goals"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)

    name = Column(String, nullable=False)
    target_amount = Column(Float, nullable=False)
    current_amount = Column(Float, default=0)
    deadline = Column(DateTime, nullable=True)
    status = Column(String, default="active")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="goals")
```

**Step 5: Create chat.py**

```python
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, Text

from app.database import Base


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)

    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="chat_messages")
```

**Step 6: Update models/__init__.py**

```python
from app.models.user import User, UserProfile
from app.models.transaction import Transaction
from app.models.report import MonthlyReport
from app.models.goal import Goal
from app.models.chat import ChatMessage

__all__ = ["User", "UserProfile", "Transaction", "MonthlyReport", "Goal", "ChatMessage"]
```

**Step 7: Commit**

```bash
git add backend/app/models/
git commit -m "feat: add SQLAlchemy models for all database tables"
```

---

## Task 5: Backend — Alembic Setup

**Files:**
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`
- Create: `backend/alembic/script.py.mako`
- Create: `backend/alembic/versions/` (directory)

**Step 1: Initialize Alembic**

This must be run inside the backend container or with the backend virtualenv. During bootstrap, we create the files manually.

`backend/alembic.ini`:
```ini
[alembic]
script_location = alembic
sqlalchemy.url = postgresql://finance:finance_dev@db:5432/finance_advisor

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

**Step 2: Create alembic/env.py**

```python
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.config import settings
from app.database import Base
from app.models import *  # noqa: F401,F403 — ensure all models are registered

config = context.config
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

**Step 3: Create alembic/script.py.mako**

```mako
"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
```

**Step 4: Create versions directory**

```bash
mkdir -p backend/alembic/versions
touch backend/alembic/versions/.gitkeep
```

**Step 5: Commit**

```bash
git add backend/alembic.ini backend/alembic/
git commit -m "chore: add Alembic migration setup"
```

---

## Task 6: Backend — Test Infrastructure

**Files:**
- Create: `backend/pytest.ini`
- Create: `backend/tests/__init__.py`
- Create: `backend/tests/conftest.py`
- Create: `backend/tests/test_health.py`

**Step 1: Create pytest.ini**

```ini
[pytest]
testpaths = tests
asyncio_mode = auto
```

**Step 2: Create tests/conftest.py**

```python
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)
```

**Step 3: Create tests/test_health.py (the failing test first)**

```python
def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
```

**Step 4: Verify test passes**

Run (once Docker is up): `docker compose exec backend pytest -v`
Expected: PASS — health endpoint exists from Task 3.

**Step 5: Commit**

```bash
git add backend/pytest.ini backend/tests/
git commit -m "test: add pytest infrastructure and health endpoint test"
```

---

## Task 7: Backend — Linting Config

**Files:**
- Create: `backend/pyproject.toml`

**Step 1: Create pyproject.toml with ruff config**

```toml
[tool.ruff]
target-version = "py312"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP"]
ignore = ["E501"]

[tool.ruff.lint.isort]
known-first-party = ["app"]

[tool.mypy]
python_version = "3.12"
warn_return_any = true
warn_unused_configs = true
ignore_missing_imports = true
```

**Step 2: Commit**

```bash
git add backend/pyproject.toml
git commit -m "chore: add ruff and mypy configuration"
```

---

## Task 8: Frontend — Vite + React + TypeScript + Tailwind CSS 4 + shadcn/ui

**Files:**
- Create: `frontend/` (entire scaffold via CLI tools)

**Step 1: Scaffold Vite project**

```bash
cd /Users/aneeqhassan/Development/FinanceAdvisor
npm create vite@latest frontend -- --template react-ts
```

**Step 2: Install dependencies**

```bash
cd frontend
npm install
npm install tailwindcss @tailwindcss/vite
npm install react-router-dom
npm install recharts
npm install -D eslint @eslint/js typescript-eslint globals eslint-plugin-react-hooks eslint-plugin-react-refresh
```

**Step 3: Configure Vite for Tailwind CSS 4 + path aliases**

Replace `frontend/vite.config.ts`:
```typescript
import path from "path"
import tailwindcss from "@tailwindcss/vite"
import react from "@vitejs/plugin-react"
import { defineConfig } from "vite"

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    host: true,
    port: 5173,
  },
})
```

**Step 4: Configure Tailwind CSS 4 (CSS-first)**

Replace `frontend/src/index.css`:
```css
@import "tailwindcss";
```

**Step 5: Add TypeScript path alias**

Update `frontend/tsconfig.app.json` — add to `compilerOptions`:
```json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```

**Step 6: Initialize shadcn/ui**

```bash
cd frontend
npx shadcn@latest init --defaults
```

This creates `components.json` and sets up the `src/components/ui/` directory.

**Step 7: Add core shadcn/ui components**

```bash
npx shadcn@latest add button card input progress table dialog select tabs badge alert skeleton separator
```

**Step 8: Create placeholder App.tsx**

Replace `frontend/src/App.tsx`:
```tsx
function App() {
  return (
    <div className="min-h-screen bg-background text-foreground flex items-center justify-center">
      <div className="text-center space-y-4">
        <h1 className="text-4xl font-bold">Finance Advisor</h1>
        <p className="text-muted-foreground">Your AI-powered financial coach</p>
      </div>
    </div>
  )
}

export default App
```

**Step 9: Commit**

```bash
cd /Users/aneeqhassan/Development/FinanceAdvisor
git add frontend/
git commit -m "chore: scaffold frontend with Vite, React, TypeScript, Tailwind CSS 4, shadcn/ui"
```

---

## Task 9: Frontend — Dockerfile

**Files:**
- Create: `frontend/Dockerfile`
- Create: `frontend/.dockerignore`

**Step 1: Create multi-stage Dockerfile**

`frontend/Dockerfile`:
```dockerfile
# ---- Dev Stage ----
FROM node:20-alpine AS dev

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm install

COPY . .

CMD ["npm", "run", "dev", "--", "--host"]

# ---- Prod Stage ----
FROM node:20-alpine AS build

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:alpine AS prod
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

**Step 2: Create .dockerignore**

`frontend/.dockerignore`:
```
node_modules
dist
.git
```

**Step 3: Commit**

```bash
git add frontend/Dockerfile frontend/.dockerignore
git commit -m "chore: add frontend Dockerfile with multi-stage build"
```

---

## Task 10: Docker Compose

**Files:**
- Create: `docker-compose.yml`
- Create: `scripts/init-db.sql`
- Create: `backend/.dockerignore`

**Step 1: Create docker-compose.yml**

```yaml
version: '3.8'

services:
  db:
    image: postgres:16-alpine
    container_name: finance_db
    environment:
      POSTGRES_USER: finance
      POSTGRES_PASSWORD: finance_dev
      POSTGRES_DB: finance_advisor
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init-db.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U finance -d finance_advisor"]
      interval: 5s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: ./backend
      target: dev
    container_name: finance_backend
    environment:
      DATABASE_URL: postgresql://finance:finance_dev@db:5432/finance_advisor
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY:-}
      JWT_SECRET: ${JWT_SECRET:-dev-secret-change-in-production}
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy
    volumes:
      - ./backend:/app
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  frontend:
    build:
      context: ./frontend
      target: dev
    container_name: finance_frontend
    ports:
      - "5173:5173"
    depends_on:
      - backend
    volumes:
      - ./frontend:/app
      - /app/node_modules
    command: npm run dev -- --host

volumes:
  postgres_data:
```

**Step 2: Create scripts/init-db.sql**

```sql
-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```

**Step 3: Create backend/.dockerignore**

```
__pycache__
*.pyc
.pytest_cache
.mypy_cache
.venv
venv
.git
```

**Step 4: Commit**

```bash
git add docker-compose.yml scripts/ backend/.dockerignore
git commit -m "chore: add Docker Compose with PostgreSQL, backend, and frontend services"
```

---

## Task 11: Pre-commit Hooks

**Files:**
- Create: `.pre-commit-config.yaml`
- Create: `frontend/eslint.config.js` (if not already created by Vite scaffold)

**Step 1: Create .pre-commit-config.yaml**

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-json
      - id: check-added-large-files
        args: ['--maxkb=500']

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.6
    hooks:
      - id: ruff
        args: [--fix, --config, backend/pyproject.toml]
        files: ^backend/
      - id: ruff-format
        args: [--config, backend/pyproject.toml]
        files: ^backend/

  - repo: local
    hooks:
      - id: eslint
        name: eslint (frontend)
        entry: bash -c 'cd frontend && npx eslint --max-warnings 0 src/'
        language: system
        files: ^frontend/src/.*\.(ts|tsx)$
        pass_filenames: false

      - id: tsc
        name: typecheck (frontend)
        entry: bash -c 'cd frontend && npx tsc --noEmit'
        language: system
        files: ^frontend/src/.*\.(ts|tsx)$
        pass_filenames: false
```

**Step 2: Install pre-commit and hooks**

```bash
pip install pre-commit
pre-commit install
```

**Step 3: Verify hooks run**

```bash
pre-commit run --all-files
```

Expected: All hooks pass (or minor whitespace fixes auto-applied).

**Step 4: Commit**

```bash
git add .pre-commit-config.yaml
git commit -m "chore: add pre-commit hooks for ruff, eslint, and TypeScript checking"
```

---

## Task 12: CI Pipeline (GitHub Actions)

**Files:**
- Create: `.github/workflows/ci.yml`

**Step 1: Create CI workflow**

`.github/workflows/ci.yml`:
```yaml
name: CI

on:
  push:
    branches: ['**']
  pull_request:
    branches: [main]

jobs:
  lint-backend:
    name: Lint & Type Check (Backend)
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: backend
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install ruff mypy
      - run: ruff check app/
      - run: ruff format --check app/
      - run: pip install -r requirements.txt
      - run: mypy app/ --ignore-missing-imports

  lint-frontend:
    name: Lint & Type Check (Frontend)
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: frontend
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json
      - run: npm ci
      - run: npx eslint --max-warnings 0 src/
      - run: npx tsc --noEmit

  test-backend:
    name: Test (Backend)
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_USER: finance
          POSTGRES_PASSWORD: finance_dev
          POSTGRES_DB: finance_advisor
        ports:
          - 5432:5432
        options: >-
          --health-cmd="pg_isready -U finance -d finance_advisor"
          --health-interval=5s
          --health-timeout=5s
          --health-retries=5
    defaults:
      run:
        working-directory: backend
    env:
      DATABASE_URL: postgresql://finance:finance_dev@localhost:5432/finance_advisor
      JWT_SECRET: ci-test-secret
      ANTHROPIC_API_KEY: test-key
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install -r requirements-dev.txt
      - run: pytest -v

  test-frontend:
    name: Test (Frontend)
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: frontend
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json
      - run: npm ci
      - run: npm run build

  docker-build:
    name: Docker Build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: docker compose build
```

**Step 2: Commit**

```bash
git add .github/
git commit -m "ci: add GitHub Actions workflow for lint, test, and Docker build"
```

---

## Task 13: Environment Config & README

**Files:**
- Create: `.env.example`
- Create: `README.md`

**Step 1: Create .env.example**

```env
# Anthropic API key for AI features
ANTHROPIC_API_KEY=sk-ant-your-key-here

# JWT secret for authentication (generate with: openssl rand -hex 32)
JWT_SECRET=change-me-generate-a-secure-random-string

# Database URL (default works with Docker Compose)
DATABASE_URL=postgresql://finance:finance_dev@db:5432/finance_advisor
```

**Step 2: Create README.md**

```markdown
# Finance Advisor

Personal Finance Advisor — an AI-powered application for tracking spending, analyzing budgets, and getting financial coaching. Upload your CIBC bank transaction CSVs and get actionable insights.

## Tech Stack

- **Frontend:** React + TypeScript + Vite + Tailwind CSS 4 + shadcn/ui
- **Backend:** Python 3.12 + FastAPI + SQLAlchemy + Alembic
- **Database:** PostgreSQL 16
- **AI:** Anthropic Claude API
- **Infrastructure:** Docker Compose + GitHub Actions CI

## Architecture

```mermaid
graph LR
    FE[Frontend<br/>React/Vite<br/>:5173] --> BE[Backend<br/>FastAPI<br/>:8000]
    BE --> DB[(PostgreSQL<br/>:5432)]
    BE --> AI[Anthropic<br/>Claude API]
```

## Quick Start

### Prerequisites

- Docker & Docker Compose
- An Anthropic API key (for AI features)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/<your-username>/finance-advisor.git
   cd finance-advisor
   ```

2. Copy environment variables:
   ```bash
   cp .env.example .env
   ```

3. Edit `.env` and add your `ANTHROPIC_API_KEY` and generate a `JWT_SECRET`:
   ```bash
   openssl rand -hex 32  # Use output as JWT_SECRET
   ```

4. Start all services:
   ```bash
   docker compose up --build
   ```

5. Run database migrations:
   ```bash
   docker compose exec backend alembic upgrade head
   ```

6. Open the app: [http://localhost:5173](http://localhost:5173)

## Development

### Common Commands

```bash
# Start all services
docker compose up --build

# Start in background
docker compose up -d

# View logs
docker compose logs -f backend
docker compose logs -f frontend

# Stop everything
docker compose down

# Reset database (destroys data)
docker compose down -v

# Run backend tests
docker compose exec backend pytest -v

# Run migrations
docker compose exec backend alembic upgrade head

# Create new migration
docker compose exec backend alembic revision --autogenerate -m "description"

# Access database
docker compose exec db psql -U finance -d finance_advisor
```

### Pre-commit Hooks

This project uses pre-commit for code quality:

```bash
pip install pre-commit
pre-commit install
```

Hooks run automatically on commit: ruff (Python lint/format), eslint (TypeScript), tsc (type check).

## Contributing

1. Create a feature branch: `feat/<issue-number>-<description>`
2. Write tests for new code
3. Ensure Docker builds and tests pass
4. Open a PR to `main`
5. Wait for CI to pass + approval
```

**Step 3: Commit**

```bash
git add .env.example README.md
git commit -m "docs: add README and .env.example"
```

---

## Task 14: Verify Full Stack Builds & Runs

**Step 1: Build all containers**

```bash
docker compose build
```

Expected: All three services build successfully.

**Step 2: Start the stack**

```bash
docker compose up -d
```

**Step 3: Verify health**

```bash
docker compose ps
curl http://localhost:8000/health
```

Expected: `{"status":"healthy"}`

**Step 4: Verify frontend**

Open http://localhost:5173 — should show "Finance Advisor" placeholder page.

**Step 5: Run backend tests**

```bash
docker compose exec backend pytest -v
```

Expected: 1 test passes (health endpoint).

**Step 6: Stop stack**

```bash
docker compose down
```

---

## Task 15: Create GitHub Labels

**Step 1: Create all labels**

```bash
# Type labels
gh label create "epic" --color "3E4B9E" --description "Epic-level tracking issue"
gh label create "feature" --color "0E8A16" --description "New feature"
gh label create "bug" --color "D73A4A" --description "Bug fix"
gh label create "chore" --color "FBCA04" --description "Maintenance and tooling"
gh label create "tech-debt" --color "E4E669" --description "Technical debt"

# Status labels
gh label create "blocked" --color "B60205" --description "Blocked by another issue"
gh label create "in-progress" --color "0075CA" --description "Currently being worked on"
gh label create "ready-for-review" --color "BFD4F2" --description "Ready for code review"
gh label create "mvp-critical" --color "D93F0B" --description "Must have for MVP"

# Priority labels
gh label create "priority:high" --color "B60205" --description "High priority"
gh label create "priority:medium" --color "FBCA04" --description "Medium priority"
gh label create "priority:low" --color "0E8A16" --description "Low priority"

# Size labels
gh label create "size:S" --color "C5DEF5" --description "Small — a few hours"
gh label create "size:M" --color "BFD4F2" --description "Medium — a day or two"
gh label create "size:L" --color "0075CA" --description "Large — multiple days"
```

---

## Task 16: Create GitHub Issues

Create all issues using `gh issue create`. Dependencies noted in each issue body.

### Epic 1: Project Foundation

**Issue #1** is this bootstrap task itself (already being done).

### Epic 2: Authentication

**Issue #2: User registration endpoint**
```bash
gh issue create \
  --title "feat: User registration endpoint" \
  --label "feature,mvp-critical,priority:high,size:M" \
  --body "$(cat <<'EOF'
## Description
Create POST /auth/register endpoint that accepts email + password, hashes password, creates user + empty profile, returns JWT token.

## Acceptance Criteria
- [ ] POST /auth/register accepts {email, password}
- [ ] Password hashed with pwdlib (argon2)
- [ ] Returns JWT token in httpOnly cookie
- [ ] Returns 409 if email already exists
- [ ] Creates empty UserProfile row
- [ ] Tests: register success, duplicate email, invalid input

## Technical Approach
- Create `backend/app/routers/auth.py`
- Create `backend/app/utils/auth.py` (hash_password, verify_password, create_token, get_current_user)
- Create `backend/app/schemas/auth.py` (RegisterRequest, LoginRequest, TokenResponse)
- Register router in main.py

## Dependencies
- Project skeleton (Task 1 — bootstrap)
EOF
)"
```

**Issue #3: User login endpoint**
```bash
gh issue create \
  --title "feat: User login endpoint with JWT" \
  --label "feature,mvp-critical,priority:high,size:S" \
  --body "$(cat <<'EOF'
## Description
Create POST /auth/login endpoint. Verify credentials, return JWT in httpOnly cookie.

## Acceptance Criteria
- [ ] POST /auth/login accepts {email, password}
- [ ] Returns JWT in httpOnly cookie on success
- [ ] Returns 401 on invalid credentials
- [ ] GET /auth/me returns current user (protected)
- [ ] POST /auth/logout clears cookie
- [ ] Tests for all endpoints

## Technical Approach
- Add login/logout/me routes to auth router
- JWT contains user_id, expiry

## Dependencies
- #2 (registration endpoint)
EOF
)"
```

**Issue #4: Login & registration UI**
```bash
gh issue create \
  --title "feat: Login and registration pages" \
  --label "feature,mvp-critical,priority:high,size:M" \
  --body "$(cat <<'EOF'
## Description
Build login and registration pages with form validation. Redirect to dashboard on success.

## Acceptance Criteria
- [ ] /login page with email + password form
- [ ] /register page with email + password + confirm password
- [ ] Client-side validation (email format, password length, match)
- [ ] Error display for API errors (duplicate email, wrong password)
- [ ] Redirect to /dashboard on successful auth
- [ ] Auth context provider with useAuth hook
- [ ] Protected route wrapper for authenticated pages
- [ ] React Router setup with routes

## Technical Approach
- Create AuthContext + useAuth hook
- Create ProtectedRoute component
- Set up React Router in App.tsx
- Build Login and Register pages using shadcn/ui Card, Input, Button

## Dependencies
- #3 (login endpoint)
EOF
)"
```

### Epic 3: User Profile & Onboarding

**Issue #5: Profile CRUD endpoints**
```bash
gh issue create \
  --title "feat: User profile CRUD endpoints" \
  --label "feature,mvp-critical,priority:high,size:S" \
  --body "$(cat <<'EOF'
## Description
Create endpoints to get and update user profile (income, expenses, targets, etc.)

## Acceptance Criteria
- [ ] GET /profile returns current user's profile
- [ ] PUT /profile updates profile fields
- [ ] PATCH /profile/onboarding-complete marks onboarding done
- [ ] All endpoints require authentication
- [ ] Tests for get, update, partial update

## Technical Approach
- Create `backend/app/routers/profile.py`
- Create `backend/app/schemas/profile.py`
- Register router in main.py

## Dependencies
- #2 (auth)
EOF
)"
```

**Issue #6: AI-powered onboarding flow**
```bash
gh issue create \
  --title "feat: AI-powered onboarding flow" \
  --label "feature,mvp-critical,priority:medium,size:L" \
  --body "$(cat <<'EOF'
## Description
Build a conversational onboarding flow where the AI advisor asks questions one section at a time to build the user's financial profile.

## Acceptance Criteria
- [ ] Onboarding chat UI with step indicator
- [ ] AI asks about: income, fixed expenses, debts, budget targets, goals, risk tolerance
- [ ] User responses update profile via API
- [ ] Can skip and come back later
- [ ] Marks onboarding_complete when done
- [ ] Backend: POST /onboarding/chat endpoint
- [ ] Frontend: Onboarding page with chat interface + profile summary sidebar

## Technical Approach
- Backend: Create onboarding router that wraps AdvisorService with onboarding-specific system prompt
- Frontend: Multi-step chat interface that extracts structured data from conversation

## Dependencies
- #4 (auth UI), #5 (profile endpoints)
EOF
)"
```

### Epic 4: Transaction Management

**Issue #7: CSV upload & parsing endpoint**
```bash
gh issue create \
  --title "feat: CSV upload and transaction parsing endpoint" \
  --label "feature,mvp-critical,priority:high,size:M" \
  --body "$(cat <<'EOF'
## Description
Create endpoint to upload CIBC CSV files, parse transactions, auto-categorize, deduplicate, and store.

## Acceptance Criteria
- [ ] POST /transactions/upload accepts multiple CSV files
- [ ] Parses CIBC debit format (Date, Transaction, Debit, Credit)
- [ ] Parses CIBC credit format (Date, Transaction, Payment, Credit)
- [ ] Auto-categorizes using keyword matching
- [ ] Deduplicates against existing transactions (date+description+amount)
- [ ] Skips credit card payment rows
- [ ] Returns count of uploaded, duplicates skipped, months affected
- [ ] Tests: debit CSV, credit CSV, deduplication, categorization

## Technical Approach
- Create `backend/app/services/csv_parser.py`
- Create `backend/app/utils/categories.py`
- Create `backend/app/routers/transactions.py`
- Use pandas for CSV parsing

## Dependencies
- #2 (auth)
EOF
)"
```

**Issue #8: Transaction list endpoint & UI**
```bash
gh issue create \
  --title "feat: Transaction list with search and filtering" \
  --label "feature,mvp-critical,priority:medium,size:M" \
  --body "$(cat <<'EOF'
## Description
Endpoint to list transactions by month + full transaction table UI with search/filter.

## Acceptance Criteria
- [ ] GET /transactions/{month_key} returns transactions for a month
- [ ] Query params: category filter, search term, sort order
- [ ] Frontend: Transactions page with Table, search input, category filter Select
- [ ] Month selector to switch between months
- [ ] Category badges with color coding
- [ ] Tests for API filtering and pagination

## Technical Approach
- Add list endpoint to transactions router
- Frontend: Transactions page using shadcn Table, Input, Select, Badge

## Dependencies
- #7 (CSV upload), #4 (auth UI)
EOF
)"
```

**Issue #9: CSV upload UI**
```bash
gh issue create \
  --title "feat: Drag-and-drop CSV upload UI" \
  --label "feature,mvp-critical,priority:medium,size:M" \
  --body "$(cat <<'EOF'
## Description
Build a drag-and-drop file upload component for CSV files with processing status feedback.

## Acceptance Criteria
- [ ] Drag-and-drop zone for CSV files
- [ ] Click to browse also works
- [ ] Accepts multiple files
- [ ] Shows upload progress and processing status
- [ ] Displays results: uploaded count, duplicates skipped, months affected
- [ ] Error handling for invalid files
- [ ] Links to transaction view for affected months

## Technical Approach
- Create Upload page component
- Use native drag-and-drop API
- POST multipart/form-data to /transactions/upload

## Dependencies
- #7 (upload endpoint), #4 (auth UI)
EOF
)"
```

### Epic 5: Dashboard & Reports

**Issue #10: Monthly spending aggregation endpoint**
```bash
gh issue create \
  --title "feat: Monthly spending aggregation and report endpoint" \
  --label "feature,mvp-critical,priority:high,size:M" \
  --body "$(cat <<'EOF'
## Description
Create endpoint that aggregates spending by category for a month, compares to targets and previous month.

## Acceptance Criteria
- [ ] GET /reports/{month_key} returns or generates monthly report
- [ ] Aggregates spending by category
- [ ] Computes vs_target (actual vs budget target per category)
- [ ] Computes vs_prev_month (current vs previous month per category)
- [ ] Caches generated report in monthly_reports table
- [ ] Tests: aggregation logic, target comparison, month-over-month

## Technical Approach
- Create `backend/app/routers/reports.py`
- Create `backend/app/schemas/report.py`

## Dependencies
- #7 (transactions exist), #5 (profile has budget targets)
EOF
)"
```

**Issue #11: AI monthly analysis**
```bash
gh issue create \
  --title "feat: AI-generated monthly spending analysis" \
  --label "feature,mvp-critical,priority:high,size:M" \
  --body "$(cat <<'EOF'
## Description
Integrate Claude API to generate narrative analysis of monthly spending with actionable insights.

## Acceptance Criteria
- [ ] AdvisorService.analyze_month() generates summary + insights
- [ ] Summary: narrative paragraph about the month
- [ ] Insights: extracted bullet points (over/under budget, trends)
- [ ] Analysis stored in MonthlyReport.summary and .insights
- [ ] Graceful fallback if API key missing or API fails
- [ ] Tests: mock Anthropic API, verify prompt construction

## Technical Approach
- Create `backend/app/services/advisor.py`
- System prompt from spec (fiduciary-minded, sustainable change focus)
- Inject into report generation flow

## Dependencies
- #10 (report endpoint)
EOF
)"
```

**Issue #12: Dashboard UI**
```bash
gh issue create \
  --title "feat: Main dashboard with spending breakdown and insights" \
  --label "feature,mvp-critical,priority:high,size:L" \
  --body "$(cat <<'EOF'
## Description
Build the main dashboard page showing current month overview with charts, progress bars, and AI insights.

## Acceptance Criteria
- [ ] Month selector (dropdown or arrows)
- [ ] Spending breakdown chart (pie or bar chart by category)
- [ ] Progress bars: actual vs target for each budget category
- [ ] Quick insights cards from AI analysis
- [ ] Recent transactions list (last 10)
- [ ] Total spent vs income summary
- [ ] Loading skeletons while data loads
- [ ] Responsive layout

## Technical Approach
- Use recharts for pie/bar charts
- shadcn Progress for budget bars
- shadcn Card for insight cards, Skeleton for loading
- Fetch from /reports/{month_key} and /transactions/{month_key}

## Dependencies
- #10 (report endpoint), #8 (transaction list), #4 (auth UI)
EOF
)"
```

**Issue #13: Month-over-month comparison UI**
```bash
gh issue create \
  --title "feat: Month-over-month comparison view" \
  --label "feature,mvp-critical,priority:medium,size:M" \
  --body "$(cat <<'EOF'
## Description
Side-by-side comparison of two months' spending with visual diff indicators.

## Acceptance Criteria
- [ ] Select two months to compare
- [ ] Side-by-side category breakdown
- [ ] Visual indicators: up/down arrows, red/green for better/worse
- [ ] Percentage change per category
- [ ] Total spending comparison

## Technical Approach
- Create MonthComparison page component
- Fetch two reports and compute diffs client-side
- Use shadcn Table with colored badges for changes

## Dependencies
- #10 (report endpoint), #4 (auth UI)
EOF
)"
```

### Epic 6: Goals & Chat

**Issue #14: Goal CRUD endpoints**
```bash
gh issue create \
  --title "feat: Goal tracking CRUD endpoints" \
  --label "feature,mvp-critical,priority:medium,size:S" \
  --body "$(cat <<'EOF'
## Description
CRUD endpoints for financial goals (create, read, update progress, complete/pause).

## Acceptance Criteria
- [ ] POST /goals — create goal (name, target_amount, deadline)
- [ ] GET /goals — list all goals for user
- [ ] PUT /goals/{id} — update goal (name, target, current_amount, status)
- [ ] DELETE /goals/{id} — delete goal
- [ ] Tests: CRUD operations, validation

## Technical Approach
- Create `backend/app/routers/goals.py`
- Create `backend/app/schemas/goal.py`

## Dependencies
- #2 (auth)
EOF
)"
```

**Issue #15: Goal tracking UI**
```bash
gh issue create \
  --title "feat: Goal tracking page with progress cards" \
  --label "feature,mvp-critical,priority:medium,size:M" \
  --body "$(cat <<'EOF'
## Description
UI for viewing, creating, editing, and tracking financial goals.

## Acceptance Criteria
- [ ] Goal cards showing name, progress bar, current/target amounts
- [ ] Add new goal dialog (name, target amount, optional deadline)
- [ ] Edit goal dialog (update amount, name, target)
- [ ] Mark goal as completed or paused
- [ ] Delete goal with confirmation
- [ ] Empty state when no goals exist

## Technical Approach
- Goals page with Card grid layout
- shadcn Dialog for add/edit forms
- shadcn Progress for progress bars

## Dependencies
- #14 (goal endpoints), #4 (auth UI)
EOF
)"
```

**Issue #16: AI chat endpoint**
```bash
gh issue create \
  --title "feat: AI advisor chat endpoint" \
  --label "feature,mvp-critical,priority:medium,size:M" \
  --body "$(cat <<'EOF'
## Description
Chat endpoint that maintains conversation history and includes user's financial context.

## Acceptance Criteria
- [ ] POST /chat — send message, get AI response
- [ ] GET /chat/history — get chat history
- [ ] DELETE /chat/history — clear chat history
- [ ] AI has access to user's profile, current spending, targets, goals
- [ ] Chat history persisted in chat_messages table
- [ ] Tests: send message, history retrieval, context injection

## Technical Approach
- Create `backend/app/routers/chat.py`
- AdvisorService.chat() method with conversation history
- Inject user context into system/user messages

## Dependencies
- #11 (advisor service), #5 (profile)
EOF
)"
```

**Issue #17: Chat UI**
```bash
gh issue create \
  --title "feat: Chat interface with AI advisor" \
  --label "feature,mvp-critical,priority:medium,size:M" \
  --body "$(cat <<'EOF'
## Description
Chat page with message bubbles, typing indicator, and message input.

## Acceptance Criteria
- [ ] Chat message list with user/assistant bubbles
- [ ] Text input with send button
- [ ] Loading/typing indicator while AI responds
- [ ] Auto-scroll to latest message
- [ ] Clear history button
- [ ] Markdown rendering in AI responses
- [ ] Empty state with suggested prompts

## Technical Approach
- Chat page component with message list and input
- Fetch history on load, POST new messages
- Use shadcn Card for message bubbles, Skeleton for typing indicator

## Dependencies
- #16 (chat endpoint), #4 (auth UI)
EOF
)"
```

**Issue #18: Seed data script**
```bash
gh issue create \
  --title "chore: Database seed script with test profile and sample transactions" \
  --label "chore,priority:medium,size:S" \
  --body "$(cat <<'EOF'
## Description
Create a seed script that populates the database with the test user profile and sample transactions for development.

## Acceptance Criteria
- [ ] Script creates test user (user@example.com / password)
- [ ] Creates full user profile with budget targets, expenses, debts
- [ ] Creates sample Travel Fund goal
- [ ] Optionally creates sample transactions for 2 months
- [ ] Idempotent — safe to run multiple times
- [ ] Runnable via: docker compose exec backend python -m scripts.seed

## Technical Approach
- Create `backend/scripts/seed.py`
- Use SQLAlchemy session to insert data
- Check for existing data before inserting

## Dependencies
- #2 (auth/password hashing)
EOF
)"
```

**Step 2: Commit issue creation script (optional)**

No files to commit — issues are created directly on GitHub.

---

## Task 17: Push to GitHub

**Step 1: Add remote and push**

```bash
git remote add origin https://github.com/<username>/finance-advisor.git
git branch -M main
git push -u origin main
```

**Step 2: Set up branch protection (optional, via gh CLI)**

```bash
gh api repos/{owner}/{repo}/branches/main/protection \
  -X PUT \
  -f "required_status_checks[strict]=true" \
  -f "required_status_checks[contexts][]=lint-backend" \
  -f "required_status_checks[contexts][]=lint-frontend" \
  -f "required_status_checks[contexts][]=test-backend" \
  -f "required_status_checks[contexts][]=test-frontend" \
  -f "required_status_checks[contexts][]=docker-build" \
  -f "enforce_admins=false" \
  -f "required_pull_request_reviews[required_approving_review_count]=0" \
  -f "restrictions=null"
```

---

## Summary: Task Dependency Graph

```
Task 1 (repo + git)
  └─▶ Task 2 (backend deps + Dockerfile)
       └─▶ Task 3 (FastAPI skeleton)
            └─▶ Task 4 (models)
                 └─▶ Task 5 (Alembic)
       └─▶ Task 6 (tests)
       └─▶ Task 7 (linting config)
  └─▶ Task 8 (frontend scaffold)
       └─▶ Task 9 (frontend Dockerfile)
  └─▶ Task 10 (docker-compose)  [depends on Tasks 2, 9]
  └─▶ Task 11 (pre-commit)
  └─▶ Task 12 (CI pipeline)
  └─▶ Task 13 (.env.example + README)
  └─▶ Task 14 (verify) [depends on all above]
  └─▶ Task 15 (GitHub labels) [depends on Task 1]
  └─▶ Task 16 (GitHub issues) [depends on Task 15]
  └─▶ Task 17 (push) [depends on Task 14]
```

## Issue Execution Order (after bootstrap)

Critical path: #2 → #3 → #4 → #5 → #7 → #8 → #9 → #10 → #11 → #12 → #13 → #14 → #15 → #16 → #17 → #6 → #18
