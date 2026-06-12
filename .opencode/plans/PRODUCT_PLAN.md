# FinGraph Terminal — Product & Technical Plan

## Vision

Build India's first AI-native financial terminal that combines:
- **Zerodha's depth** (professional-grade trading, advanced charts, F&O)
- **Groww's simplicity** (clean UX, onboarding, SIP/mutual funds)
- **Bloomberg's intelligence** (AI agent, knowledge graph, risk analytics)

...but with an agentic layer that makes every interaction intelligent.

---

## User Personas (Phased)

| Phase | Persona | Priority | Timeline |
|-------|---------|----------|----------|
| **P1** | AI-native analyst | Core | Weeks 1-8 |
| **P2** | Active trader (Kite-like) | High | Weeks 9-16 |
| **P3** | Retail investor (Groww-like) | Medium | Weeks 17-24 |

---

## Revenue Model: API Marketplace

| Tier | Price | API Calls/Day | AI Queries | Real-time | Features |
|------|-------|---------------|------------|-----------|----------|
| **Free** | ₹0 | 100 | 5/day | Delayed 15min | Basic quotes, screener |
| **Developer** | ₹999/mo | 10,000 | 100/day | Real-time | All data endpoints, no trading |
| **Pro** | ₹2,499/mo | 100,000 | Unlimited | Real-time | + Trading APIs, AI portfolio management |
| **Enterprise** | Custom | Unlimited | Unlimited | Real-time | + Dedicated infra, custom models |

---

## Architecture Overview

```
                    ┌──────────────────────────────────┐
                    │         React Frontend            │
                    │   Terminal / Mobile / API Docs    │
                    └──────────────┬───────────────────┘
                                   │ SSE + REST
                    ┌──────────────▼───────────────────┐
                    │        API Gateway (FastAPI)       │
                    │   Auth │ Rate Limit │ Router      │
                    └──────────────┬───────────────────┘
                                   │
          ┌────────────────────────┼────────────────────────┐
          │                        │                        │
┌─────────▼──────────┐ ┌──────────▼──────────┐ ┌──────────▼──────────┐
│   Agent Engine     │ │   Market Data       │ │   Trading Engine    │
│   GPT-4o + 18 tools│ │   TrueData + NSE    │ │   Broker Adapters   │
│   Conversation Mem │ │   Yahoo Finance     │ │   Order Management  │
│   Streaming SSE    │ │   Screener.in       │ │   Position Tracking │
└─────────┬──────────┘ └──────────┬──────────┘ └──────────┬──────────┘
          │                        │                        │
          └────────────────────────┼────────────────────────┘
                                   │
          ┌────────────────────────┼────────────────────────┐
          │                        │                        │
┌─────────▼──────────┐ ┌──────────▼──────────┐ ┌──────────▼──────────┐
│   PostgreSQL       │ │   Neo4j Graph       │ │   Redis + Qdrant   │
│   Companies        │ │   Promoters         │ │   Cache + Vectors   │
│   Quotes/Fundamentals│ │   Sectors           │ │   Embeddings        │
│   Users/Orders     │ │   Relationships     │ │   Semantic Search   │
└────────────────────┘ └────────────────────┘ └────────────────────┘
```

---

## Phase 1: AI-Native Analyst Terminal (Weeks 1-8)

### P1.1 — Production Foundation (Week 1-2)

#### Auth System (Real, Enforced)
**Current state**: Auth routes exist but no middleware enforces auth on any endpoint.

**Build**:
- JWT auth middleware (`middleware/auth_middleware.py`)
- Public routes: `/auth/*`, `/health`, `/api/v1/quotes/indices`, `/api/v1/search/trending`
- Protected routes: everything else (user-scoped data)
- API key auth for developer/marketplace users (`X-API-Key` header)
- Rate limiting per tier (Redis-based sliding window)
- Auth context propagation to tools (user_id, plan, rate limits)

