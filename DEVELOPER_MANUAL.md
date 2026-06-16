# Developer Manual: Multi-Tenant AI Research Assistant

**Document Version:** 3.0.0 (Unified Final)
**Project Status:** Active Development

---

## 1. Vision & Core System Objectives

The Multi-Tenant AI Research Assistant is a high-performance, collaborative workspace environment designed for advanced AI engineering and research. It leverages **LiteLLM** as a library to seamlessly abstract interactions across multiple LLM providers while maintaining strict multi-tenant isolation, precise financial token tracking, and real-time collaboration.

### Core Architectural Mandates

1. **Dynamic Cost Resolution:** Token costs are resolved from `litellm.model_cost` (the built-in pricing dictionary). The `GlobalModel` database table's `fallback_input_cost_per_million` and `fallback_output_cost_per_million` act exclusively as fallbacks for models not recognized by LiteLLM.
2. **Strict API Key Centralization:** API keys are stored per-model in the `GlobalModel` database table, managed exclusively by the Application Owner through the admin UI. Workspaces never see or manage provider keys.
3. **Immutable Financial Ledgers:** Chat messaging pipelines (UI state) are physically decoupled from the `UsageLedger` (financial logging). Billing records survive conversation AND workspace deletions via `SET NULL` foreign keys.
4. **Mid-Stream Crash Protection:** If an LLM stream drops mid-generation, the system catches the exception and dispatches a Temporal workflow with `0` tokens to ensure logging integrity without unfair charges.
5. **Real-Time Streaming:** The application enforces WebSockets for real-time LLM text streaming and workspace-level presence.

---

## 2. Architectural Pattern

### Modular Monolith (Feature-First) with Selective Hexagonal Boundaries

The backend is organized by **domain/feature** rather than by technical layer. Within each module, a simple **layered structure** is used: `router → service → repository`.

**Hexagonal (Ports & Adapters) principles are applied selectively** — specifically to the LLM integration boundary — rather than across the entire codebase.

### Why this combination

- **Modular Monolith:** Keeps each domain area (workspaces, conversations, usage) self-contained. Provides natural seams for future extraction without committing to microservices.
- **Layered structure per module:** Most modules (workspaces, conversations, auth) are largely CRUD with light validation — `router → service → repository` is sufficient.
- **Selective Hexagonal ports:** The LLM provider boundary is the part most likely to change, most valuable to test in isolation, and most naturally expressed as an interface.

### What this explicitly avoids

- Full hexagonal/clean architecture applied uniformly — adds indirection with no payoff for simple CRUD.
- Flat, non-modular layered structure — tangles domains together as the system grows.
- Microservices — unnecessary operational overhead for a single application with one database.

---

## 3. Technology Stack & Tooling

| Layer | Technology | Tooling |
| :--- | :--- | :--- |
| **Frontend UI** | Next.js 15 (App Router), Tailwind CSS v4, shadcn/ui | **npm** |
| **Client State** | Zustand | **npm** |
| **Frontend Testing** | Jest | **npm** |
| **Backend API** | FastAPI (Python 3.12+) | **uv** |
| **LLM Gateway** | LiteLLM Python SDK (used as library, NOT proxy) | **uv** |
| **Async Billing** | Temporal IO (worker runs in FastAPI event loop) | **uv** |
| **Backend Testing** | Pytest | **uv** |
| **Database & ORM** | PostgreSQL & SQLModel | **uv** |
| **Migrations** | Alembic | **uv** |
| **Password Hashing** | bcrypt via passlib | **uv** |
| **Authentication** | JWT (PyJWT), stored in HttpOnly Secure cookie | **uv** |

---

## 4. Role-Based Access Control (RBAC)

The system has **three roles**:

| Role | Description |
| :--- | :--- |
| **Application Owner** | Super-admin seeded via CLI script. Manages global API keys and has cross-workspace financial visibility. |
| **Workspace Admin** | Any authenticated user who creates a workspace. Manages members, allowed models, and sees workspace-wide usage. |
| **Workspace Member** | A user added to a workspace by its admin. Can chat and see own usage only. |

