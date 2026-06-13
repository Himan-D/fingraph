"use client"

import { useQuery } from "@tanstack/react-query"
import { api } from "@/lib/api"

// --- Quotes ---

export type Quote = {
  symbol: string
  name: string
  price: number
  change: number
  pct_change: number
  open: number
  high: number
  low: number
  volume: number
  market_cap: number | null
  sector: string | null
  industry: string | null
  pe_ratio: number | null
  week52_high: number | null
  week52_low: number | null
}

export type IndexQuote = {
  symbol: string
  name: string
  price: number
  change: number
  pct_change: number
}

export type MoverData = {
  gainers: Quote[]
  losers: Quote[]
}

export type SectorData = {
  sector: string
  change: number
  volume: number
  count: number
}

export type HistoricalPoint = {
  timestamp: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

export type OptionChainData = {
  symbol: string
  underlying: number
  calls: OptionData[]
  puts: OptionData[]
  expiry: string
  timestamp: string
}

export type OptionData = {
  strike: number
  bid: number
  ask: number
  last: number
  volume: number
  oi: number
  oi_change: number
}

export function useQuote(symbol: string) {
  return useQuery({
    queryKey: ["quote", symbol],
    queryFn: () => api.get<{ success: boolean; data: Quote }>(`/api/v1/quotes/${symbol}`).then((r) => r.data),
    enabled: !!symbol,
  })
}

export function useBatchQuotes(symbols: string) {
  return useQuery({
    queryKey: ["batchQuotes", symbols],
    queryFn: () =>
      api
        .get<{ success: boolean; data: Quote[] }>(`/api/v1/quotes/batch?symbols=${symbols}`)
        .then((r) => r.data),
    enabled: !!symbols,
  })
}

export function useIndices() {
  return useQuery({
    queryKey: ["indices"],
    queryFn: () =>
      api.get<{ success: boolean; data: IndexQuote[] }>("/api/v1/quotes/indices").then((r) => r.data),
    refetchInterval: 60_000,
  })
}

export function useMovers(segment = "equity", limit = 10) {
  return useQuery({
    queryKey: ["movers", segment, limit],
    queryFn: () =>
      api
        .get<{ success: boolean; data: MoverData }>(`/api/v1/quotes/movers?segment=${segment}&limit=${limit}`)
        .then((r) => r.data),
    refetchInterval: 60_000,
  })
}

export function useSectors() {
  return useQuery({
    queryKey: ["sectors"],
    queryFn: () =>
      api.get<{ success: boolean; data: SectorData[] }>("/api/v1/quotes/sectors").then((r) => r.data),
    refetchInterval: 120_000,
  })
}

export function useSearchStocks(query: string) {
  return useQuery({
    queryKey: ["searchStocks", query],
    queryFn: () =>
      api
        .get<{ success: boolean; data: { symbol: string; name: string; sector: string; industry: string; type: string }[] }>(
          `/api/v1/quotes/search?q=${encodeURIComponent(query)}`,
        )
        .then((r) => r.data),
    enabled: query.length >= 1,
  })
}

export function useHistorical(symbol: string, period = "1y") {
  return useQuery({
    queryKey: ["historical", symbol, period],
    queryFn: () =>
      api
        .get<{ success: boolean; data: HistoricalPoint[] }>(`/api/v1/quotes/historical/${symbol}?period=${period}`)
        .then((r) => r.data),
    enabled: !!symbol,
  })
}

export function useOptionChain(symbol: string) {
  return useQuery({
    queryKey: ["optionChain", symbol],
    queryFn: () =>
      api
        .get<{ success: boolean; data: OptionChainData }>(`/api/v1/quotes/option-chain/${symbol}`)
        .then((r) => r.data),
    enabled: !!symbol,
  })
}

// --- Fundamentals ---

export type Fundamentals = {
  symbol: string
  pe: number | null
  pb: number | null
  roe: number | null
  roce: number | null
  debt_equity: number | null
  dividend_yield: number | null
  eps: number | null
  revenue: number | null
  profit: number | null
  book_value: number | null
  market_cap: number | null
}

export type QuarterlyData = {
  quarter: string
  revenue: number | null
  profit: number | null
  eps: number | null
  growth: number | null
}

export function useFundamentals(symbol: string) {
  return useQuery({
    queryKey: ["fundamentals", symbol],
    queryFn: () =>
      api
        .get<{ success: boolean; data: Fundamentals }>(`/api/v1/fundamentals/${symbol}`)
        .then((r) => r.data),
    enabled: !!symbol,
  })
}

export function useQuarterly(symbol: string) {
  return useQuery({
    queryKey: ["quarterly", symbol],
    queryFn: () =>
      api
        .get<{ success: boolean; data: QuarterlyData[] }>(`/api/v1/quarterly/${symbol}`)
        .then((r) => r.data),
    enabled: !!symbol,
  })
}

// --- Screener ---

export type ScreenerResult = {
  symbol: string
  name: string
  sector: string
  industry: string
  price: number
  change: number
  pct_change: number
  volume: number
  market_cap: number | null
  pe_ratio: number | null
  roe: number | null
  debt_equity: number | null
  dividend_yield: number | null
  week52_high: number | null
  week52_low: number | null
}

export type ScreenerFilters = {
  market_cap_min?: number
  market_cap_max?: number
  pe_min?: number
  pe_max?: number
  pb_min?: number
  pb_max?: number
  roe_min?: number
  roce_min?: number
  net_margin_min?: number
  revenue_growth_min?: number
  profit_growth_min?: number
  dividend_yield_min?: number
  debt_equity_max?: number
  sector?: string
  sort_by?: string
  sort_order?: string
  limit?: number
}

export function useScreener(filters: ScreenerFilters, enabled = false) {
  const params = new URLSearchParams()
  Object.entries(filters).forEach(([k, v]) => {
    if (v !== undefined && v !== "") params.set(k, String(v))
  })
  return useQuery({
    queryKey: ["screener", filters],
    queryFn: () =>
      api
        .get<{ success: boolean; data: ScreenerResult[]; count: number }>(`/api/v1/screen/run?${params}`)
        .then((r) => r.data),
    enabled,
  })
}

export function useScreenerTemplates() {
  return useQuery({
    queryKey: ["screenerTemplates"],
    queryFn: () =>
      api
        .get<{ success: boolean; data: { id: string; name: string; description: string; filters: ScreenerFilters }[] }>(
          "/api/v1/screen/templates",
        )
        .then((r) => r.data),
  })
}

export function useScreenerSectors() {
  return useQuery({
    queryKey: ["screenerSectors"],
    queryFn: () => api.get<{ success: boolean; data: string[] }>("/api/v1/screen/sectors").then((r) => r.data),
  })
}

// --- News ---

export type NewsArticle = {
  id: number
  headline: string
  summary: string
  source: string
  url: string
  category: string
  sentiment: string | null
  published_at: string
}

export function useNews(limit = 10) {
  return useQuery({
    queryKey: ["news", limit],
    queryFn: () =>
      api.get<{ success: boolean; data: NewsArticle[] }>(`/api/v1/news/?limit=${limit}`).then((r) => r.data),
    refetchInterval: 300_000,
  })
}

// --- AI Alerts ---

export type AIAlert = {
  id: number
  symbol: string
  alert_type: string
  severity: string
  title: string
  summary: string
  data: Record<string, unknown>
  is_read: boolean
  created_at: string
}

export function useAIAlerts(limit = 20) {
  return useQuery({
    queryKey: ["aiAlerts", limit],
    queryFn: () =>
      api.get<{ success: boolean; data: AIAlert[] }>(`/api/v1/ai/alerts?limit=${limit}`).then((r) => r.data),
    refetchInterval: 60_000,
  })
}

// --- Risk ---

export type RiskAnalysis = {
  var: { daily: number; weekly: number; monthly: number }
  monte_carlo: { mean_return: number; worst_case: number; best_case: number; scenarios: number }
  stress_test: { scenarios: { name: string; impact: number }[] }
}

export function useRisk(symbol: string) {
  return useQuery({
    queryKey: ["risk", symbol],
    queryFn: () =>
      api.get<{ success: boolean; data: RiskAnalysis }>(`/api/v1/risk/commodity/${symbol}`).then((r) => r.data),
    enabled: !!symbol,
  })
}

// --- Signals ---

export type TradingSignal = {
  symbol: string
  signal: string
  strength: number
  indicators: Record<string, string>
  timestamp: string
}

export function useSignals(commodity?: string) {
  return useQuery({
    queryKey: ["signals", commodity],
    queryFn: () => {
      const path = commodity
        ? `/api/v1/signals/signals/${commodity}`
        : "/api/v1/signals/signals"
      return api.get<{ success: boolean; data: TradingSignal[] }>(path).then((r) => r.data)
    },
  })
}

// --- Analytics / Predictions ---

export type Prediction = {
  symbol: string
  prediction: string
  confidence: number
  price_target: number
  timeframe: string
  factors: string[]
}

export function usePrediction(symbol: string) {
  return useQuery({
    queryKey: ["prediction", symbol],
    queryFn: () =>
      api
        .get<{ success: boolean; data: Prediction }>(`/api/v1/analytics/predict/${symbol}`)
        .then((r) => r.data),
    enabled: !!symbol,
  })
}

// --- Search ---

export type SearchResult = {
  stocks: { symbol: string; name: string; sector: string; industry: string; price: number; type: string; score: number; id: number }[]
  sectors: { name: string; icon: string; description: string; type: string; score: number }[]
  news: { id: number; headline: string; source: string; url: string; timestamp: string; type: string; score: number }[]
}

export function useSearch(query: string) {
  return useQuery({
    queryKey: ["search", query],
    queryFn: () =>
      api
        .get<{ success: boolean; data: SearchResult }>(`/api/v1/search/search?q=${encodeURIComponent(query)}`)
        .then((r) => r.data),
    enabled: query.length >= 2,
  })
}

export function useTrending() {
  return useQuery({
    queryKey: ["trending"],
    queryFn: () =>
      api
        .get<{ success: boolean; data: { symbol: string; name: string; price: number; change: number; volume: number }[] }>(
          "/api/v1/search/trending",
        )
        .then((r) => r.data),
    refetchInterval: 60_000,
  })
}

export function useSuggestions(query: string) {
  return useQuery({
    queryKey: ["suggest", query],
    queryFn: () =>
      api
        .get<{ success: boolean; data: { symbol: string; name: string; sector: string }[] }>(
          `/api/v1/search/suggest?q=${encodeURIComponent(query)}`,
        )
        .then((r) => r.data),
    enabled: query.length >= 1,
  })
}

// --- Agent Conversations ---

export type Conversation = {
  id: number
  title: string
  symbol: string | null
  created_at: string
  updated_at: string
}

export type Message = {
  id: number
  role: string
  content: string
  tool_calls: unknown
  tool_results: unknown
  created_at: string
}

export function useConversations(limit = 20) {
  return useQuery({
    queryKey: ["conversations", limit],
    queryFn: () =>
      api
        .get<{ success: boolean; data: Conversation[] }>(`/api/v1/agent/conversations?limit=${limit}`)
        .then((r) => r.data),
  })
}

export function useConversationMessages(conversationId: number) {
  return useQuery({
    queryKey: ["conversation", conversationId],
    queryFn: () =>
      api
        .get<{ success: boolean; data: { id: number; title: string; symbol: string | null; messages: Message[] } }>(
          `/api/v1/agent/conversations/${conversationId}`,
        )
        .then((r) => r.data),
    enabled: conversationId > 0,
  })
}
