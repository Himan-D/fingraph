import { Gauge, TrendingUp, Percent, DollarSign, Info } from 'lucide-react'

interface WACCCardProps {
  data: Record<string, any>
}

export default function WACCCard({ data }: WACCCardProps) {
  const { inputs } = data
  if (!inputs) return null

  return (
    <div className="bg-terminal-card border border-terminal-border rounded-xl overflow-hidden">
      <div className="flex items-center gap-3 p-3 bg-gradient-to-r from-emerald-500/10 to-teal-500/10 border-b border-terminal-border">
        <div className="p-2 bg-emerald-500/20 rounded-lg">
          <Gauge size={18} className="text-emerald-400" />
        </div>
        <div>
          <h3 className="font-semibold text-sm">WACC Calculation — {data.symbol}</h3>
          <p className="text-xs text-terminal-muted">{data.name} • {data.sector}</p>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-px bg-terminal-border">
        {[
          { label: 'Risk-Free Rate', value: `${inputs.risk_free_rate_pct}%`, icon: Percent },
          { label: 'Market Risk Premium', value: `${inputs.market_risk_premium_pct}%`, icon: TrendingUp },
          { label: 'Beta (Est.)', value: inputs.beta_estimated, icon: Gauge },
        ].map(m => {
          const Icon = m.icon
          return (
            <div key={m.label} className="bg-terminal-card p-3">
              <div className="flex items-center gap-1.5 text-terminal-muted mb-1">
                <Icon size={12} />
                <span className="text-[10px] uppercase tracking-wider">{m.label}</span>
              </div>
              <span className="text-sm font-semibold">{m.value}</span>
            </div>
          )
        })}
      </div>

      <div className="grid grid-cols-3 gap-px bg-terminal-border border-t border-terminal-border">
        {[
          { label: 'Cost of Equity', value: `${inputs.cost_of_equity_pct}%`, icon: TrendingUp },
          { label: 'Cost of Debt (Pre-tax)', value: `${inputs.cost_of_debt_pretax_pct}%`, icon: DollarSign },
          { label: 'Cost of Debt (After-tax)', value: `${inputs.cost_of_debt_aftertax_pct}%`, icon: Percent },
        ].map(m => {
          const Icon = m.icon
          return (
            <div key={m.label} className="bg-terminal-card p-3">
              <div className="flex items-center gap-1.5 text-terminal-muted mb-1">
                <Icon size={12} />
                <span className="text-[10px] uppercase tracking-wider">{m.label}</span>
              </div>
              <span className="text-sm font-semibold">{m.value}</span>
            </div>
          )
        })}
      </div>

      <div className="grid grid-cols-3 gap-px bg-terminal-border border-t border-terminal-border">
        {[
          { label: 'Equity Weight', value: `${inputs.equity_weight_pct}%`, icon: TrendingUp },
          { label: 'Debt Weight', value: `${inputs.debt_weight_pct}%`, icon: DollarSign },
          { label: 'D/E Ratio', value: inputs.debt_to_equity, icon: Percent },
        ].map(m => {
          const Icon = m.icon
          return (
            <div key={m.label} className="bg-terminal-card p-3">
              <div className="flex items-center gap-1.5 text-terminal-muted mb-1">
                <Icon size={12} />
                <span className="text-[10px] uppercase tracking-wider">{m.label}</span>
              </div>
              <span className="text-sm font-semibold">{m.value}</span>
            </div>
          )
        })}
      </div>

      <div className="p-4 bg-terminal-bg border-t border-terminal-border flex items-center justify-between">
        <div>
          <div className="text-[10px] uppercase tracking-wider text-terminal-muted mb-1">Weighted Average Cost of Capital</div>
          <span className="text-2xl font-bold text-emerald-400">{data.wacc_pct}%</span>
        </div>
        {data.current_price && (
          <div className="text-right">
            <div className="text-[10px] uppercase tracking-wider text-terminal-muted mb-1">Current Price</div>
            <span className="text-sm font-semibold">₹{Number(data.current_price).toLocaleString()}</span>
          </div>
        )}
      </div>

      {data.interpretation && (
        <div className="p-3 border-t border-terminal-border flex items-start gap-2">
          <Info size={14} className="text-terminal-muted mt-0.5 flex-shrink-0" />
          <p className="text-xs text-terminal-muted leading-relaxed">{data.interpretation}</p>
        </div>
      )}
    </div>
  )
}