**Files to create/modify**:
```
backend/middleware/auth_middleware.py      (NEW — JWT + API key verification)
backend/core/services/auth.py             (MODIFY — add get_current_user dependency)
backend/api/deps.py                       (NEW — FastAPI dependencies: get_user, require_plan)
backend/api/routes/*.py                   (MODIFY — add Depends(get_user) to all protected routes)
```

#### Database Hardening
**Current state**: Migrations work but no indexes on hot paths, no connection pooling config, seed data is manual.

**Build**:
- Add indexes: `stock_quotes(company_id, timestamp)`, `messages(conversation_id, created_at)`, `ai_alerts(user_id, is_read)`
- Connection pooling: `pool_size=20, max_overflow=40` for production
- Auto-seed on startup: run `seed.py` if `companies` table is empty
- Add `settings.py` environment profiles: `dev`, `staging`, `prod`

**Files**:
```
backend/alembic/versions/0004_add_production_indexes.py  (NEW)
backend/config.py                                        (MODIFY — add ENVIRONMENT)
backend/db/postgres.py                                   (MODIFY — pool config from env)
backend/main.py                                          (MODIFY — auto-seed in lifespan)
```

#### Error Handling & Observability
**Build**:
- Structured JSON logging (replace `print()` with proper logger)
- Request ID tracing (middleware adds X-Request-ID)
- Prometheus metrics endpoint (`/metrics`): request count, latency, error rate, DB pool usage
- Sentry integration for error tracking
- Health check improvements: check Neo4j, Qdrant, OpenAI API connectivity

**Files**:
```
backend/middleware/request_id.py    (NEW)
backend/middleware/metrics.py       (NEW — Prometheus)
backend/core/services/monitoring.py (MODIFY — comprehensive health)
backend/main.py                     (MODIFY — wire middleware)
```

### P1.2 — Data Pipeline (Week 2-3)

#### TrueData Real-time Feed
**Current state**: `truedata_service.py` exists as WebSocket client but not connected in production.

**Build**:
- Robust WebSocket reconnection with exponential backoff
- Subscribe to Nifty 50 + F&O stocks + indices
- Store tick data in Redis (latest price cache)
- Aggregate to 1-min OHLCV candles → PostgreSQL `stock_quotes`
- Feed into option chain, Greeks, real-time charts
- Graceful degradation: fall back to NSE HTTP API if TrueData disconnects

**Files**:
```
backend/core/services/truedata_service.py  (REWRITE — robust reconnection)
backend/core/services/market_cache.py      (NEW — Redis price cache)
backend/core/pipelines/price_pipeline.py   (NEW — tick aggregation)
backend/main.py                            (MODIFY — start pipeline in lifespan)
```

#### Fundamental Data Pipeline
**Current state**: Only 8 stocks have hardcoded `SAMPLE_FUNDAMENTALS`. Rest return nulls.

**Build**:
- Screener.in scraper (financial data) → scheduled daily at 6 AM
- NSE API for corporate actions, shareholding patterns
- Store quarterly results, annual reports
- AI extraction: parse PDF annual reports via GPT-4o → structured fundamentals
- Coverage: All Nifty 500 stocks

**Files**:
```
backend/core/scraper/screener_scraper.py    (REWRITE — robust, rate-limited)
backend/core/pipelines/fundamentals_pipeline.py  (NEW)
backend/core/scraper/nse_corporate.py       (NEW — corporate actions from NSE)
backend/core/services/pdf_extractor.py      (NEW — GPT-4o PDF parsing)
backend/core/scheduler.py                   (MODIFY — add fundamentals daily job)
```

#### News & Sentiment Pipeline
**Current state**: RSS scraper works, sentiment engine exists but not wired to scheduler.

**Build**:
- RSS feeds (18 sources) → every 30 min (works)
- NSE company announcements → every hour
- GPT-4o-mini sentiment on all new articles → `NewsArticle.sentiment`
- Entity extraction (stock symbols) → `NewsArticle.related_symbols`
- Store in Qdrant for semantic search
- Scheduler job: run `SentimentEngine.analyze_headlines()` on unprocessed articles

