# CLAUDE.md

## Project Overview

Personal Finance Advisor — a full-stack application where users upload monthly bank transaction CSVs (CIBC format), and an AI financial advisor analyzes spending, compares to previous months, tracks goals, and provides actionable coaching. All data persists across sessions.

## Tech Stack

- **Frontend**: React (TypeScript) + Vite + Tailwind CSS 4 + shadcn/ui
- **Backend**: Python 3.12 + FastAPI
- **Database**: PostgreSQL 16 (local, containerized)
- **ORM**: SQLAlchemy + Alembic (migrations)
- **AI**: Anthropic Claude API (claude-sonnet-4-20250514)
- **Containerization**: Docker + Docker Compose

## Project Structure

```
finance-advisor/
├── docker-compose.yml
├── .env                      # Environment variables (not committed)
├── .env.example              # Template for environment variables
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   ├── components.json       # shadcn/ui config
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── index.css
│       ├── components/
│       │   ├── ui/           # shadcn/ui primitives
│       │   └── ...           # App components
│       ├── lib/
│       │   ├── api.ts        # API client (fetch wrapper)
│       │   └── utils.ts      # cn() helper, formatters
│       ├── hooks/
│       └── types/
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── alembic/
│   └── app/
│       ├── main.py           # FastAPI app entry
│       ├── config.py         # Settings from env
│       ├── database.py       # SQLAlchemy engine + session
│       ├── models/           # SQLAlchemy models
│       ├── schemas/          # Pydantic schemas
│       ├── routers/          # API route handlers
│       ├── services/         # Business logic
│       └── utils/            # Helpers (auth, categories)
└── scripts/
    └── init-db.sql           # Optional DB init script
```

## Development Commands

```bash
# Start all services (postgres, backend, frontend)
docker-compose up --build

# Start in detached mode
docker-compose up -d

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Stop everything
docker-compose down

# Stop and remove volumes (reset database)
docker-compose down -v

# Run database migrations
docker-compose exec backend alembic upgrade head

# Create new migration after model changes
docker-compose exec backend alembic revision --autogenerate -m "description"

# Access database directly
docker-compose exec db psql -U finance -d finance_advisor

# Run backend tests
docker-compose exec backend pytest

# Install new frontend dependency
docker-compose exec frontend npm install <package>

# Install new backend dependency (then rebuild)
# Add to requirements.txt, then:
docker-compose up --build backend
```

## Environment Variables

Copy `.env.example` to `.env` and fill in:

```env
ANTHROPIC_API_KEY=sk-ant-...      # Required for AI features
JWT_SECRET=<random-32-char>        # Generate with: openssl rand -hex 32
DATABASE_URL=postgresql://finance:finance_dev@db:5432/finance_advisor
```

## Architecture Decisions

### Backend

- **FastAPI** chosen for async support, automatic OpenAPI docs, and Pydantic integration
- **SQLAlchemy 2.0** style with type hints
- **Alembic** for migrations — never modify database schema directly
- **JWT auth** stored in httpOnly cookies, not localStorage
- All endpoints return JSON; errors use HTTPException with appropriate status codes
- Services contain business logic; routers are thin and handle HTTP concerns only

### Frontend

- **Vite** for fast HMR and optimized builds
- **Tailwind CSS 4** with CSS-first configuration
- **shadcn/ui** components copied into `src/components/ui/` (not a dependency)
- API calls go through `src/lib/api.ts` which handles auth headers and error transformation
- State management: React hooks + context for auth; no Redux needed for MVP

### Database

- PostgreSQL runs in Docker; data persists in a named volume (`postgres_data`)
- No cloud DB — fully local development
- Models use UUID primary keys (string format for JSON compatibility)
- JSON columns for flexible schema fields (expenses, targets, etc.)

## Key Patterns

### API Client (Frontend)

```typescript
// src/lib/api.ts
const API_BASE = 'http://localhost:8000';

async function request<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${endpoint}`, {
    credentials: 'include', // Send cookies
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || 'Request failed');
  }
  return res.json();
}

