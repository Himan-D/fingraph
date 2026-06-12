import { Activity, TrendingUp, Scale, Gauge, BarChart3, Info } from 'lucide-react'

interface RatiosCardProps {
  data: Record<string, any>
}

export default function RatiosCard({ data }: RatiosCardProps) {
  const { ratios, health_score, interpretation } = data
  if (!ratios) return null

  const categories = [
    { key: 'profitability', label: 'Profitability', icon: TrendingUp, color: 'text-green-400 bg-green-500/10' },
    { key: 'liquidity', label: 'Liquidity', icon: Activity, color: 'text-blue-400 bg-blue-500/10' },
    { key: 'leverage', label: 'Leverage', icon: Scale, color: 'text-orange-400 bg-orange-500/10' },
    { key: 'efficiency', label: 'Efficiency', icon: Gauge, color: 'text-purple-400 bg-purple-500/10' },
    { key: 'valuation', label: 'Valuation', icon: BarChart3, color: 'text-cyan-400 bg-cyan-500/10' },
  ]

  const ratioLabels: Record<string, Record<string, string>> = {
    profitability: {
      net_margin_pct: 'Net Margin', gross_margin_pct: 'Gross Margin', roe_pct: 'ROE',
      roce_pct: 'ROCE', return_on_assets_pct: 'ROA', eps: 'EPS',
    },
    liquidity: { current_ratio: 'Current Ratio', quick_ratio_estimate: 'Quick Ratio' },
    leverage: { debt_to_equity: 'D/E', debt_ratio_estimate: 'Debt Ratio', interest_coverage_estimate: 'Int. Coverage' },
    efficiency: { asset_turnover_estimate: 'Asset Turnover', revenue_per_employee_estimate: 'Rev/Employee' },
    valuation: { pe_ratio: 'P/E', pb_ratio: 'P/B', dividend_yield_pct: 'Div. Yield', price_to_sales_ratio: 'P/S', peg_ratio_estimate: 'PEG' },
  }

  const healthColor =
    health_score?.rating === 'Strong Buy' ? 'text-green-400' :
    health_score?.rating === 'Buy' ? 'text-cyan-400' :
    health_score?.rating === 'Hold' ? 'text-yellow-400' :
    'text-red-400'

  return (
    <div className="bg-terminal-card border border-terminal-border rounded-xl overflow-hidden">
      <div className="flex items-center gap-3 p-3 bg-gradient-to-r from-teal-500/10 to-emerald-500/10 border-b border-terminal-border">
        <div className="p-2 bg-teal-500/20 rounded-lg">
          <Activity size={18} className="text-teal-400" />
        </div>
        <div>
          <h3 className="font-semibold text-sm">Financial Ratio Analysis — {data.symbol}</h3>
          <p className="text-xs text-terminal-muted">{data.name} • {data.sector}</p>
        </div>
      </div>

      {health_score && (
        <div className="p-3 bg-terminal-bg border-b border-terminal-border flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="relative w-12 h-12">
              <svg className="w-12 h-12 -rotate-90" viewBox="0 0 36 36">
                <circle cx="18" cy="18" r="15.5" fill="none" stroke="rgb(75 85 99 / 0.3)" strokeWidth="3" />
                <circle cx="18" cy="18" r="15.5" fill="none" stroke="currentColor" strokeWidth="3"
                  strokeDasharray={`${(health_score.score / health_score.max) * 100} ${100 - (health_score.score / health_score.max) * 100}`}
                  className={healthColor} strokeLinecap="round" />
              </svg>
              <span className={`absolute inset-0 flex items-center justify-center text-xs font-bold ${healthColor}`}>
                {health_score.score}/{health_score.max}
              </span>
            </div>
            <div>
              <div className="text-[10px] uppercase tracking-wider text-terminal-muted">Health Score</div>
              <span className={`text-sm font-semibold ${healthColor}`}>{health_score.rating}</span>
            </div>
          </div>
        </div>
      )}

      <div className="divide-y divide-terminal-border/50">
        {categories.map(cat => {
          const catData = ratios[cat.key]
          if (!catData) return null
          const labels = ratioLabels[cat.key]
          const validEntries = Object.entries(labels).filter(([k]) => catData[k] != null)
          if (validEntries.length === 0) return null
          const Icon = cat.icon
          return (
            <details key={cat.key} className="group" open>
              <summary className="flex items-center gap-2 p-3 cursor-pointer hover:bg-terminal-bg/50 transition-colors">
                <div className={`p-1.5 rounded-lg ${cat.color}`}>
                  <Icon size={14} />
                </div>
                <span className="text-sm font-semibold flex-1">{cat.label}</span>
                <span className="text-[10px] text-terminal-muted">{validEntries.length} ratios</span>
              </summary>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-px bg-terminal-border border-t border-terminal-border/50">
                {validEntries.map(([k, label]) => {
                  const val = catData[k]
                  const isPct = k.includes('pct') || k.includes('yield') || k.includes('margin')
                  return (
                    <div key={k} className="bg-terminal-card p-3">
                      <div className="text-[10px] uppercase tracking-wider text-terminal-muted mb-1">{label}</div>
                      <span className="text-sm font-semibold">
                        {val != null ? (
                          typeof val === 'number' ? (
                            <span className={val > 0 ? 'text-green-400' : 'text-red-400'}>
                              {val.toFixed(2)}{isPct ? '%' : ''}
                            </span>
                          ) : String(val)
                        ) : '—'}
                      </span>
                    </div>
                  )
                })}
              </div>
            </details>
          )
        })}
      </div>

      {interpretation && (
        <div className="p-3 border-t border-terminal-border flex items-start gap-2">
          <Info size={14} className="text-terminal-muted mt-0.5 flex-shrink-0" />
          <p className="text-xs text-terminal-muted leading-relaxed">{interpretation}</p>
        </div>
      )}
    </div>
  )
}