**Files**:
```
backend/core/pipelines/news_pipeline.py     (NEW — unified news processing)
backend/core/scheduler.py                   (MODIFY — wire sentiment job)
backend/core/services/sentiment.py          (MODIFY — batch process unprocessed)
```

### P1.3 — Agent Engine v2 (Week 3-4)

#### Enhanced Agent Tools
**Current state**: 12 tools exist but some have gaps (prediction is simple scoring, graph falls back to hardcoded data).

**Build**:
- `analyze_portfolio` — aggregate holdings, P&L, sector exposure, risk
- `backtest_strategy` — historical strategy simulation with metrics (Sharpe, max drawdown)
- `screen_technicals` — RSI, MACD, Bollinger Band scanner across all stocks
- `get_earnings_calendar` — upcoming quarterly results, historical surprises
- `search_documents` — semantic search via Qdrant over news, research reports
- `get_institutional_activity` — FII/DII data, bulk/block deals, MF holdings changes
- Improve existing tools: real prediction model (XGBoost), better graph queries

**Files**:
```
backend/core/services/agent_tools.py        (MODIFY — add 6 new tools)
backend/core/services/agent_orchestrator.py (MODIFY — support multi-step plans)
backend/core/services/backtest.py           (NEW — strategy backtesting)
backend/core/services/technical_scanner.py  (NEW — RSI/MACD/BB scanner)
backend/core/services/ml_prediction.py      (NEW — XGBoost prediction model)
```

#### Multi-step Agent Plans
**Build**:
- Agent can decompose complex queries into multi-step plans
- Example: "Research RELIANCE for investment" → plan: get_quote → get_fundamentals → get_historical → run_risk_analysis → search_news → get_trading_signals → synthesize report
- Streaming shows plan progress (step 1/6, step 2/6...)
- Plan results can be cached and shared across conversations

**Files**:
```
backend/core/services/agent_planner.py      (NEW — plan decomposition)
backend/core/services/agent_orchestrator.py (MODIFY — plan execution mode)
backend/api/routes/agent.py                 (MODIFY — plan execution endpoint)
```

#### Agent Memory & Context
**Current state**: Conversation history stored in DB but no long-term memory.

**Build**:
- User preferences: risk tolerance, sectors of interest, investment horizon
- Long-term memory: key insights per stock, user's past queries
- Market context injection: current Nifty level, VIX, FII/DII flow of the day
- Symbol resolution: "that bank stock I asked about yesterday" → HDFCBANK

**Files**:
```
backend/db/postgres_models.py               (MODIFY — add AgentMemory model)
backend/core/services/agent_memory.py       (NEW — preference + context management)
backend/core/services/agent_orchestrator.py (MODIFY — inject memory into prompts)
```

### P1.4 — Frontend Overhaul (Week 4-6)

#### Terminal Shell Redesign
**Current state**: Good Bloomberg-style dark theme but sidebar-heavy, not responsive.

**Build**:
- Command palette (Cmd+K): search stocks, tools, actions — like Raycast/Spotlight
- Tab system: open multiple stocks/tools as tabs
- Split pane: view chart + AI chat side by side
- Keyboard shortcuts: ESC to close, 1-9 for nav, / for search
- Responsive: collapse sidebar on small screens

**Files**:
```
frontend/src/components/Shell/CommandPalette.tsx   (NEW)
frontend/src/components/Shell/TabManager.tsx        (NEW)
frontend/src/components/Shell/SplitPane.tsx          (NEW)
frontend/src/components/Shell/KeyboardShortcuts.tsx  (NEW)
frontend/src/App.tsx                                (REWRITE — new shell)
frontend/src/hooks/useKeyboard.ts                   (NEW)
```