### Permission Matrix

| Feature | Application Owner | Workspace Admin | Workspace Member |
| :--- | :--- | :--- | :--- |
| **Manage Global API Keys (GlobalModel CRUD)** | ✅ Full Access | ❌ Denied | ❌ Denied |
| **Create Workspaces** | ❌ Denied | ✅ (any user can create) | ✅ (any user can create) |
| **Add/Remove Workspace Members** | ❌ Denied | ✅ Own workspace only | ❌ Denied |
| **Delete Workspace** | ❌ Denied | ✅ Own workspace only | ❌ Denied |
| **Configure Workspace Allowed Models** | ❌ Denied | ✅ From Owner's global list | ❌ Denied |
| **Stream Chats (WebSocket)** | ❌ Denied | ✅ Full Access | ✅ Full Access |
| **View Financial Analytics** | ✅ All workspaces, all users | ✅ Workspace total + per-user breakdown | 🔒 Own token usage only |

### Access Control Rules

| Action | Who |
| :--- | :--- |
| Create a workspace | Any authenticated user (becomes admin) |
| Add/remove members | Workspace admin only |
| Delete workspace | Workspace admin only |
| Configure allowed models | Workspace admin only (restricted to Owner's global list) |
| View/create conversations & messages | Any workspace member |
| View own usage (tokens used) | Any workspace member |
| View workspace total & per-user breakdown | Workspace admin only |
| View all workspaces' usage | Application Owner only |

---

## 5. Monorepo Directory Structure

```text
multi-tenant-research-app/
├── frontend/                          # Next.js Application (Managed via npm)
│   ├── src/
│   │   ├── app/
│   │   │   ├── (auth)/               # Route group for authentication
│   │   │   │   ├── login/page.tsx
│   │   │   │   └── register/page.tsx
│   │   │   ├── (dashboard)/          # Route group for the main application
│   │   │   │   ├── layout.tsx        # Sidebar and navigation shell
│   │   │   │   ├── chat/[id]/page.tsx # Active conversation view
│   │   │   │   ├── workspaces/page.tsx
│   │   │   │   └── usage/page.tsx    # Member/Admin financial dashboards
│   │   │   └── owner/                # Isolated Super-Owner portal
│   │   │       └── page.tsx
│   │   ├── components/
│   │   │   ├── ui/                   # Base components generated by shadcn/ui
│   │   │   ├── chat/                 # Chat-specific components (message bubbles, input)
│   │   │   └── workspace/            # Workspace management components
│   │   ├── store/
│   │   │   └── chatStore.ts          # Zustand store managing WebSocket & messages
│   │   ├── hooks/
│   │   │   └── useWebsocket.ts       # Hook to interface with chatStore
│   │   └── lib/
│   │       └── api.ts                # Fetch/Axios client for REST calls
│   ├── package.json
│   ├── components.json               # shadcn/ui configuration
│   └── .env.local
│
├── backend/                           # FastAPI & Temporal (Managed via uv)
│   ├── src/
│   │   ├── modules/
│   │   │   ├── auth/                 # Standard Layered Module
│   │   │   │   ├── router.py
│   │   │   │   ├── service.py
│   │   │   │   ├── repository.py
│   │   │   │   ├── models.py         # User SQLModel
│   │   │   │   └── schemas.py        # Pydantic request/response DTOs
│   │   │   │
│   │   │   ├── workspaces/           # Standard Layered Module
│   │   │   │   ├── router.py
│   │   │   │   ├── service.py
│   │   │   │   ├── repository.py
│   │   │   │   ├── models.py         # Workspace, WorkspaceUserLink, WorkspaceModelLink
│   │   │   │   └── schemas.py
│   │   │   │
│   │   │   ├── conversations/        # Standard Layered Module + WebSocket
│   │   │   │   ├── router.py         # REST + WebSocket endpoints
│   │   │   │   ├── service.py        # Orchestrates LLM calls, message persistence
│   │   │   │   ├── repository.py
│   │   │   │   ├── models.py         # Conversation, Message SQLModels
│   │   │   │   ├── schemas.py
│   │   │   │   └── connection_manager.py  # WebSocket connection & presence tracking
│   │   │   │
│   │   │   ├── llm/                  # Selective Hexagonal Boundary
│   │   │   │   ├── ports.py          # Abstract LLMProvider interface
│   │   │   │   ├── model_registry.py # Exposes valid LiteLLM model identifiers
│   │   │   │   └── adapters/
│   │   │   │       └── litellm_adapter.py  # Concrete implementation
│   │   │   │
│   │   │   ├── usage/                # Temporal Orchestration Module
│   │   │   │   ├── router.py         # Usage query endpoints (member/admin views)
│   │   │   │   ├── service.py        # Visibility rules & aggregation logic
│   │   │   │   ├── repository.py     # Usage fetch queries
│   │   │   │   ├── models.py         # UsageLedger SQLModel
│   │   │   │   ├── schemas.py
│   │   │   │   ├── workflows.py      # Temporal billing workflow definition
│   │   │   │   └── activities.py     # Temporal billing activity (cost calculation)
│   │   │   │
│   │   │   └── admin/                # Application Owner endpoints
│   │   │       ├── router.py         # Global API key CRUD + cross-workspace analytics
│   │   │       └── schemas.py
│   │   │
│   │   ├── shared/
│   │   │   ├── db/
│   │   │   │   ├── engine.py         # PostgreSQL async engine & session factory
│   │   │   │   └── migrations/       # Alembic migration versions
│   │   │   ├── middleware/
│   │   │   │   ├── auth.py           # JWT cookie extraction & dependency injection
│   │   │   │   └── error_handler.py  # Global exception handlers
│   │   │   └── config/
│   │   │       └── settings.py       # Pydantic Settings for env vars
│   │   │
│   │   └── main.py                   # FastAPI app factory + Temporal worker startup
│   │
│   ├── scripts/
│   │   └── create_owner.py           # CLI script to seed Application Owner
│   ├── tests/                        # Pytest test suites
│   ├── alembic.ini                   # Alembic configuration
│   ├── pyproject.toml                # Python dependencies
│   └── .env
│
├── docker-compose.yml                # PostgreSQL + Temporal cluster
└── README.md
```

---

## 6. Database Schema (SQLModel)

All primary keys use **UUID v4**. All timestamps use **timezone-aware UTC** (`datetime.now(timezone.utc)`). Financial fields use **`Decimal`** (`NUMERIC(12,6)` in PostgreSQL). Models are **distributed** across feature modules.

### `modules/auth/models.py`

```python
import uuid
from datetime import datetime, timezone
from typing import List, Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from src.modules.workspaces.models import Workspace
    from src.modules.conversations.models import Message

class User(SQLModel, table=True):
    __tablename__ = "users"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    username: str = Field(max_length=15, unique=True, index=True, nullable=False)
    email: str = Field(unique=True, nullable=False)
    hashed_password: str = Field(nullable=False)          # bcrypt via passlib
    is_owner: bool = Field(default=False, nullable=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)

    workspaces: List["Workspace"] = Relationship(
        back_populates="members",
        link_model="WorkspaceUserLink"
    )
    messages: List["Message"] = Relationship(back_populates="sender")
```

### `modules/workspaces/models.py`

```python
import uuid
from datetime import datetime, timezone
from typing import List, Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from src.modules.auth.models import User
    from src.modules.conversations.models import Conversation

class WorkspaceUserLink(SQLModel, table=True):
    __tablename__ = "workspace_user_links"
    workspace_id: uuid.UUID = Field(foreign_key="workspaces.id", primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", primary_key=True)

class WorkspaceModelLink(SQLModel, table=True):
    __tablename__ = "workspace_model_links"
    workspace_id: uuid.UUID = Field(foreign_key="workspaces.id", primary_key=True)
    model_id: uuid.UUID = Field(foreign_key="global_models.id", primary_key=True)

class Workspace(SQLModel, table=True):
    __tablename__ = "workspaces"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(nullable=False)
    admin_id: uuid.UUID = Field(foreign_key="users.id", nullable=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)

    members: List["User"] = Relationship(
        back_populates="workspaces",
        link_model=WorkspaceUserLink
    )
    allowed_models: List["GlobalModel"] = Relationship(link_model=WorkspaceModelLink)
    conversations: List["Conversation"] = Relationship(
        back_populates="workspace",
        cascade_delete=True
    )

class GlobalModel(SQLModel, table=True):
    __tablename__ = "global_models"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    llm_company_name: str = Field(nullable=False)         # e.g., "OpenAI", "Anthropic"
    model_type: str = Field(nullable=False)               # e.g., "chat", "completion"
    model_name: str = Field(unique=True, nullable=False, index=True)  # LiteLLM identifier
    api_key: str = Field(nullable=False)

    requires_manual_pricing: bool = Field(default=False, nullable=False)
    fallback_input_cost_per_million: Optional[float] = Field(default=None, nullable=True)
    fallback_output_cost_per_million: Optional[float] = Field(default=None, nullable=True)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)
```

### `modules/conversations/models.py`

```python
import uuid
from datetime import datetime, timezone
from typing import List, Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from src.modules.workspaces.models import Workspace
    from src.modules.auth.models import User

class Conversation(SQLModel, table=True):
    __tablename__ = "conversations"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    title: str = Field(nullable=False)
    workspace_id: uuid.UUID = Field(foreign_key="workspaces.id", ondelete="CASCADE", nullable=False)
    created_by: uuid.UUID = Field(foreign_key="users.id", nullable=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)

    workspace: "Workspace" = Relationship(back_populates="conversations")
    messages: List["Message"] = Relationship(back_populates="conversation", cascade_delete=True)

class Message(SQLModel, table=True):
    __tablename__ = "messages"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    conversation_id: uuid.UUID = Field(foreign_key="conversations.id", ondelete="CASCADE", nullable=False)
    sender_id: uuid.UUID = Field(foreign_key="users.id", nullable=False)
    sender_name: str = Field(nullable=False)
    prompt_text: str = Field(nullable=False)
    response_text: str = Field(nullable=False)
    model_used: str = Field(nullable=False)               # LiteLLM model identifier
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)

    conversation: Conversation = Relationship(back_populates="messages")
    sender: "User" = Relationship(back_populates="messages")
```

### `modules/usage/models.py`

```python
import uuid
from decimal import Decimal
from datetime import datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Field

class UsageLedger(SQLModel, table=True):
    __tablename__ = "usage_ledger"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    workspace_id: Optional[uuid.UUID] = Field(
        default=None,
        foreign_key="workspaces.id",
        ondelete="SET NULL",                               # Immutable ledger: survives workspace deletion
        nullable=True
    )
    user_id: uuid.UUID = Field(foreign_key="users.id", nullable=False)
    model_name: str = Field(nullable=False)
    message_id: Optional[uuid.UUID] = Field(
        default=None,
        foreign_key="messages.id",
        ondelete="SET NULL",                               # Immutable ledger: survives message deletion
        nullable=True
    )
    prompt_tokens: int = Field(default=0, nullable=False)
    completion_tokens: int = Field(default=0, nullable=False)
    total_tokens: int = Field(default=0, nullable=False)
    calculated_cost: Decimal = Field(default=Decimal("0.000000"), nullable=False)  # NUMERIC(12,6)
    is_flagged_error: bool = Field(default=False, nullable=False)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)
```

---

## 7. REST API Endpoints

All REST endpoints use the `/api/` prefix. All responses follow a standard envelope:

```json
// Success
{"success": true, "data": { ... }}

// Error
{"success": false, "error": {"message": "...", "detail": [...]}}
```

### `modules/auth/router.py`

| Method | Endpoint | Description | Auth |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/auth/register` | Register new user. Auto-login (sets HttpOnly cookie). | Public |
| `POST` | `/api/auth/login` | Login. Sets HttpOnly JWT cookie. | Public |
| `POST` | `/api/auth/logout` | Clears JWT cookie. | Authenticated |
| `GET` | `/api/auth/me` | Get current user profile from JWT. | Authenticated |

### `modules/workspaces/router.py`

| Method | Endpoint | Description | Auth |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/workspaces` | Create workspace (caller becomes admin). | Authenticated |
| `GET` | `/api/workspaces` | List workspaces the current user belongs to. | Authenticated |
| `GET` | `/api/workspaces/{workspace_id}` | Get workspace details. | Workspace Member |
| `DELETE` | `/api/workspaces/{workspace_id}` | Delete workspace. | Workspace Admin |
| `POST` | `/api/workspaces/{workspace_id}/members` | Add a user to the workspace. | Workspace Admin |
| `DELETE` | `/api/workspaces/{workspace_id}/members/{user_id}` | Remove a user. | Workspace Admin |
| `GET` | `/api/workspaces/{workspace_id}/members` | List workspace members. | Workspace Member |
| `GET` | `/api/workspaces/{workspace_id}/models` | List allowed models for this workspace. | Workspace Member |
| `POST` | `/api/workspaces/{workspace_id}/models` | Add a model to the workspace's allowed list. | Workspace Admin |
| `DELETE` | `/api/workspaces/{workspace_id}/models/{model_id}` | Remove a model from allowed list. | Workspace Admin |

### `modules/conversations/router.py`

| Method | Endpoint | Description | Auth |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/workspaces/{workspace_id}/conversations` | Create a new conversation. | Workspace Member |
| `GET` | `/api/workspaces/{workspace_id}/conversations` | List conversations in a workspace. | Workspace Member |
| `GET` | `/api/conversations/{conversation_id}` | Get conversation with message history. | Workspace Member |
| `DELETE` | `/api/conversations/{conversation_id}` | Delete a conversation. | Workspace Member |
| `WebSocket` | `/ws/chat/{conversation_id}` | Real-time streaming chat. Auth via HttpOnly cookie on handshake. | Workspace Member |

### `modules/usage/router.py`

| Method | Endpoint | Description | Auth |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/workspaces/{workspace_id}/usage/me` | Get current user's own usage summary. | Workspace Member |
| `GET` | `/api/workspaces/{workspace_id}/usage` | Get workspace-wide usage + per-user breakdown. | Workspace Admin |

### `modules/admin/router.py`

| Method | Endpoint | Description | Auth |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/admin/models` | List all global models (with API keys masked). | Owner Only |
| `POST` | `/api/admin/models` | Add a new global model + API key. | Owner Only |
| `PUT` | `/api/admin/models/{model_id}` | Update a global model. | Owner Only |
| `DELETE` | `/api/admin/models/{model_id}` | Delete a global model (cascades to workspace links). | Owner Only |
| `GET` | `/api/admin/usage` | Cross-workspace financial analytics (all workspaces). | Owner Only |
| `GET` | `/api/admin/usage/{workspace_id}` | Single workspace financial breakdown. | Owner Only |

---

## 8. WebSocket Protocol

### Connection

```
URL: /ws/chat/{conversation_id}
Auth: HttpOnly JWT cookie (sent automatically by the browser on handshake)
```

The server extracts `user_id` from the JWT cookie and `workspace_id` from the conversation's FK. No user/workspace IDs in the URL.

### Message Format (JSON)

**Client → Server:**

```json
{
  "type": "send_message",
  "model": "gpt-4o",
  "prompt": "Explain quantum computing"
}
```

**Server → Client (streaming chunk):**

```json
{
  "type": "message_chunk",
  "content": "Quantum computing is..."
}
```

**Server → Client (stream complete):**

```json
{
  "type": "message_complete",
  "message_id": "uuid-here",
  "model_used": "gpt-4o"
}
```

**Server → Client (presence broadcast — workspace-scoped):**

```json
{
  "type": "presence_update",
  "active_users": [
    {"id": "uuid", "username": "alice"},
    {"id": "uuid", "username": "bob"}
  ]
}
```

**Server → Client (error):**

```json
{
  "type": "error",
  "detail": "Model gpt-4o is not allowed in this workspace"
}
```

---

## 9. System Data Flows

### A. Real-Time Chat & Streaming Pipeline

1. **Connection:** Client establishes a WebSocket to `/ws/chat/{conversation_id}`. Server authenticates via JWT cookie, validates workspace membership.
2. **Presence:** `ConnectionManager` logs the user and broadcasts a `presence_update` to all active users in that workspace.
3. **Prompt Received:** User sends `{"type": "send_message", "model": "gpt-4o", "prompt": "..."}`.
4. **Model Validation:** `conversations` service checks the model against `workspace_allowed_models`. If not allowed, sends `error` frame.
5. **History Assembly:** `conversations` service fetches previous messages from DB and builds the `messages` array. Uses `litellm.trim_messages()` to fit within the model's context window.
6. **LLM Call:** Service invokes the `LLMProvider` port → `litellm_adapter` executes `litellm.acompletion(model, messages, stream=True)` using the API key from `GlobalModel`.
7. **Streaming:** As chunks yield, server sends `message_chunk` frames over WebSocket.
8. **Persistence:** On completion, full prompt + response saved to `Message` table. Server sends `message_complete` frame.
9. **Billing Dispatch:** Token usage captured. Temporal workflow dispatched with raw token counts + model name.

### B. Asynchronous Financial Ledger Pipeline (Temporal)

1. **Dispatch:** `conversations` service starts a Temporal workflow (in `modules/usage/workflows.py`) with: `workspace_id`, `user_id`, `message_id`, `model_name`, `prompt_tokens`, `completion_tokens`.
2. **Cost Calculation (Temporal Activity in `modules/usage/activities.py`):**
   - **Step 1:** Look up `model_name` in `litellm.model_cost`. If found, extract `input_cost_per_token` and `output_cost_per_token`.
   - **Step 2:** If not found in LiteLLM, query the `GlobalModel` DB table for `fallback_input_cost_per_million` and `fallback_output_cost_per_million`.
   - **Step 3:** Calculate: `cost = (prompt_tokens × input_rate + completion_tokens × output_rate) / 1_000_000`.
3. **Persistence:** Activity commits a `UsageLedger` record with tokens, cost, and metadata.
4. **Crash Circuit Breaker:** If the LLM stream drops mid-generation, `conversations` service dispatches the workflow with `0` tokens and `is_flagged_error=True`.

### C. Model Selection Flow

1. User sends a message specifying a model.
2. `conversations` service checks the model against `workspace_allowed_models` for that workspace.
3. If not allowed → rejected before any LLM call.
4. If allowed → `conversations` calls `LLMProvider.generate(model, messages)`.

### D. Visibility Rules (in `usage` module)

- **Member view:** `SUM(tokens), SUM(cost) FROM usage_ledger WHERE workspace_id = X AND user_id = current_user`
- **Admin view:** `SELECT user_id, SUM(tokens), SUM(cost) FROM usage_ledger WHERE workspace_id = X GROUP BY user_id` + overall total
- **Owner view:** All workspaces, all users, full breakdown

---

## 10. LLM Integration Details (`modules/llm/`)

### Port Interface (`ports.py`)

```python
from abc import ABC, abstractmethod
from typing import AsyncIterator
from dataclasses import dataclass

@dataclass
class LLMUsage:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

@dataclass
class LLMStreamResult:
    content: str          # Full assembled response text
    usage: LLMUsage

class LLMProvider(ABC):
    @abstractmethod
    async def stream(
        self,
        model: str,
        messages: list[dict],
        api_key: str
    ) -> AsyncIterator[str]:
        """Yields content chunks as strings."""
        ...

    @abstractmethod
    def get_usage(self) -> LLMUsage:
        """Returns token usage after stream completes."""
        ...
```

### Adapter (`adapters/litellm_adapter.py`)

- The **sole place** that calls `litellm.acompletion()`.
- Resolves provider credentials from the `api_key` passed in (sourced from `GlobalModel` by the `conversations` service).
- Catches LiteLLM's normalized exception types and translates them into the application's own error types.
- Uses `litellm.trim_messages()` for context window management.

### Model Registry (`model_registry.py`)

- Exposes the list of valid LiteLLM model identifiers (sourced from `litellm.model_cost`).
- Used by the `admin` module's UI to validate model names before the Owner adds them to `GlobalModel`.

---

## 11. Environment Variables

### Backend (`backend/.env`)

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/research_platform
JWT_SECRET_KEY=your_super_secret_jwt_string
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
TEMPORAL_HOST=localhost:7233
TEMPORAL_TASK_QUEUE=billing-tasks
```

### Frontend (`frontend/.env.local`)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

---

## 12. Setup & Development Guide

### A. Infrastructure

```bash
# Start PostgreSQL and Temporal cluster
docker-compose up -d
```

### B. Backend (using `uv`)

```bash
cd backend
uv venv
# Windows: .venv\Scripts\activate | Linux/Mac: source .venv/bin/activate
uv sync                          # Install from pyproject.toml

# Initialize Alembic migrations
alembic upgrade head

# Seed the Application Owner
python scripts/create_owner.py \
  --username "master_admin" \
  --email "admin@researchapp.com" \
  --password "SecurePass123!"
# Note: Username Max 15 chars, Password Max 20 chars

# Start FastAPI (includes Temporal worker in event loop)
fastapi dev src/main.py
```

### C. Frontend (using `npm`)

```bash
cd frontend
npm install
npm run dev
```

---

## 13. Testing Strategy

### Backend (`pytest`)

```bash
cd backend
uv run pytest tests/ -v
```

- **Unit tests:** Access control rules, model-allowlist checks, cost aggregation, visibility rules — tested with fake repositories and a fake `LLMProvider`, no database or network calls.
- **Adapter tests:** `litellm_adapter` tested against LiteLLM (mocked or against real models in a separate, less frequent test suite).
- **Integration tests:** API endpoints tested against a test database, covering the full request flow including role-based access.

### Frontend (`Jest`)

```bash
cd frontend
npm run test
```

---

## 14. Design Decisions Log

| # | Decision | Rationale |
| :--- | :--- | :--- |
| 1 | Modular Monolith over full Hexagonal | Avoids boilerplate for CRUD modules; Hexagonal only where it matters (LLM boundary) |
| 2 | Distributed SQLModels (per-module) | Architectural purity; each module owns its data model |
| 3 | WebSockets for streaming | Best UX for real-time LLM chat |
| 4 | Temporal IO for billing | Crash protection, retry guarantees, audit trail for financial data |
| 5 | Temporal worker in FastAPI event loop | Simplifies local development without separate process |
| 6 | JWT in HttpOnly Secure cookie | Maximum XSS protection; no token in localStorage |
| 7 | Auto-login after registration | Better UX; cookie set immediately on signup |
| 8 | Open registration | Any user can sign up; workspace RBAC handles access from there |
| 9 | `/ws/chat/{conversation_id}` (simplified) | Secure by design; user from cookie, workspace from conversation FK |
| 10 | Server-side conversation history | Uses `litellm.trim_messages()` to manage context windows |
| 11 | `litellm.model_cost` for pricing | Dictionary lookup with DB fallback for unknown models |
| 12 | UUID v4 primary keys | Globally unique, no information leakage |
| 13 | `Decimal` for financial fields | Avoids floating-point precision errors |
| 14 | `bcrypt` via passlib | Industry standard, brute-force resistant |
| 15 | `datetime.now(timezone.utc)` | Modern Python 3.12+ standard, timezone-aware |
| 16 | Tailwind CSS v4 | CSS-first configuration, latest features |
| 17 | Alembic for migrations | Safe, reversible schema evolution |
| 18 | `SET NULL` on UsageLedger FKs | Financial records survive workspace/message deletion |
| 19 | `model_registry` in `llm` module | Validates model names before Owner adds them to GlobalModel |
| 20 | Standard JSON envelope for REST | Consistent `{success, data, error}` response shape |
| 21 | Presence scoped to workspace | All users in a workspace see who's online, regardless of conversation |
| 22 | `workspaces` module owns allowed-models | Admin module is only for Owner super-admin endpoints |
