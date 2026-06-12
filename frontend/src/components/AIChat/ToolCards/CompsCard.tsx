import { Users, TrendingUp, TrendingDown, BarChart3 } from 'lucide-react'

interface CompsCardProps {
  data: Record<string, any>
}

export default function CompsCard({ data }: CompsCardProps) {
  const { target_company, peer_median, peer_min, peer_max, percentile_vs_peers, peers } = data
  if (!target_company || !peers) return null

  const metrics = [
    { key: 'pe', label: 'P/E' },
    { key: 'pb', label: 'P/B' },
    { key: 'roe', label: 'ROE', isPct: true },
  ]

  return (
    <div className="bg-terminal-card border border-terminal-border rounded-xl overflow-hidden">
      <div className="flex items-center gap-3 p-3 bg-gradient-to-r from-indigo-500/10 to-purple-500/10 border-b border-terminal-border">
        <div className="p-2 bg-indigo-500/20 rounded-lg">
          <Users size={18} className="text-indigo-400" />
        </div>
        <div>
          <h3 className="font-semibold text-sm">Peer Comparison — {data.target_sector}</h3>
          <p className="text-xs text-terminal-muted">{data.peer_count} peers</p>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-terminal-border">
              <th className="text-left p-2 text-[10px] uppercase text-terminal-muted font-medium">Metric</th>
              <th className="text-right p-2 text-[10px] uppercase text-terminal-accent font-medium">{target_company.symbol}</th>
              <th className="text-right p-2 text-[10px] uppercase text-terminal-muted font-medium">Peer Median</th>
              <th className="text-right p-2 text-[10px] uppercase text-terminal-muted font-medium">Min</th>
              <th className="text-right p-2 text-[10px] uppercase text-terminal-muted font-medium">Max</th>
            </tr>
          </thead>
          <tbody>
            {metrics.map(m => {
              const targetVal = target_company[m.key]
              const medianVal = peer_median?.[m.key]
              const minVal = peer_min?.[m.key]
              const maxVal = peer_max?.[m.key]
              const isTargetBetter = m.key === 'roe' ? targetVal && medianVal && targetVal > medianVal : targetVal && medianVal && targetVal < medianVal
              return (
                <tr key={m.key} className="border-b border-terminal-border/50 hover:bg-terminal-bg/50 transition-colors">
                  <td className="p-2 font-medium">{m.label}</td>
                  <td className="p-2 text-right font-mono text-xs">
                    <span className="inline-flex items-center gap-1 justify-end">
                      {isTargetBetter ? <TrendingUp size={10} className="text-green-400" /> : targetVal ? <TrendingDown size={10} className="text-red-400" /> : null}
                      {targetVal != null ? targetVal.toFixed(2) : '—'}
                      {m.isPct && targetVal != null ? '%' : ''}
                    </span>
                  </td>
                  <td className="p-2 text-right font-mono text-xs">{medianVal != null ? medianVal.toFixed(2) : '—'}{m.isPct && medianVal != null ? '%' : ''}</td>
                  <td className="p-2 text-right font-mono text-xs text-green-400">{minVal != null ? minVal.toFixed(2) : '—'}</td>
                  <td className="p-2 text-right font-mono text-xs text-red-400">{maxVal != null ? maxVal.toFixed(2) : '—'}</td>
                </tr>
              )
            })}
            <tr className="border-b border-terminal-border/50">
              <td className="p-2 font-medium">Mkt Cap (₹Cr)</td>
              <td className="p-2 text-right font-mono text-xs font-semibold">{target_company.market_cap_cr?.toLocaleString()}</td>
              <td className="p-2 text-right font-mono text-xs" colSpan={3}>—</td>
            </tr>
          </tbody>
        </table>
      </div>

      {percentile_vs_peers && (
        <div className="flex gap-2 p-3 bg-terminal-bg border-t border-terminal-border flex-wrap">
          {percentile_vs_peers.pe_cheaper_pct != null && (
            <span className="px-2 py-1 bg-green-500/10 text-green-400 rounded-full text-[10px] font-medium">
              PE cheaper than {percentile_vs_peers.pe_cheaper_pct}% of peers
            </span>
          )}
          {percentile_vs_peers.roe_better_pct != null && (
            <span className="px-2 py-1 bg-indigo-500/10 text-indigo-400 rounded-full text-[10px] font-medium">
              ROE better than {percentile_vs_peers.roe_better_pct}% of peers
            </span>
          )}
        </div>
      )}

      {peers && peers.length > 0 && (
        <details className="border-t border-terminal-border">
          <summary className="p-3 text-xs text-terminal-muted hover:text-terminal-foreground cursor-pointer flex items-center gap-1">
            <BarChart3 size={12} />
            Peer List ({peers.length})
          </summary>
          <div className="overflow-x-auto border-t border-terminal-border/50">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-terminal-border">
                  <th className="text-left p-2 text-[10px] uppercase text-terminal-muted font-medium">Symbol</th>
                  <th className="text-right p-2 text-[10px] uppercase text-terminal-muted font-medium">P/E</th>
                  <th className="text-right p-2 text-[10px] uppercase text-terminal-muted font-medium">P/B</th>
                  <th className="text-right p-2 text-[10px] uppercase text-terminal-muted font-medium">ROE</th>
                  <th className="text-right p-2 text-[10px] uppercase text-terminal-muted font-medium">EPS</th>
                  <th className="text-right p-2 text-[10px] uppercase text-terminal-muted font-medium">D/E</th>
                </tr>
              </thead>
              <tbody>
                {peers.slice(0, 15).map((p: any, i: number) => (
                  <tr key={i} className="border-b border-terminal-border/50 hover:bg-terminal-bg/50 transition-colors">
                    <td className="p-2 font-medium">{p.symbol}</td>
                    <td className="p-2 text-right font-mono text-xs">{p.pe?.toFixed(2) ?? '—'}</td>
                    <td className="p-2 text-right font-mono text-xs">{p.pb?.toFixed(2) ?? '—'}</td>
                    <td className="p-2 text-right font-mono text-xs">{p.roe != null ? `${p.roe.toFixed(1)}%` : '—'}</td>
                    <td className="p-2 text-right font-mono text-xs">{p.eps?.toFixed(2) ?? '—'}</td>
                    <td className="p-2 text-right font-mono text-xs">{p.debt_equity?.toFixed(2) ?? '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </details>
      )}
    </div>
  )
}