#### AI Chat v2
**Current state**: Streaming works, markdown renders, but no tool result visualization.

**Build**:
- Tool result cards: rich cards for each tool call (quote card, chart card, table card)
- Inline charts: sparklines for price data in chat
- Citation links: news articles, data sources
- Follow-up suggestions: agent suggests next questions
- Export: download analysis as PDF report

**Files**:
```
frontend/src/components/AIChat/ToolCards/QuoteCard.tsx        (NEW)
frontend/src/components/AIChat/ToolCards/ScreenerCard.tsx      (NEW)
frontend/src/components/AIChat/ToolCards/RiskCard.tsx          (NEW)
frontend/src/components/AIChat/ToolCards/NewsCard.tsx          (NEW)
frontend/src/components/AIChat/ToolCards/ComparisonTable.tsx   (NEW)
frontend/src/components/AIChat/InlineChart.tsx                 (NEW)
frontend/src/components/AIChat/FollowUpSuggestions.tsx         (NEW)
frontend/src/components/AIChat/AIChat.tsx                      (MODIFY — integrate cards)
```

#### Charts Enhancement
**Current state**: Lightweight Charts with basic indicators. Good but needs AI overlay.

**Build**:
- AI annotations on chart: "Earnings beat by 12%", "Promoter increased stake"
- Drawing tools: trend lines, Fibonacci, support/resistance markers
- Multi-timeframe: 1m, 5m, 15m, 1H, 1D, 1W, 1M
- Compare mode: overlay 2-5 stocks
- Volume profile, VWAP overlay

**Files**:
```
frontend/src/components/Charts/ChartAnnotations.tsx    (NEW)
frontend/src/components/Charts/DrawingTools.tsx         (NEW)
frontend/src/components/Charts/CompareChart.tsx         (NEW)
frontend/src/components/Charts/Charts.tsx               (MODIFY)
```

#### Portfolio Dashboard
**Current state**: No portfolio view at all.

**Build**:
- Holdings table with P&L, day change, sector breakdown
- Asset allocation pie chart
- Performance vs benchmark (Nifty 50)
- AI portfolio health score
- Sector exposure heatmap

**Files**:
```
frontend/src/components/Portfolio/Holdings.tsx        (NEW)
frontend/src/components/Portfolio/Allocation.tsx      (NEW)
frontend/src/components/Portfolio/Performance.tsx     (NEW)
frontend/src/components/Portfolio/HealthScore.tsx     (NEW)
frontend/src/components/Portfolio/Portfolio.tsx       (NEW — main page)
backend/api/routes/portfolio.py                       (NEW)
backend/core/services/portfolio.py                    (NEW)
```

### P1.5 — Knowledge Graph v2 (Week 6-7)

**Current state**: Neo4j works but seeded with only 10 companies' hardcoded data.

**Build**:
- Auto-populate from Company table (all Nifty 500)
- Promoter graph: cross-company directorships, family relationships
- Supply chain: sector-level supplier/customer relationships
- AI relationship extraction from news: "Company X signed deal with Company Y"
- Graph-powered insights: "Promoter of RELIANCE also owns X, Y, Z"
- Interactive graph explorer: D3 force graph with filtering

**Files**:
```
backend/core/services/graph_service.py               (REWRITE — auto-populate)
backend/core/services/graph_builder.py               (NEW — AI relationship extraction)
backend/core/pipelines/graph_pipeline.py             (NEW — scheduled graph building)
scripts/enrich_articles_finance_relations.py         (MODIFY — wire to scheduler)
frontend/src/components/Graph/GraphExplorer.tsx      (MODIFY — better UX)
```

### P1.6 — API Marketplace (Week 7-8)

**Current state**: Billing models exist but no actual API key auth or marketplace.

**Build**:
- API key generation and management (CRUD)
- Usage tracking: per-endpoint, per-day aggregation
- Rate limiting per tier (Redis sliding window)
- API documentation (OpenAPI/Swagger with examples)
- Developer dashboard: usage charts, API key management
- Webhook system: price alerts, order updates via webhook

