# FinGraph Terminal — Agent Development Guide

## Project Overview

FinGraph is a Bloomberg-style terminal for the Indian stock market (NSE/BSE) with an AI-powered agentic layer. The agent uses OpenAI GPT-4 with function-calling to provide natural language access to market data, risk analytics, knowledge graphs, predictions, and trading signals.

## Architecture

```
Frontend (React/Vite :5173)
  ↕ SSE streaming + REST
Backend (FastAPI :8000)
  ├── AgentOrchestrator — GPT-4 function-calling loop
  │   ├── agent_tools.py — 12 tool definitions + implementations
  │   └── agent_orchestrator.py — streaming orchestration
  ├── Auth — JWT (python-jose) + bcrypt
  ├── Databases:
  │   ├── PostgreSQL — companies, quotes, fundamentals, conversations, users
  │   ├── Neo4j — knowledge graph (promoters, KMP, sectors, relationships)
  │   ├── Qdrant — vector search (semantic document retrieval)
  │   └── Redis — caching + rate limiting
  └── Background:
      ├── Scheduler (APScheduler) — news, prices, sentiment, alerts
      ├── SentimentEngine — GPT-4o-mini batch sentiment
      └── AlertEngine — proactive AI-generated alerts
```

## Key Files

### Backend Agent System
| File | Purpose |
|------|---------|
| `backend/core/services/agent_tools.py` | 12 OpenAI function-tool definitions + async implementations |
| `backend/core/services/agent_orchestrator.py` | GPT-4 function-calling loop with streaming SSE |
| `backend/core/services/auth.py` | JWT auth, password hashing, user management |
| `backend/core/services/sentiment.py` | AI-powered news sentiment (GPT-4o-mini batch) |
| `backend/core/services/alert_engine.py` | Proactive AI alert generation |
| `backend/api/routes/agent.py` | Streaming chat endpoint + conversation management |
| `backend/api/routes/auth.py` | Login/signup/refresh endpoints |
| `backend/db/postgres_models.py` | All ORM models including User, Conversation, Message, AIAlert |

### Frontend
| File | Purpose |
|------|---------|
| `frontend/src/components/AIChat/AIChat.tsx` | Streaming chat with SSE, markdown, tool cards |
| `frontend/src/components/Auth/LoginForm.tsx` | Login/signup UI |
| `frontend/src/services/api.ts` | Centralized API client with auth interceptor |

### Data Flow
```
User message → POST /agent/chat (SSE)
  → AgentOrchestrator receives message + history
  → Calls GPT-4 with tools= parameter
  → If tool_calls returned:
      → Execute tool (e.g., get_quote("RELIANCE"))
      → Feed result back to GPT-4
      → Repeat (max 5 rounds)
  → Stream final response tokens to frontend
  → Store message in Conversation/Message tables
```

## Agent Tools

| Tool | What it does | Source Service |
|------|-------------|----------------|
| `get_quote` | Live stock quote (price, OHLCV, market cap) | `api/routes/quotes.py` |
| `get_fundamentals` | PE, PB, ROE, debt/equity, EPS | `api/routes/fundamentals.py` |
| `get_historical` | Historical OHLCV data | `api/routes/quotes.py` |
| `get_option_chain` | F&O chain with OI/volume | `api/routes/quotes.py` |
| `run_risk_analysis` | Monte Carlo + VaR + stress test | `core/services/risk_engine.py` |
| `run_monte_carlo` | Price simulation with probabilities | `core/services/risk_engine.py` |
| `get_company_graph` | Knowledge graph relationships | `core/services/graph_service.py` |
| `search_news` | Search news articles | `api/routes/news.py` |
| `run_screener` | Filter stocks by fundamentals | `api/routes/screener.py` |
| `get_prediction` | Stock/commodity prediction score | `core/services/prediction.py` |
| `get_trading_signals` | Buy/sell/hold signals | `core/services/signals.py` |
| `get_sentiment` | Social sentiment analysis | `core/services/social_pipeline.py` |

## Database Models

### User
```python
class User(Base):
    __tablename__ = "users"
    id, email, password_hash, name, plan, created_at, updated_at
```

### Conversation
```python
class Conversation(Base):
    __tablename__ = "conversations"
    id, user_id, title, symbol, created_at, updated_at
```

### Message
```python
class Message(Base):
    __tablename__ = "messages"
    id, conversation_id, role, content, tool_calls(JSON), 
    tool_results(JSON), tokens_used, created_at
```

### AIAlert
```python
class AIAlert(Base):
    __tablename__ = "ai_alerts"
    id, user_id, symbol, alert_type, severity, title, 
    summary, data(JSON), is_read, created_at
```

## API Endpoints

### Agent
- `POST /api/v1/agent/chat` — Streaming chat (SSE)
- `GET /api/v1/agent/conversations` — List conversations
- `GET /api/v1/agent/conversations/{id}` — Get messages
- `DELETE /api/v1/agent/conversations/{id}` — Delete conversation

### Auth
- `POST /api/v1/auth/signup` — Create account
- `POST /api/v1/auth/login` — Get JWT tokens
- `POST /api/v1/auth/refresh` — Refresh access token
- `GET /api/v1/auth/me` — Current user profile

### AI
- `GET /api/v1/ai/alerts` — User's AI alerts
- `POST /api/v1/ai/alerts/{id}/read` — Mark alert read

## Environment Variables

```env
# Required for AI features
OPENAI_API_KEY=sk-...

# Database (via Docker)
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/fingraph

# Auth
JWT_SECRET=<random-32-char-string>
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
```

## Running

```bash
# Infrastructure
docker compose -f docker/docker-compose.yml up -d

# Backend
cd backend
PYTHONPATH=. .venv311/bin/python -m uvicorn main:app --reload

# Frontend
cd frontend
npm run dev

# Open http://localhost:5173
```

## Testing

```bash
# Backend tests
cd backend && PYTHONPATH=. .venv311/bin/python -m pytest tests/ -v

# Type check frontend
cd frontend && npx tsc --noEmit
```

## Coding Standards

- Python: Follow existing FastAPI patterns in `api/routes/`
- All new endpoints use `AsyncSession` for DB access
- Tool implementations must handle errors gracefully (return error dict, not raise)
- Agent orchestrator has a max 5 tool-call rounds per message
- Frontend: React functional components with hooks, Tailwind CSS, dark theme
