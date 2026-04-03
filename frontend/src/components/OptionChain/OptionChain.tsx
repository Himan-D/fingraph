import { useState, useEffect, useMemo } from 'react';
import axios from 'axios';

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const BASE = (import.meta as any).env?.VITE_API_URL ?? 'http://localhost:8000/api/v1';

// ─── Types ────────────────────────────────────────────────────────────────────

interface Strike {
  strike: number;
  bid: number;
  ask: number;
  last: number;
  volume: number;
  oi: number;
  oi_change: number;
  iv?: number;
}

interface OptionChainData {
  symbol: string;
  underlying: number;
  expiry: string;
  calls: Strike[];
  puts: Strike[];
  pcr: number;
  max_pain: number;
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

function fmt(n: number | null | undefined, dec = 2): string {
  if (n == null || isNaN(n)) return '—';
  return n.toLocaleString('en-IN', { maximumFractionDigits: dec });
}

function fmtOI(n: number): string {
  if (n >= 10_000_000) return `${(n / 10_000_000).toFixed(2)}Cr`;
  if (n >= 100_000) return `${(n / 100_000).toFixed(2)}L`;
  return n.toLocaleString('en-IN');
}

/** Compute max pain strike (strike with max extrinsic value destruction). */
function calcMaxPain(calls: Strike[], puts: Strike[], underlying: number): number {
  const strikes = [...new Set([...calls, ...puts].map((s) => s.strike))].sort(
    (a, b) => a - b,
  );
  let best = underlying;
  let bestLoss = Infinity;

  for (const testStrike of strikes) {
    const callLoss = calls.reduce(
      (sum, c) => sum + Math.max(testStrike - c.strike, 0) * c.oi,
      0,
    );
    const putLoss = puts.reduce(
      (sum, p) => sum + Math.max(p.strike - testStrike, 0) * p.oi,
      0,
    );
    const total = callLoss + putLoss;
    if (total < bestLoss) {
      bestLoss = total;
      best = testStrike;
    }
  }
  return best;
}

// ─── OI Bar ──────────────────────────────────────────────────────────────────

function OIBar({
  value,
  max,
  isCall,
}: {
  value: number;
  max: number;
  isCall: boolean;
}) {
  const pct = max > 0 ? Math.min((value / max) * 100, 100) : 0;
  return (
    <div className="relative h-4 w-24 bg-terminal-border rounded overflow-hidden">
      <div
        className={`absolute top-0 h-full rounded ${isCall ? 'bg-terminal-success/40 right-0' : 'bg-terminal-danger/40 left-0'}`}
        style={{ width: `${pct}%` }}
      />
    </div>
  );
}

// ─── Component ───────────────────────────────────────────────────────────────

const INDICES = ['NIFTY', 'BANKNIFTY', 'FINNIFTY'];

export default function OptionChain() {
  const [selectedIndex, setSelectedIndex] = useState('NIFTY');
  const [data, setData] = useState<OptionChainData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [highlightATM, setHighlightATM] = useState(true);
  const [strikesVisible, setStrikesVisible] = useState(20);

  useEffect(() => {
    setLoading(true);
    setError(null);
    axios
      .get(`${BASE}/quotes/option-chain/${selectedIndex}`)
      .then((r) => {
        const payload = r.data?.data;
        if (payload) {
          // Enrich with max-pain calc if not provided by server
          const mp =
            payload.max_pain ??
            calcMaxPain(payload.calls, payload.puts, payload.underlying);
          setData({ ...payload, max_pain: mp });
        }
        setLoading(false);
      })
      .catch((e) => {
        setError(e?.response?.data?.error ?? e.message);
        setLoading(false);
      });
  }, [selectedIndex]);

  // Merge calls and puts by strike into a merged row list
  const mergedRows = useMemo(() => {
    if (!data) return [];
    const underlying = data.underlying;

    const callMap = new Map(data.calls.map((c) => [c.strike, c]));
    const putMap = new Map(data.puts.map((p) => [p.strike, p]));
    const strikes = [...new Set([...callMap.keys(), ...putMap.keys()])].sort(
      (a, b) => a - b,
    );

    return strikes.map((strike) => ({
      strike,
      call: callMap.get(strike) ?? null,
      put: putMap.get(strike) ?? null,
      isATM: Math.abs(strike - underlying) < 75, // within ~75 pts
    }));
  }, [data]);

  const maxCallOI = useMemo(
    () => Math.max(...(data?.calls.map((c) => c.oi) ?? [1])),
    [data],
  );
  const maxPutOI = useMemo(
    () => Math.max(...(data?.puts.map((p) => p.oi) ?? [1])),
    [data],
  );

  const visibleRows = mergedRows.slice(
    Math.max(0, mergedRows.findIndex((r) => r.isATM) - Math.floor(strikesVisible / 2)),
    Math.max(0, mergedRows.findIndex((r) => r.isATM) - Math.floor(strikesVisible / 2)) + strikesVisible,
  );

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center text-terminal-muted">
        <span className="animate-pulse">Loading option chain…</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="h-full flex flex-col items-center justify-center text-terminal-danger gap-2">
        <span>Failed to load option chain</span>
        <span className="text-xs text-terminal-muted">{error}</span>
      </div>
    );
  }

  if (!data) return null;

  const totalCallOI = data.calls.reduce((s, c) => s + c.oi, 0);
  const totalPutOI = data.puts.reduce((s, p) => s + p.oi, 0);
  const pcr = totalPutOI > 0 ? totalPutOI / totalCallOI : 0;

  return (
    <div className="h-full flex flex-col bg-terminal-bg text-terminal-text text-xs">
      {/* Header bar */}
      <div className="px-4 py-3 border-b border-terminal-border flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-3">
          <span className="text-terminal-accent font-semibold text-sm">Option Chain</span>
          {/* Index selector */}
          <div className="flex gap-1">
            {INDICES.map((idx) => (
              <button
                key={idx}
                onClick={() => setSelectedIndex(idx)}
                className={`px-3 py-1 rounded text-xs font-mono transition-colors ${
                  selectedIndex === idx
                    ? 'bg-terminal-accent text-terminal-bg'
                    : 'bg-terminal-card text-terminal-muted hover:text-terminal-text border border-terminal-border'
                }`}
              >
                {idx}
              </button>
            ))}
          </div>
        </div>

        {/* Live stats */}
        <div className="flex items-center gap-6 font-mono">
          <span>
            <span className="text-terminal-muted mr-1">Underlying</span>
            <span className="text-terminal-accent font-semibold">{fmt(data.underlying)}</span>
          </span>
          <span>
            <span className="text-terminal-muted mr-1">Expiry</span>
            <span>{data.expiry}</span>
          </span>
          <span>
            <span className="text-terminal-muted mr-1">PCR</span>
            <span
              className={
                pcr > 1.2
                  ? 'text-terminal-success'
                  : pcr < 0.8
                    ? 'text-terminal-danger'
                    : 'text-terminal-warning'
              }
            >
              {pcr.toFixed(2)}
            </span>
          </span>
          <span>
            <span className="text-terminal-muted mr-1">Max Pain</span>
            <span className="text-terminal-warning">{fmt(data.max_pain, 0)}</span>
          </span>
          <span>
            <span className="text-terminal-muted mr-1">Call OI</span>
            <span className="text-terminal-success">{fmtOI(totalCallOI)}</span>
          </span>
          <span>
            <span className="text-terminal-muted mr-1">Put OI</span>
            <span className="text-terminal-danger">{fmtOI(totalPutOI)}</span>
          </span>
        </div>

        <label className="flex items-center gap-1 text-terminal-muted cursor-pointer select-none">
          <input
            type="checkbox"
            checked={highlightATM}
            onChange={(e) => setHighlightATM(e.target.checked)}
            className="accent-terminal-accent"
          />
          Highlight ATM
        </label>
      </div>

      {/* OI Summary bar */}
      <div className="px-4 py-2 border-b border-terminal-border flex items-center gap-2">
        <span className="text-terminal-success text-xs">CALL OI</span>
        <div className="flex-1 h-2 bg-terminal-border rounded overflow-hidden">
          <div
            className="h-full bg-terminal-success/60 rounded"
            style={{ width: `${(totalCallOI / (totalCallOI + totalPutOI)) * 100}%` }}
          />
        </div>
        <span className="text-terminal-danger text-xs">PUT OI</span>
        <div className="flex-1 h-2 bg-terminal-border rounded overflow-hidden flex justify-end">
          <div
            className="h-full bg-terminal-danger/60 rounded"
            style={{ width: `${(totalPutOI / (totalCallOI + totalPutOI)) * 100}%` }}
          />
        </div>
      </div>

      {/* Column headers */}
      <div className="grid grid-cols-[1fr_80px_80px_80px_80px_96px_24px_80px_96px_80px_80px_80px_1fr] gap-0 px-4 py-1.5 border-b border-terminal-border text-terminal-muted font-medium bg-terminal-card/50 sticky top-0 z-10">
        <div className="text-right text-terminal-success">OI</div>
        <div className="text-right text-terminal-success">Chng OI</div>
        <div className="text-right text-terminal-success">Vol</div>
        <div className="text-right text-terminal-success">IV</div>
        <div className="text-right text-terminal-success">LTP</div>
        <div className="text-right text-terminal-success">Bid</div>
        <div />
        <div className="text-left text-terminal-danger">Ask</div>
        <div className="text-center font-bold text-terminal-text">Strike</div>
        <div className="text-right text-terminal-danger">LTP</div>
        <div className="text-right text-terminal-danger">IV</div>
        <div className="text-right text-terminal-danger">Vol</div>
        <div className="text-left text-terminal-danger">OI</div>
      </div>

      {/* Rows */}
      <div className="flex-1 overflow-y-auto">
        {visibleRows.map(({ strike, call, put, isATM }) => {
          const rowBg = isATM && highlightATM
            ? 'bg-terminal-accent/10 border-y border-terminal-accent/30'
            : 'hover:bg-terminal-card/60';

          return (
            <div
              key={strike}
              className={`grid grid-cols-[1fr_80px_80px_80px_80px_96px_24px_80px_96px_80px_80px_80px_1fr] gap-0 px-4 py-1 font-mono text-xs transition-colors ${rowBg}`}
            >
              {/* CALL side (left) */}
              <div className="flex items-center justify-end gap-1">
                {call && (
                  <OIBar value={call.oi} max={maxCallOI} isCall={true} />
                )}
                <span className="text-terminal-text">{call ? fmtOI(call.oi) : '—'}</span>
              </div>
              <div className={`text-right ${call?.oi_change && call.oi_change > 0 ? 'text-terminal-success' : 'text-terminal-danger'}`}>
                {call ? fmtOI(Math.abs(call.oi_change)) : '—'}
              </div>
              <div className="text-right text-terminal-muted">{call ? fmtOI(call.volume) : '—'}</div>
              <div className="text-right text-terminal-warning">{call?.iv ? `${call.iv.toFixed(1)}%` : '—'}</div>
              <div className="text-right text-terminal-success font-medium">{call ? fmt(call.last) : '—'}</div>
              <div className="text-right text-terminal-muted">{call ? fmt(call.bid) : '—'}</div>

              {/* Center divider */}
              <div className="flex items-center justify-center text-terminal-border">│</div>

              {/* PUT side (right) */}
              <div className="text-left text-terminal-muted">{put ? fmt(put.ask) : '—'}</div>
              <div
                className={`text-center font-bold ${
                  isATM ? 'text-terminal-accent' : 'text-terminal-text'
                }`}
              >
                {strike.toLocaleString('en-IN')}
                {isATM && (
                  <span className="ml-1 text-terminal-accent text-xs">ATM</span>
                )}
                {strike === data.max_pain && (
                  <span className="ml-1 text-terminal-warning text-xs">MP</span>
                )}
              </div>
              <div className="text-right text-terminal-danger font-medium">{put ? fmt(put.last) : '—'}</div>
              <div className="text-right text-terminal-warning">{put?.iv ? `${put.iv.toFixed(1)}%` : '—'}</div>
              <div className="text-right text-terminal-muted">{put ? fmtOI(put.volume) : '—'}</div>
              <div className="flex items-center gap-1">
                <span className="text-terminal-text">{put ? fmtOI(put.oi) : '—'}</span>
                {put && <OIBar value={put.oi} max={maxPutOI} isCall={false} />}
              </div>
            </div>
          );
        })}
      </div>

      {/* Footer — load more */}
      <div className="px-4 py-2 border-t border-terminal-border flex items-center justify-between text-terminal-muted">
        <span>
          Showing {visibleRows.length} of {mergedRows.length} strikes
        </span>
        <div className="flex gap-2">
          {strikesVisible < mergedRows.length && (
            <button
              className="text-terminal-accent hover:underline"
              onClick={() => setStrikesVisible((v) => v + 20)}
            >
              Show more
            </button>
          )}
          {strikesVisible > 20 && (
            <button
              className="text-terminal-muted hover:underline"
              onClick={() => setStrikesVisible(20)}
            >
              Collapse
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