**Files**:
```
backend/api/routes/api_keys.py          (NEW — API key CRUD)
backend/api/routes/usage.py             (NEW — usage stats endpoint)
backend/middleware/api_key_auth.py       (NEW — API key verification)
backend/middleware/rate_limiter.py       (MODIFY — per-tier Redis limits)
frontend/src/components/Developer/DeveloperDashboard.tsx  (NEW)
frontend/src/components/Developer/ApiKeyManager.tsx       (NEW)
frontend/src/components/Developer/UsageCharts.tsx         (NEW)
```

---

## Phase 2: Active Trading Terminal (Weeks 9-16)

### P2.1 — Broker Adapter Layer

**Build a unified trading interface** with adapters for 4 brokers:

```python
class BrokerAdapter(ABC):
    async def place_order(order: Order) -> OrderResponse
    async def cancel_order(order_id: str) -> bool
    async def get_positions() -> List[Position]
    async def get_orders() -> List[Order]
    async def get_holdings() -> List[Holding]
    async def get_margins() -> MarginInfo
    async def get_trade_book() -> List[Trade]
```

| Broker | Auth Method | Key Features |
|--------|------------|--------------|
| **Zerodha** | OAuth + access_token | Kite Connect API, WebSocket quotes |
| **Angel One** | JWT (SmartAPI) | Free API, good documentation |
| **Upstox** | OAuth 2.0 | Fast execution, good WebSocket |
| **Groww** | TBD | Growing API support |

**Files**:
```
backend/core/brokers/base.py              (NEW — abstract adapter)
backend/core/brokers/zerodha.py           (NEW)
backend/core/brokers/angel_one.py         (NEW)
backend/core/brokers/upstox.py            (NEW)
backend/core/brokers/groww.py             (NEW)
backend/core/brokers/broker_factory.py    (NEW — adapter selection)
backend/api/routes/broker.py              (NEW — broker management)
backend/db/postgres_models.py             (MODIFY — add BrokerAccount, Order, Position)
```

### P2.2 — Order Management System

**Build**:
- Unified order book: place, modify, cancel across all connected brokers
- Order types: MARKET, LIMIT, SL, SL-M, GTT (Good Till Triggered)
- Bracket orders, cover orders, AMO (After Market Order)
- Order validation: margin check, lot size, circuit limits
- Smart order routing: route to broker with best execution price
- Order history and audit trail

**Files**:
```
backend/core/services/oms.py              (NEW — order management)
backend/core/services/margin_calculator.py (NEW)
backend/core/services/order_validator.py   (NEW)
backend/api/routes/orders.py              (NEW)
backend/api/routes/positions.py           (NEW)
backend/db/postgres_models.py             (MODIFY — Order, Position, Trade models)
```

### P2.3 — Paper Trading Engine

**Build**:
- Virtual money: ₹10 lakh default, configurable
- Simulated order execution at market/limit price
- Slippage model: configurable % or fixed
- Brokerage simulation: Zerodha-equivalent charges
- Leaderboard: compare paper trading performance
- AI coaching: "Your stop losses are too tight", "You're overtrading"

**Files**:
```
backend/core/services/paper_trading.py    (NEW)
backend/api/routes/paper_trading.py       (NEW)
backend/db/postgres_models.py             (MODIFY — PaperAccount, PaperOrder)
frontend/src/components/PaperTrading/PaperDashboard.tsx  (NEW)
frontend/src/components/PaperTrading/PaperPnL.tsx        (NEW)
frontend/src/components/PaperTrading/Leaderboard.tsx     (NEW)
```

### P2.4 — Trading Terminal UI (Kite-like)

