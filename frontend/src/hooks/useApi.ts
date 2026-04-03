/**
 * API hooks — thin wrappers around axios that normalise
 * loading / error / data state for every major endpoint.
 *
 * Uses the same axios instance and base-URL pattern already in use
 * by the existing components (no new dependencies required).
 */
import { useState, useEffect, useCallback, useRef } from 'react';
import axios from 'axios';

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const BASE = (import.meta as any).env?.VITE_API_URL ?? 'http://localhost:8000/api/v1';

const api = axios.create({ baseURL: BASE, timeout: 15_000 });

// ─── Generic state type ───────────────────────────────────────────────────────

export interface ApiState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

function useApiRequest<T>(
  fetcher: () => Promise<T>,
  deps: unknown[],
): ApiState<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const fetch = useCallback(() => {
    abortRef.current?.abort();
    const ctrl = new AbortController();
    abortRef.current = ctrl;

    setLoading(true);
    setError(null);

    fetcher()
      .then((result) => {
        if (!ctrl.signal.aborted) {
          setData(result);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (!ctrl.signal.aborted) {
          setError(err?.response?.data?.error ?? err?.message ?? 'Request failed');
          setLoading(false);
        }
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  useEffect(() => {
    fetch();
    return () => abortRef.current?.abort();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fetch]);

  return { data, loading, error, refetch: fetch };
}

// ─── Quotes ───────────────────────────────────────────────────────────────────

export interface Quote {
  symbol: string;
  name: string;
  price: number;
  open: number;
  high: number;
  low: number;
  close: number;
  change: number;
  pct_change: number;
  volume: number;
  week52_high?: number;
  week52_low?: number;
}

export function useQuote(symbol: string) {
  return useApiRequest<Quote>(
    () =>
      api
        .get(`/quotes/${symbol}`)
        .then((r) => r.data?.data),
    [symbol],
  );
}

export function useMovers(limit = 10) {
  return useApiRequest<{ gainers: Quote[]; losers: Quote[] }>(
    () => api.get(`/quotes/movers?limit=${limit}`).then((r) => r.data?.data),
    [limit],
  );
}

export function useIndices() {
  return useApiRequest<Quote[]>(
    () => api.get('/quotes/indices').then((r) => r.data?.data),
    [],
  );
}

export function useSectors() {
  return useApiRequest<{ sector: string; change: number; volume: number; count: number }[]>(
    () => api.get('/quotes/sectors').then((r) => r.data?.data),
    [],
  );
}

export function useHistorical(symbol: string, period = '1y') {
  return useApiRequest<{ date: string; open: number; high: number; low: number; close: number; volume: number }[]>(
    () =>
      api
        .get(`/quotes/historical/${symbol}?period=${period}`)
        .then((r) => r.data?.data),
    [symbol, period],
  );
}

export function useOptionChain(symbol = 'NIFTY') {
  return useApiRequest<{
    symbol: string;
    underlying: number;
    expiry: string;
    calls: unknown[];
    puts: unknown[];
    pcr: number;
    max_pain: number;
  }>(
    () =>
      api.get(`/quotes/option-chain/${symbol}`).then((r) => r.data?.data),
    [symbol],
  );
}

// ─── Fundamentals ────────────────────────────────────────────────────────────

export interface Fundamentals {
  symbol: string;
  pe: number | null;
  pb: number | null;
  roe: number | null;
  roce: number | null;
  debt_equity: number | null;
  dividend_yield: number | null;
  eps: number | null;
  book_value: number | null;
  market_cap: number | null;
}

export function useFundamentals(symbol: string) {
  return useApiRequest<Fundamentals>(
    () =>
      api
        .get(`/fundamentals/${symbol}`)
        .then((r) => r.data?.data),
    [symbol],
  );
}

export function useQuarterly(symbol: string, limit = 8) {
  return useApiRequest<{ quarter: string; revenue: number; profit: number; eps: number; growth: number }[]>(
    () =>
      api
        .get(`/quarterly/${symbol}?limit=${limit}`)
        .then((r) => r.data?.data),
    [symbol, limit],
  );
}

export function useShareholding(symbol: string) {
  return useApiRequest<{ quarter: string; promoter: number; fii: number; dii: number; public: number }[]>(
    () =>
      api
        .get(`/shareholding/${symbol}`)
        .then((r) => r.data?.data),
    [symbol],
  );
}

// ─── Screener ────────────────────────────────────────────────────────────────

export interface ScreenerFilters {
  market_cap_min?: number;
  market_cap_max?: number;
  pe_min?: number;
  pe_max?: number;
  roe_min?: number;
  sector?: string;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
  limit?: number;
}

export function useScreener(filters: ScreenerFilters) {
  const key = JSON.stringify(filters);
  return useApiRequest<unknown[]>(
    () =>
      api
        .post('/screen/run', filters)
        .then((r) => r.data?.data),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [key],
  );
}

// ─── News ────────────────────────────────────────────────────────────────────

export function useNews(limit = 20, sentiment?: string) {
  const params = new URLSearchParams({ limit: String(limit) });
  if (sentiment) params.set('sentiment', sentiment);

  return useApiRequest<unknown[]>(
    () =>
      api.get(`/news?${params}`).then((r) => r.data?.data),
    [limit, sentiment ?? ''],
  );
}

// ─── Graph ───────────────────────────────────────────────────────────────────

export function useCompanyGraph(symbol: string) {
  return useApiRequest<{ nodes: unknown[]; edges: unknown[] }>(
    () =>
      api.get(`/graph/company/${symbol}`).then((r) => r.data?.data),
    [symbol],
  );
}

// ─── Watchlist ───────────────────────────────────────────────────────────────

export function useWatchlists() {
  return useApiRequest<{ id: number; name: string; symbols: string[] }[]>(
    () => api.get('/watchlist').then((r) => r.data?.data),
    [],
  );
}

// ─── Search ──────────────────────────────────────────────────────────────────

export function useSearch(query: string) {
  return useApiRequest<unknown[]>(
    () => {
      if (!query.trim()) return Promise.resolve([]);
      return api.get(`/search?q=${encodeURIComponent(query)}`).then((r) => r.data?.data ?? []);
    },
    [query],
  );
}

// ─── AI ──────────────────────────────────────────────────────────────────────

export function useAiSummary(symbol: string) {
  return useApiRequest<{ symbol: string; summary: string }>(
    () =>
      api.get(`/ai/summarize/${symbol}`).then((r) => r.data?.data),
    [symbol],
  );
}

// ─── Polling hook ─────────────────────────────────────────────────────────────

/**
 * Poll an endpoint every `intervalMs` milliseconds and return the latest value.
 * Useful for live price updates without WebSocket.
 */
export function usePolling<T>(
  fetcher: () => Promise<T>,
  intervalMs: number,
  deps: unknown[],
): ApiState<T> {
  const state = useApiRequest<T>(fetcher, deps);
  const { refetch } = state;

  useEffect(() => {
    const id = window.setInterval(refetch, intervalMs);
    return () => clearInterval(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [intervalMs, ...deps]);

  return state;
}
