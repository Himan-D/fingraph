# FinGraph Terminal - Specification

## Project Overview

**Project Name:** FinGraph  
**Type:** Desktop Terminal Application with Knowledge Graph  
**Target:** Indian Stock Market (NSE/BSE)  
**Repository:** `/Users/himand/fingraph/`

---

## 1. Technology Stack

| Layer | Technology |
|-------|------------|
| Backend | Python FastAPI |
| Frontend | React + Electron |
| Primary DB | PostgreSQL (via Docker) |
| Graph DB | Neo4j Aura (Free Tier) |
| Vector DB | Qdrant (via Docker) |
| Crawling | Crawl4AI |
| AI | OpenAI GPT-4 |
| Real-time Data | TrueData WebSocket |
| Charts | TradingView Lightweight Charts |
| Task Queue | Celery + Redis |

---

## 2. Data Sources

### 2.1 Market Data

| Source | Data Type | Method |
|--------|-----------|--------|
| **TrueData** | Real-time NSE/BSE quotes | WebSocket API |
| **NSE India** | Option chain, indices, deals | Official API |
| **BSE India** | Corporate filings | Official API |

### 2.2 Fundamental Data

| Source | Data Points | Method |
|--------|-------------|--------|
| **Screener.in** | P/E, P/B, ROE, Debt, revenue, quarterly results | Crawl4AI |
| **MoneyControl** | News, results | Crawl4AI |
| **ET Markets** | News | Crawl4AI |
| **AMFI** | MF Holdings | Official API |

---

## 3. Database Schema

### 3.1 PostgreSQL Tables

```sql
-- companies
companies(id, symbol, nse_code, bse_code, name, isin, sector, industry, market_cap, listing_date, face_value)

-- stock_quotes
stock_quotes(id, company_id, timestamp, open, high, low, close, volume, delivery, vwap, turnover)

-- fundamentals
fundamentals(id, company_id, quarter, fiscal_year, revenue, profit, eps, pe, pb, roe, roce, debt_equity, current_ratio, gross_margin, net_margin)

-- shareholding
shareholding(id, company_id, date, promoter, fii, dii, public, total_shares)

-- corporate_actions
corporate_actions(id, company_id, action_type, record_date, ex_date, ratio, price)

-- deals
deals(id, company_id, deal_date, deal_type, buyer_name, seller_name, quantity, price)

-- mf_holdings
mf_holdings(id, company_id, mf_name, quarter, year, quantity, change_qq)

-- news_articles
news_articles(id, headline, summary, source, url, published_at, sentiment, related_symbols)

-- watchlists
watchlists(id, user_id, name, symbols)
```

### 3.2 Neo4j Graph Schema

**Node Types:**
- `Company` - NSE/BSE listed stocks
- `Promoter` - Promoter groups/individuals
- `KMP` - Key Managerial Personnel
- `Investor` - FII, DII, Mutual Funds
- `Index` - Nifty, BankNifty, etc.
- `Sector` - NSE sectors
- `CorporateAction` - Dividends, bonuses
- `Deal` - Bulk/Block deals

**Key Relationships:**
- `(Promoter)-[:PROMOTER_OF]->(Company)`
- `(Company)-[:SUBSIDIARY_OF]->(Company)`
- `(KMP)-[:CEO_OF|CFO_OF|CHAIRMAN_OF|BOARD_MEMBER_OF]->(Company)`
- `(Investor)-[:HOLDS_STOCK_IN]->(Company)`
- `(Company)-[:PART_OF_INDEX]->(Index)`
- `(Company)-[:BELONGS_TO_SECTOR]->(Sector)`
- `(Company)-[:SUPPLIES_TO|COMPETES_WITH]->(Company)`
- `(Deal)-[:BOUGHT_IN_BULK_DEAL|SOLD_IN_BULK_DEAL]->(Company)`

---

## 4. API Endpoints

### Market Data
- `GET /api/v1/quotes/{symbol}` - Live quote
- `GET /api/v1/quotes/batch` - Batch quotes
- `GET /api/v1/historical/{symbol}` - Historical data
- `GET /api/v1/option-chain/{symbol}` - Option chain
- `GET /api/v1/movers` - Top gainers/losers
- `GET /api/v1/indices` - Index values

