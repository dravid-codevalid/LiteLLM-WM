# Multi-Tenant AI Research Assistant

A production-grade multi-tenant AI research platform built with **FastAPI** (Python) and **Next.js** (TypeScript). It enables organizations to manage workspaces, collaborate on AI-powered research conversations, and track token usage with full financial audit trails.

## Architecture

- **Backend:** Modular monolith with selective hexagonal boundaries (FastAPI + SQLModel + asyncpg)
- **Frontend:** Next.js 16 App Router + Tailwind CSS v4 + shadcn/ui + Zustand
- **LLM Integration:** LiteLLM for multi-provider model routing (OpenAI, Anthropic, Google, etc.)
- **Billing:** Temporal IO for crash-proof usage recording
- **Database:** PostgreSQL 16

## Key Features

- **Multi-tenant workspaces** with admin/member role-based access
- **Real-time streaming chat** via WebSocket
- **Multi-model support** — configure and switch between any LiteLLM-compatible model
- **Immutable financial ledger** — usage records survive workspace deletion
- **Owner portal** — cross-workspace analytics dashboard with charts
- **JWT authentication** with HttpOnly secure cookies

## Quick Start

### Prerequisites

- Python 3.12+, [uv](https://docs.astral.sh/uv/) package manager
- Node.js 20+, npm
- Docker & Docker Compose (for PostgreSQL + Temporal)

### 1. Start Infrastructure

```bash
docker compose up -d
```

### 2. Backend Setup

```bash
cd backend
uv sync
alembic upgrade head
python scripts/create_owner.py --username admin --email admin@example.com --password YourPassword123
fastapi dev src/main.py
```

### 3. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### 4. Access

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **Temporal UI:** http://localhost:8233

## Project Structure

```
├── backend/
│   ├── src/
│   │   ├── modules/           # Domain modules (auth, workspaces, conversations, usage, admin, llm)
│   │   ├── shared/            # Cross-cutting (config, db, middleware)
│   │   └── main.py            # Application entry point
│   ├── scripts/               # CLI utilities
│   ├── tests/                 # pytest test suite
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── app/               # Next.js App Router pages
│   │   ├── components/        # Reusable UI components (shadcn/ui + custom)
│   │   ├── hooks/             # Custom React hooks
│   │   ├── store/             # Zustand state management
│   │   └── lib/               # API client & utilities
│   └── package.json
├── docker-compose.yml         # PostgreSQL + Temporal
└── DEVELOPER_MANUAL.md        # Full architectural specification
```

## Documentation

See [DEVELOPER_MANUAL.md](./DEVELOPER_MANUAL.md) for the complete architectural specification, API contracts, and design decisions.

## Environment Variables

### Backend (`backend/.env`)

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://postgres:postgres@localhost:5432/research_platform` |
| `JWT_SECRET_KEY` | Secret for JWT signing | — |
| `TEMPORAL_HOST` | Temporal server address | `localhost:8234` (mapped from Docker 7233) |
| `TEMPORAL_TASK_QUEUE` | Temporal task queue name | `billing-tasks` |

### Frontend (`frontend/.env.local`)

| Variable | Description | Default |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API base URL | `http://localhost:8000` |
| `NEXT_PUBLIC_WS_URL` | WebSocket base URL | `ws://localhost:8000` |
