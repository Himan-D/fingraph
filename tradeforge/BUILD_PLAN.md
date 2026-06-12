# TradeForge AI — Build Plan

## Overview
Production-grade SaaS trading platform with AI copilot, strategy builder, backtesting engine, trading bot management, portfolio analytics, and market scanner.

## Tech Stack
- **Frontend**: Next.js 16, React 19, TypeScript, Tailwind CSS v4, shadcn/ui, Recharts, Framer Motion
- **Backend**: Supabase (PostgreSQL, Edge Functions, Auth, Realtime)
- **AI**: Claude API + OpenAI API with RAG architecture
- **Market Data**: Polygon.io, Alpaca, Binance, Yahoo Finance
- **Auth**: Supabase Auth + Google/GitHub OAuth + MFA
- **Payments**: Stripe
- **Deployment**: Vercel + Supabase

## Architecture

### Phase 1: Foundation
- Project config (tailwind, env, tsconfig)
- Supabase client (server + browser + middleware)
- shadcn/ui component registration
- Auth system (login/signup/OAuth/MFA)
- App shell (sidebar, topnav, responsive layout)
- Stripe integration
- Globals CSS with trading theme (dark mode, glassmorphism)

### Phase 2: Core UI Components
- Trading components (chart, ticker, order book, position card)
- Charts (equity curve, drawdown, allocation, correlation)
- Layout components (page header, stat card, data table, empty state)

### Phase 3: Pages (12 total)
1. Landing Page
2. Dashboard
3. AI Copilot
4. Portfolio
5. Strategy Builder
6. Backtesting
7. Trading Bots
8. Market Scanner
9. Alerts
10. Journal
11. Settings
12. Admin

### Phase 4: Backend
- Supabase Edge Functions (market-data, backtest, ai-copilot, strategy-builder, trading-bot, scanner, alerts, stripe-webhook, risk-engine)
- Database schema (all tables)
- AI agent system with tool definitions
- RAG system for strategy/market knowledge
- Trading engine (backtest + live bots)
- Risk management system

### Phase 5: Polish
- Animations and micro-interactions
- Performance optimization
- Testing
- Deployment config

## Database Tables
profiles, broker_connections, strategies, backtest_runs, trades, bots, bot_logs, positions, portfolios, portfolio_holdings, alerts, alert_history, journal_entries, market_data_cache, subscriptions, api_keys, conversations, messages

## AI Tools
get_market_data, analyze_technical, analyze_fundamental, generate_strategy, run_backtest, optimize_portfolio, get_news_sentiment, explain_market, suggest_trades

## Folder Structure
```
src/
├── app/           → pages (auth, dashboard/*, pricing, landing)
├── components/    → ui/, auth/, layout/, charts/, trading/, copilot/, strategies/, bots/, portfolio/
├── hooks/         → queries/, useAuth, useRealtime*
├── lib/           → supabase/, ai/, stripe/, trading/,
├── stores/        → state management
└── types/         → TypeScript definitions
supabase/
└── functions/     → Edge Functions
```