### Fundamentals
- `GET /api/v1/company/{symbol}` - Company profile
- `GET /api/v1/fundamentals/{symbol}` - Financial ratios
- `GET /api/v1/quarterly/{symbol}` - Quarterly results
- `GET /api/v1/shareholding/{symbol}` - Shareholding pattern
- `GET /api/v1/deals/{symbol}` - Bulk/block deals

### Knowledge Graph
- `GET /api/v1/graph/company/{symbol}` - Company relationships
- `GET /api/v1/graph/promoter/{name}` - Promoter network
- `GET /api/v1/graph/competitors/{symbol}` - Peer companies

### AI Features
- `POST /api/v1/ai/query` - Natural language query
- `GET /api/v1/ai/summarize/{symbol}` - Financial summary

---

## 5. Frontend Components

### Dashboard Layout
```
┌─────────────────────────────────────────────┐
│ HEADER: Logo | Search | Watchlist | Alerts │
├─────────────────────────────────────────────┤
│ QUOTE BOARD (scrolling ticker)              │
├─────────────┬───────────────────────────────┤
│ SIDEBAR     │ MAIN CONTENT                  │
│ - Watchlist │ - Quotes / Screener / Graph   │
│ - Recent    │ - Charts                      │
│ - Sectors   │ - AI Chat                    │
├─────────────┴───────────────────────────────┤
│ FOOTER: Market Status | Last Updated        │
└─────────────────────────────────────────────┘
```

### Key Pages
1. **Dashboard** - Market overview, movers, heatmap
2. **Quotes** - Live stock quotes with search
3. **Charts** - TradingView price charts
4. **Screener** - Filter stocks by fundamentals
5. **Graph** - Knowledge graph visualization
6. **Option Chain** - F&O chain with Greeks
7. **AI Chat** - Natural language queries

---

## 6. Environment Variables

```env
# Backend
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/fingraph
NEO4J_URI=neo4j+s://xxx.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=xxx
QDRANT_URL=http://localhost:6333

# Data Sources
TRUEDATA_URL=wss://marketdata.truedata.in
TRUEDATA_USERNAME=xxx
TRUEDATA_PASSWORD=xxx
OPENAI_API_KEY=sk-xxx

# Crawling
CRAWL4AI_URL=http://localhost:11202
```

---

## 7. Development Phases

### Phase 1: Foundation
- [x] Project structure created
- [ ] Docker setup (PostgreSQL, Qdrant, Redis)
- [ ] FastAPI backend setup
- [ ] React + Electron frontend

### Phase 2: Data Pipeline
- [ ] TrueData integration
- [ ] Quote storage
- [ ] NSE API integration

### Phase 3: Scraping & Fundamentals
- [ ] Screener.in scraper
- [ ] Fundamentals storage
- [ ] Shareholding pattern

### Phase 4: Knowledge Graph
- [ ] Neo4j setup
- [ ] Entity extraction
- [ ] Relationship mapping
- [ ] Graph visualization

### Phase 5: AI Features
- [ ] GPT-4 integration
- [ ] Natural language queries
- [ ] Summarization

---

## 8. Running the Project

```bash
# Start databases
docker-compose -f docker/docker-compose.yml up -d

# Backend
cd backend
uvicorn main:app --reload

# Frontend
cd frontend
npm run dev
```

---

## 9. Competitive Edge

| Feature | Description |
|---------|-------------|
| **Promoter Network Graph** | Visualize promoter holdings across companies |
| **KMP Cross-Company** | Directors on multiple boards |
| **AI Summarizer** | Auto-summarize quarterly results |
| **Supply Chain Graph** | Supplier-customer relationships |
| **Natural Screener** | Text-based filtering |
| **Real-time Alerts** | Custom alert conditions |

---

## 10. Pricing

| Tier | Price | Features |
|------|-------|----------|
| Free | ₹0 | Delayed quotes, basic graph |
| Pro | ₹199/mo | Real-time, AI queries, unlimited graph |
| Pro+ | ₹499/mo | API access, advanced features |
