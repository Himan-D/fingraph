import { PieChart, TrendingUp, Scale, Calculator, Info } from 'lucide-react'

interface DuPontCardProps {
  data: Record<string, any>
}

export default function DuPontCard({ data }: DuPontCardProps) {
  const { components, result, interpretation } = data
  if (!components) return null

  const duPontComponents = [
    { label: 'Net Profit Margin', value: components.net_profit_margin_pct != null ? `${components.net_profit_margin_pct}%` : null, icon: TrendingUp },
    { label: 'Asset Turnover', value: components.asset_turnover != null ? components.asset_turnover.toFixed(3) : null, icon: Scale },
    { label: 'Equity Multiplier', value: components.equity_multiplier != null ? components.equity_multiplier.toFixed(2) : null, icon: Calculator },
  ]

  return (
    <div className="bg-terminal-card border border-terminal-border rounded-xl overflow-hidden">
      <div className="flex items-center gap-3 p-3 bg-gradient-to-r from-violet-500/10 to-indigo-500/10 border-b border-terminal-border">
        <div className="p-2 bg-violet-500/20 rounded-lg">
          <PieChart size={18} className="text-violet-400" />
        </div>
        <div>
          <h3 className="font-semibold text-sm">DuPont Analysis — {data.symbol}</h3>
          <p className="text-xs text-terminal-muted">{data.name}</p>
        </div>
      </div>

      <div className="p-3 bg-terminal-bg border-b border-terminal-border">
        <div className="flex items-center justify-center gap-2 text-xs text-terminal-muted">
          <span className="text-blue-400 font-semibold">NPM</span>
          <span>×</span>
          <span className="text-purple-400 font-semibold">AT</span>
          <span>×</span>
          <span className="text-amber-400 font-semibold">EM</span>
          <span>=</span>
          <span className="text-violet-400 font-semibold">ROE</span>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-px bg-terminal-border">
        {duPontComponents.map(c => {
          const Icon = c.icon
          return (
            <div key={c.label} className={`bg-terminal-card p-3 ${c.value == null ? 'opacity-50' : ''}`}>
              <div className="flex items-center gap-1.5 text-terminal-muted mb-1">
                <Icon size={12} />
                <span className="text-[10px] uppercase tracking-wider">{c.label}</span>
              </div>
              <span className="text-sm font-semibold">{c.value ?? '—'}</span>
            </div>
          )
        })}
      </div>

      {result && (
        <div className="grid grid-cols-2 gap-px bg-terminal-border border-t border-terminal-border">
          <div className="bg-terminal-card p-3">
            <div className="text-[10px] uppercase tracking-wider text-terminal-muted mb-1">Calculated ROE</div>
            <span className={`text-sm font-semibold ${result.calculated_roe_pct != null ? 'text-cyan-400' : ''}`}>
              {result.calculated_roe_pct != null ? `${result.calculated_roe_pct}%` : '—'}
            </span>
          </div>
          <div className="bg-terminal-card p-3">
            <div className="text-[10px] uppercase tracking-wider text-terminal-muted mb-1">Actual ROE</div>
            <span className="text-sm font-semibold">{result.actual_roe_pct != null ? `${result.actual_roe_pct}%` : '—'}</span>
          </div>
        </div>
      )}

      {interpretation && (
        <div className="p-3 border-t border-terminal-border flex items-start gap-2">
          <Info size={14} className="text-terminal-muted mt-0.5 flex-shrink-0" />
          <p className="text-xs text-terminal-muted leading-relaxed">{interpretation}</p>
        </div>
      )}
    </div>
  )
}
