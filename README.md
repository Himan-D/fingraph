# FinGraph Terminal

A Bloomberg-style terminal for Indian stock market with knowledge graph capabilities.

## Features

- **Real-time Market Data** - Live NSE/BSE quotes via TrueData
- **Knowledge Graph** - Entity relationships (promoters, subsidiaries, KMP)
- **AI Assistant** - Natural language queries and financial summarization
- **Stock Screener** - Filter stocks by fundamentals
- **Option Chain** - F&O analysis with Greeks

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python FastAPI |
| Frontend | React + Electron |
| Database | PostgreSQL |
| Graph DB | Neo4j Aura |
| Vector DB | Qdrant |
| AI | OpenAI GPT-4 |
| Real-time | TrueData WebSocket |

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- Docker & Docker Compose

### 1. Clone & Install

```bash
cd /Users/himand/fingraph

# Backend
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install
```

### 2. Start Databases

```bash
docker-compose -f docker/docker-compose.yml up -d
```

### 3. Configure Environment

```bash
cp backend/.env.example backend/.env
# Edit .env with your API keys
```

Required keys:
- `NEO4J_URI` - Neo4j Aura connection string
- `NEO4J_PASSWORD` - Neo4j password
- `TRUEDATA_USERNAME` / `TRUEDATA_PASSWORD` - TrueData credentials
- `OPENAI_API_KEY` - OpenAI API key

### 4. Run Development Servers

```bash
# Terminal 1: Backend
cd backend
uvicorn main:app --reload

# Terminal 2: Frontend
cd frontend
npm run dev
```

### 5. Open Browser

Visit http://localhost:5173

## Project Structure

```
fingraph/
├── backend/           # FastAPI backend
│   ├── api/          # API routes
│   ├── core/         # Business logic
│   ├── db/           # Database clients
│   └── utils/        # Utilities
├── frontend/         # React + Electron
│   ├── src/
│   │   ├── components/
│   │   ├── hooks/
│   │   └── store/
│   └── electron/
├── docker/           # Docker configs
├── scripts/          # Utility scripts
└── docs/            # Documentation
```

## API Endpoints

### Quotes
- `GET /api/v1/quotes/{symbol}` - Live quote
- `GET /api/v1/quotes/batch` - Batch quotes
- `GET /api/v1/quotes/indices` - Index values
- `GET /api/v1/quotes/historical/{symbol}` - Historical data

### Fundamentals
- `GET /api/v1/company/{symbol}` - Company profile
- `GET /api/v1/fundamentals/{symbol}` - Financial ratios
- `GET /api/v1/shareholding/{symbol}` - Shareholding

### Knowledge Graph
- `GET /api/v1/graph/company/{symbol}` - Company relationships
- `GET /api/v1/graph/promoter/{name}` - Promoter network

### AI
- `POST /api/v1/ai/query` - Natural language query
- `GET /api/v1/ai/summarize/{symbol}` - Financial summary

## Environment Variables

See `backend/.env.example` for all configuration options.

## License

MIT