**Build**:
- **Workspace**: customizable grid layout (chart + orderbook + positions + AI chat)
- **Order entry panel**: buy/sell with all order types
- **Positions & Holdings**: real-time P&L, day change
- **Market depth**: Level 2 order book
- **Option chain**: with payoff diagram, strategy builder (straddle, strangle, iron condor)
- **F&O analytics**: OI analysis, PCR, max pain, IV skew
- **Scalper mode**: one-tap trade execution for intraday

**Files**:
```
frontend/src/components/Trading/TradingWorkspace.tsx    (NEW)
frontend/src/components/Trading/OrderEntry.tsx          (NEW)
frontend/src/components/Trading/PositionsPanel.tsx      (NEW)
frontend/src/components/Trading/MarketDepth.tsx         (NEW)
frontend/src/components/Trading/OptionPayoff.tsx        (NEW)
frontend/src/components/Trading/StrategyBuilder.tsx     (NEW)
frontend/src/components/Trading/ScalperMode.tsx         (NEW)
frontend/src/components/OptionChain/OptionChain.tsx     (MODIFY — strategy builder)
```

### P2.5 — AI Trading Assistant

**Build**:
- "What's the best F&O strategy for NIFTY expiry?" → agent builds strategy
- "Set a trailing stop loss for my RELIANCE position" → agent places GTT order
- "Hedge my portfolio against market crash" → agent suggests + executes protection
- "Alert me when NIFTY breaks 24500" → agent creates price alert
- Risk guard: "This trade uses 80% of your margin. Proceed?"

**Files**:
```
backend/core/services/agent_trading_tools.py   (NEW — 6 trading-specific tools)
backend/core/services/agent_tools.py            (MODIFY — add trading tools when broker connected)
backend/core/services/alert_service.py          (NEW — price alerts, condition alerts)
backend/api/routes/alerts.py                    (NEW)
```

---

## Phase 3: Retail Investor Platform (Weeks 17-24)

### P3.1 — Simplified Mobile-First UI

**Build**:
- Mobile-first responsive design (or React Native app)
- Onboarding flow: PAN verification, KYC, demat opening (via broker partner)
- Simple stock pages: price, 1-year chart, buy button, AI summary
- SIP/STP/SWP setup for mutual funds
- Goal-based investing: "Retirement in 20 years" → AI suggests allocation

### P3.2 — Mutual Fund & ETF Platform

**Build**:
- MF database: NAV history, fund managers, AUM, expense ratio
- MF screener: by category, returns, risk, AUM
- SIP calculator, lumpsum calculator
- Portfolio X-ray: overlap analysis, sector exposure
- AI MF recommendations based on risk profile

### P3.3 — Social & Community

**Build**:
- Leaderboard: top analysts, top paper traders
- Share analysis: generate shareable report cards
- Follow analysts: get notified of their trades/analyses
- Community Q&A: ask and answer investment questions

---

## Infrastructure Plan

### Docker Compose (Development)
Already working: PostgreSQL, Redis, Qdrant, Neo4j, Backend.

### Kubernetes (Production)
```
Namespace: fingraph-prod
├── API Pods (2-4 replicas, auto-scale on CPU)
│   └── FastAPI app with health checks
├── Worker Pods (2 replicas)
│   └── APScheduler + background jobs
├── Celery Workers (2-4 replicas)
│   └── Heavy tasks: ML prediction, backtesting, PDF parsing
├── Redis (managed ElastiCache)
├── PostgreSQL (managed RDS)
├── Neo4j (AuraDB or managed)
├── Qdrant (managed Qdrant Cloud)
└── Ingress (nginx) + SSL (Let's Encrypt)
```

### CI/CD Pipeline
```
GitHub → GitHub Actions → Docker Build → Push to ECR → Deploy to K8s
  ├── Lint (ruff + eslint)
  ├── Type check (mypy + tsc)
  ├── Test (pytest + vitest)
  ├── Build (docker build)
  └── Deploy (kubectl apply)
```

---

## Technical Debt to Clean Up