export const api = {
  get: <T>(endpoint: string) => request<T>(endpoint),
  post: <T>(endpoint: string, data: unknown) => 
    request<T>(endpoint, { method: 'POST', body: JSON.stringify(data) }),
  // ... put, delete
};
```

### Route Handler Pattern (Backend)

```python
# Routers are thin — delegate to services
@router.post("/upload")
async def upload_transactions(
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await transaction_service.process_upload(files, current_user, db)
    return result
```

### Service Pattern (Backend)

```python
# Services contain business logic
class TransactionService:
    def __init__(self, db: Session):
        self.db = db
    
    async def process_upload(self, files, user, db):
        # Parse CSVs, categorize, dedupe, save
        # Return summary
```

## Transaction Categorization

Categories are defined in `backend/app/utils/categories.py`. The categorizer:

1. Checks for family support e-transfers first (user-specific recipients)
2. Matches against keyword lists for each category
3. Handles edge cases (Uber rides vs Uber Eats)
4. Falls back to "Other" for unmatched transactions

To add a new category or keyword:
1. Edit `CATEGORY_KEYWORDS` in `categories.py`
2. No migration needed — categories are strings, not foreign keys

## AI Advisor Integration

The advisor service (`backend/app/services/advisor.py`) wraps the Anthropic API:

- System prompt defines the advisor's personality and constraints
- Context includes user profile, targets, current spending, previous month, and goals
- Monthly analysis generates a summary + extracted insights
- Chat maintains conversation history for follow-up questions

**Important**: The system prompt emphasizes sustainable change over dramatic overhauls — this user tends to burn out on intense short-term changes.

## CSV Parsing (CIBC Format)

Two formats supported:

| Type | Columns |
|------|---------|
| Debit | Date, Transaction, Debit, Credit |
| Credit | Date, Transaction, Payment, Credit |

Parser auto-detects based on column headers. Skips:
- Credit card payment rows ("PAYMENT THANK YOU")
- Rows with no debit/payment amount

Investments and internal transfers (QUESTRADE, INTERNET TRANSFER) are categorized separately.

## Common Tasks

### Adding a New API Endpoint

1. Create or update router in `backend/app/routers/`
2. Add Pydantic schemas in `backend/app/schemas/` if needed
3. Implement business logic in `backend/app/services/`
4. Register router in `backend/app/main.py` if new file
5. Update `frontend/src/lib/api.ts` with new method
6. Create/update React component to use it

### Adding a New Database Model

1. Create model in `backend/app/models/`
2. Import in `backend/app/models/__init__.py`
3. Create migration: `docker-compose exec backend alembic revision --autogenerate -m "add X"`
4. Apply migration: `docker-compose exec backend alembic upgrade head`
5. Create corresponding Pydantic schemas

### Adding a shadcn/ui Component

```bash
# From frontend directory (or exec into container)
npx shadcn@latest add <component-name>
```

Components are copied to `src/components/ui/`. Modify freely.

## Testing

### Backend

```bash
docker-compose exec backend pytest
docker-compose exec backend pytest -v                    # Verbose
docker-compose exec backend pytest tests/test_api.py    # Specific file
docker-compose exec backend pytest -k "test_upload"     # Pattern match
```

### Frontend

```bash
docker-compose exec frontend npm test
```

## Debugging

### Backend Logs

```bash
docker-compose logs -f backend
```

FastAPI auto-reloads on file changes. If something breaks, check:
1. Import errors in logs
2. Database connection (is `db` service healthy?)
3. Missing environment variables

### Frontend Logs

```bash
docker-compose logs -f frontend
```

Vite shows compilation errors. For runtime errors, check browser DevTools.

### Database Issues

```bash
# Connect directly
docker-compose exec db psql -U finance -d finance_advisor

# Check tables
\dt

# Check specific table
\d transactions

# Run query
SELECT * FROM users;
```

## Code Style

### Python

- Type hints on all function signatures
- Docstrings for public functions
- Black formatting (line length 100)
- isort for imports
- No unused imports or variables

### TypeScript

- Strict mode enabled
- Explicit return types on functions
- Interface over type for object shapes
- Async/await over .then() chains
- Destructure props in components

### General

- No console.log or print statements in committed code (use proper logging)
- No commented-out code blocks
- Descriptive variable names; avoid abbreviations except common ones (id, db, req, res)
- One component per file in frontend
- Keep files under 300 lines; split if larger

## Seed Data

The user's initial profile (for testing/development):

```json
{
  "net_monthly_income": 4634.42,
  "pay_frequency": "bi-weekly",
  "fixed_expenses": {
    "parentSupport": 400,
    "studentLoan": 128.86,
    "gym": 63.26,
    "chatgpt": 32,
    "uberOne": 11.29,
    "spotify": 7.22
  },
  "debts": [
    {"name": "Student Loan", "balance": 9000, "rate": 0, "minimum": 128.86}
  ],
  "emergency_fund": 5000,
  "budget_targets": {
    "Eating Out": 400,
    "Uber Eats": 300,
    "Groceries": 350,
    "Transportation - Rideshare": 100,
    "Transportation - Gas": 100,
    "Transportation - Parking": 50,
    "Transportation - Transit": 30,
    "Shopping": 200
  },
  "risk_tolerance": "medium",
  "family_support_recipients": ["Ammi"]
}
```

## MVP Scope

### In Scope

- User auth (register/login)
- Onboarding flow (AI-guided profile setup)
- CSV upload + auto-categorization
- Monthly dashboard with spending breakdown
- Progress bars against budget targets
- Month-over-month comparison
- AI-generated monthly analysis
- Goal tracking (create, update progress, complete)
- Chat with AI advisor

### Out of Scope (for now)

- Mobile app
- Bank API integration (Plaid, etc.)
- Multi-user households
- Receipt scanning / OCR
- Bill reminders / notifications
- Export to PDF / Excel
- Email notifications
- Recurring transaction detection

## Troubleshooting

### "Connection refused" to database

Database might not be ready. Check health:
```bash
docker-compose ps
```
If `db` shows unhealthy, check logs:
```bash
docker-compose logs db
```

### Migrations failing

```bash
# Reset to clean state (loses data)
docker-compose down -v
docker-compose up -d db
docker-compose exec backend alembic upgrade head
```

### Frontend can't reach backend

Check CORS settings in `backend/app/main.py`. Ensure `http://localhost:5173` is allowed.

### CSV upload not categorizing correctly

Check the transaction description against keywords in `categories.py`. Add missing keywords if needed. Category matching is case-insensitive.

## Contact / Context

This is a personal finance tool built for a specific user context:
- CIBC bank (Canada)
- Bi-weekly pay schedule
- Living at home (no rent)
- Key goal: reduce eating out spending from ~$1200/month to $400/month
- Tendency to burn out on intense changes — needs sustainable, gradual improvement