import { PieChart, TrendingUp, Activity, BarChart3, Info } from 'lucide-react'

interface PortfolioCardProps {
  data: Record<string, any>
}

export default function PortfolioCard({ data }: PortfolioCardProps) {
  const { optimal_portfolio, min_variance_portfolio, efficient_frontier } = data
  if (!optimal_portfolio) return null

  const weights = optimal_portfolio.weights_pct || {}
  const maxWeight = Math.max(...(Object.values(weights) as number[]), 1)

  return (
    <div className="bg-terminal-card border border-terminal-border rounded-xl overflow-hidden">
      <div className="flex items-center gap-3 p-3 bg-gradient-to-r from-rose-500/10 to-pink-500/10 border-b border-terminal-border">
        <div className="p-2 bg-rose-500/20 rounded-lg">
          <PieChart size={18} className="text-rose-400" />
        </div>
        <div>
          <h3 className="font-semibold text-sm">Portfolio Optimization</h3>
          <p className="text-xs text-terminal-muted">{data.symbols?.join(', ')}</p>
        </div>
      </div>

      <div className="p-3 border-b border-terminal-border">
        <div className="text-[10px] uppercase tracking-wider text-terminal-muted mb-2">Optimal Portfolio Weights</div>
        <div className="space-y-2">
          {Object.entries(weights).map(([sym, w]) => {
            const pct = w as number
            const barWidth = (pct / maxWeight) * 100
            return (
              <div key={sym} className="flex items-center gap-2">
                <span className="text-xs font-semibold w-20 text-right">{sym}</span>
                <div className="flex-1 h-5 bg-terminal-bg rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-rose-500 to-pink-500 rounded-full transition-all"
                    style={{ width: `${barWidth}%` }}
                  />
                </div>
                <span className="text-xs font-mono w-12 text-right">{pct.toFixed(1)}%</span>
              </div>
            )
          })}
        </div>
      </div>

      <div className="grid grid-cols-3 gap-px bg-terminal-border border-b border-terminal-border">
        {[
          { label: 'Expected Return', value: `${optimal_portfolio.expected_return_pct}%`, icon: TrendingUp, color: 'text-green-400' },
          { label: 'Expected Risk', value: `${optimal_portfolio.expected_risk_pct}%`, icon: Activity, color: 'text-orange-400' },
          { label: 'Sharpe Ratio', value: optimal_portfolio.sharpe_ratio, icon: BarChart3, color: optimal_portfolio.sharpe_ratio > 1 ? 'text-green-400' : optimal_portfolio.sharpe_ratio > 0.5 ? 'text-yellow-400' : 'text-red-400' },
        ].map(m => {
          const Icon = m.icon
          return (
            <div key={m.label} className="bg-terminal-card p-3">
              <div className="flex items-center gap-1.5 text-terminal-muted mb-1">
                <Icon size={12} />
                <span className="text-[10px] uppercase tracking-wider">{m.label}</span>
              </div>
              <span className={`text-sm font-semibold ${m.color}`}>{m.value}</span>
            </div>
          )
        })}
      </div>

      {min_variance_portfolio && (
        <div className="grid grid-cols-2 gap-px bg-terminal-border border-b border-terminal-border">
          {[
            { label: 'Min Variance — Risk', value: `${min_variance_portfolio.risk_pct}%` },
            { label: 'Min Variance — Return', value: `${min_variance_portfolio.return_pct}%` },
          ].map(m => (
            <div key={m.label} className="bg-terminal-card p-3">
              <div className="text-[10px] uppercase tracking-wider text-terminal-muted mb-1">{m.label}</div>
              <span className="text-sm font-semibold text-terminal-muted">{m.value}</span>
            </div>
          ))}
        </div>
      )}

      {efficient_frontier && efficient_frontier.length > 0 && (
        <details className="border-b border-terminal-border">
          <summary className="p-3 text-xs text-terminal-muted hover:text-terminal-foreground cursor-pointer flex items-center gap-1">
            <Activity size={12} />
            Efficient Frontier ({efficient_frontier.length} points)
          </summary>
          <div className="overflow-x-auto border-t border-terminal-border/50 max-h-48 overflow-y-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-terminal-border sticky top-0 bg-terminal-card">
                  <th className="text-left p-2 text-[10px] uppercase text-terminal-muted font-medium">Risk %</th>
                  <th className="text-right p-2 text-[10px] uppercase text-terminal-muted font-medium">Return %</th>
                  <th className="text-right p-2 text-[10px] uppercase text-terminal-muted font-medium">Sharpe</th>
                </tr>
              </thead>
              <tbody>
                {efficient_frontier.slice(0, 30).map((p: any, i: number) => (
                  <tr key={i} className="border-b border-terminal-border/50 hover:bg-terminal-bg/50 transition-colors">
                    <td className="p-2 font-mono text-xs">{p.risk_pct}</td>
                    <td className="p-2 text-right font-mono text-xs">{p.return_pct}</td>
                    <td className="p-2 text-right font-mono text-xs">{p.sharpe?.toFixed(3)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </details>
      )}

      {data.interpretation && (
        <div className="p-3 flex items-start gap-2">
          <Info size={14} className="text-terminal-muted mt-0.5 flex-shrink-0" />
          <p className="text-xs text-terminal-muted leading-relaxed">{data.interpretation}</p>
        </div>
      )}
    </div>
  )
}