| Issue | File | Fix |
|-------|------|-----|
| `advanced_gds.py` crashes on `CommodityPrice.symbol` | `core/services/advanced_gds.py` | Fix JOIN to use `commodity_id` + join Commodity table |
| `SAMPLE_FUNDAMENTALS` hardcoded for 8 stocks | `api/routes/fundamentals.py` | Replace with Screener.in scraper data |
| `SAMPLE_GRAPH_DATA` hardcoded for 10 companies | `core/services/graph_service.py` | Replace with auto-populate from Company table |
| Static indices fallback | `api/routes/quotes.py` | Use TrueData or Redis cache for latest values |
| Random option chain mock | `api/routes/quotes.py` | Fetch real OI data from NSE API |
| Auth `/me` returns first user | `api/routes/auth.py` | Extract user from JWT token |
| No CORS for production | `main.py` | Configure from environment variable |
| `agent.py` unused rule-based agent | `core/services/agent.py` | Remove or archive — orchestrator replaces it |

---

## Priority Order for Implementation

### Immediate (Week 1-2)
1. **Auth middleware** — enforce JWT on all protected routes
2. **Auto-seed database** — no more manual seeding
3. **Production indexes** — add hot-path indexes
4. **TrueData robust connection** — real-time price pipeline
5. **Technical debt cleanup** — fix crashes, remove hardcoded data

### High Priority (Week 2-4)
6. **Fundamentals pipeline** — Screener.in scraper for 500+ stocks
7. **Agent memory** — user preferences, market context
8. **New agent tools** — backtest, technical scanner, portfolio analysis
9. **Command palette** — Cmd+K search
10. **Tool result cards** — rich visualization in AI chat

### Medium Priority (Week 4-8)
11. **Portfolio dashboard** — holdings, P&L, allocation
12. **Knowledge graph auto-populate** — all Nifty 500
13. **API marketplace** — keys, usage tracking, docs
14. **Frontend polish** — tabs, split pane, keyboard shortcuts
15. **Observability** — Prometheus, structured logging, Sentry

### Next Phase (Week 8-16)
16. **Broker adapters** — Zerodha, Angel One, Upstox, Groww
17. **Order management system**
18. **Paper trading engine**
19. **Trading terminal UI**
20. **AI trading tools**

---

## Key Metrics to Track

| Metric | Target (V1) | Target (V2) |
|--------|-------------|-------------|
| Stocks with real fundamentals | 500+ | 2000+ |
| Real-time price latency | < 2 sec | < 500 ms |
| Agent response time (first token) | < 3 sec | < 1.5 sec |
| News articles processed/day | 200+ | 1000+ |
| Knowledge graph nodes | 500+ | 5000+ |
| API uptime | 99.5% | 99.9% |
| Frontend LCP | < 2.5s | < 1.5s |
| Test coverage | > 60% | > 80% |

---

## File Tree Summary (Final State)

```
backend/
├── api/
│   ├── deps.py                          # Auth dependencies
│   └── routes/
│       ├── agent.py                     # SSE chat + conversations
│       ├── auth.py                      # JWT signup/login/refresh
│       ├── alerts.py                    # Price + AI alerts
│       ├── broker.py                    # Broker account management
│       ├── orders.py                    # Order management
│       ├── portfolio.py                 # Portfolio analytics
│       └── ... (existing routes)
├── core/
│   ├── brokers/                         # Broker adapter layer
│   │   ├── base.py
│   │   ├── zerodha.py
│   │   ├── angel_one.py
│   │   ├── upstox.py
│   │   └── groww.py
│   ├── pipelines/                       # Data pipelines
│   │   ├── price_pipeline.py
│   │   ├── fundamentals_pipeline.py
│   │   ├── news_pipeline.py
│   │   └── graph_pipeline.py
│   ├── services/
│   │   ├── agent_orchestrator.py        # GPT-4o streaming agent
│   │   ├── agent_tools.py              # 18+ tools
│   │   ├── agent_memory.py             # User context
│   │   ├── agent_planner.py            # Multi-step plans
│   │   ├── auth.py                     # JWT + bcrypt
│   │   ├── backtest.py                 # Strategy backtesting
│   │   ├── technical_scanner.py        # RSI/MACD scanner
│   │   ├── ml_prediction.py            # XGBoost model
│   │   ├── oms.py                      # Order management
│   │   ├── paper_trading.py            # Simulated trading
│   │   ├── portfolio.py                # Portfolio analytics
│   │   ├── market_cache.py             # Redis price cache
│   │   └── ... (existing services)
│   └── scraper/
│       └── ... (existing + enhanced)
├── db/
│   ├── postgres_models.py              # 25+ models
│   └── ... (existing)
├── middleware/
│   ├── auth_middleware.py              # JWT enforcement
│   ├── request_id.py                  # Request tracing
│   └── metrics.py                     # Prometheus
├── main.py
└── config.py

frontend/src/
├── components/
│   ├── Shell/                          # Terminal shell
│   │   ├── CommandPalette.tsx
│   │   ├── TabManager.tsx
│   │   └── SplitPane.tsx
│   ├── AIChat/
│   │   ├── AIChat.tsx                  # Streaming chat
│   │   ├── ToolCards/                  # Rich tool visualizations
│   │   └── InlineChart.tsx
│   ├── Trading/                        # Trading workspace
│   │   ├── TradingWorkspace.tsx
│   │   ├── OrderEntry.tsx
│   │   ├── PositionsPanel.tsx
│   │   └── StrategyBuilder.tsx
│   ├── Portfolio/                      # Portfolio dashboard
│   │   ├── Portfolio.tsx
│   │   ├── Holdings.tsx
│   │   └── Performance.tsx
│   ├── Developer/                      # API marketplace
│   │   ├── DeveloperDashboard.tsx
│   │   └── ApiKeyManager.tsx
│   └── Auth/
│       └── AuthModal.tsx
├── services/
│   └── api.ts                          # Centralized API client
├── hooks/
│   └── useKeyboard.ts
└── App.tsx                             # Shell + routing
```

---

## Dependencies to Add

### Backend (pip)
```
celery[redis]==5.3.6          # Distributed task queue
prometheus-client==0.20.0     # Metrics
sentry-sdk[fastapi]==1.40.0   # Error tracking
xgboost==2.0.3                # ML prediction
scikit-learn==1.4.0           # Feature engineering
ta==0.11.0                    # Technical analysis library
pyarrow==15.0.0               # Fast data serialization
```

### Frontend (npm)
```
@dnd-kit/core                  # Drag & drop for workspace layout
recharts                        # Portfolio charts
react-grid-layout               # Trading workspace grid
framer-motion                   # Animations
@tanstack/react-query          # Data fetching + caching
```

---

## What Makes This Different from Zerodha/Groww

| Feature | Zerodha | Groww | FinGraph |
|---------|---------|-------|----------|
| AI Chat Agent | None | Basic | Full agentic with 18+ tools |
| Knowledge Graph | None | None | Neo4j company relationships |
| Risk Analytics | None | None | Monte Carlo, VaR, Greeks |
| ML Predictions | None | None | XGBoost + technical scanner |
| Strategy Backtesting | None | None | Full historical backtest |
| API Marketplace | Kite Connect (₹2000/mo) | None | Tiered from ₹0 |
| Multi-broker | No | No | Zerodha + Angel + Upstox + Groww |
| Paper Trading | None | None | AI-coached paper trading |
| Portfolio Health Score | None | Basic | AI-powered with suggestions |
| Natural Language Trading | None | None | "Buy 100 RELIANCE at market" |
| Semantic News Search | None | None | Qdrant vector search |
| Real-time Alerts | Basic | Basic | AI-generated with reasoning |

The **moat** is the AI agent that understands context, can reason across multiple data sources, and take action — not just display data.
