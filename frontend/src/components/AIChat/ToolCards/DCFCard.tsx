import { Calculator, TrendingUp, DollarSign, Target, BarChart3 } from 'lucide-react'

interface DCFCardProps {
  data: Record<string, any>
}

export default function DCFCard({ data }: DCFCardProps) {
  const { assumptions, projections, terminal_value, valuation } = data
  if (!valuation) return null

  const verdictColor =
    valuation.verdict === 'Undervalued' ? 'text-green-400 bg-green-500/10' :
    valuation.verdict === 'Overvalued' ? 'text-red-400 bg-red-500/10' :
    'text-yellow-400 bg-yellow-500/10'

  return (
    <div className="bg-terminal-card border border-terminal-border rounded-xl overflow-hidden">
      <div className="flex items-center gap-3 p-3 bg-gradient-to-r from-cyan-500/10 to-teal-500/10 border-b border-terminal-border">
        <div className="p-2 bg-cyan-500/20 rounded-lg">
          <Calculator size={18} className="text-cyan-400" />
        </div>
        <div>
          <h3 className="font-semibold text-sm">DCF Valuation — {data.symbol}</h3>
          <p className="text-xs text-terminal-muted">{data.name} • {data.valuation_date}</p>
        </div>
      </div>

      {assumptions && (
        <div className="grid grid-cols-5 gap-px bg-terminal-border">
          {[
            { label: 'Base FCF', value: `₹${assumptions.base_fcf_cr}Cr`, icon: DollarSign },
            { label: 'Growth Rate', value: `${assumptions.fcf_growth_rate_pct}%`, icon: TrendingUp },
            { label: 'WACC', value: `${assumptions.wacc_pct}%`, icon: BarChart3 },
            { label: 'Terminal Growth', value: `${assumptions.terminal_growth_pct}%`, icon: Target },
            { label: 'Projection Years', value: assumptions.projection_years, icon: Calculator },
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
      )}

      {projections && projections.length > 0 && (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-terminal-border">
                <th className="text-left p-2 text-[10px] uppercase text-terminal-muted font-medium">Year</th>
                <th className="text-right p-2 text-[10px] uppercase text-terminal-muted font-medium">Proj. FCF (₹Cr)</th>
                <th className="text-right p-2 text-[10px] uppercase text-terminal-muted font-medium">Discount Factor</th>
                <th className="text-right p-2 text-[10px] uppercase text-terminal-muted font-medium">PV of FCF (₹Cr)</th>
              </tr>
            </thead>
            <tbody>
              {projections.map((p: any) => (
                <tr key={p.year} className="border-b border-terminal-border/50 hover:bg-terminal-bg/50 transition-colors">
                  <td className="p-2 font-medium">Year {p.year}</td>
                  <td className="p-2 text-right font-mono text-xs">{p.projected_fcf_cr}</td>
                  <td className="p-2 text-right font-mono text-xs">{p.discount_factor}</td>
                  <td className="p-2 text-right font-mono text-xs text-green-400">{p.pv_of_fcf_cr}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {terminal_value && (
        <div className="grid grid-cols-3 gap-px bg-terminal-border border-t border-terminal-border">
          {[
            { label: 'Terminal FCF', value: `₹${terminal_value.terminal_fcf_cr}Cr` },
            { label: 'Terminal Value', value: `₹${terminal_value.terminal_value_cr}Cr` },
            { label: 'PV of Terminal Value', value: `₹${terminal_value.pv_of_terminal_value_cr}Cr` },
          ].map(m => (
            <div key={m.label} className="bg-terminal-card p-3">
              <div className="text-[10px] uppercase tracking-wider text-terminal-muted mb-1">{m.label}</div>
              <span className="text-sm font-semibold">{m.value}</span>
            </div>
          ))}
        </div>
      )}

      <div className="p-3 bg-terminal-bg border-t border-terminal-border">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-3">
          <div>
            <div className="text-[10px] uppercase tracking-wider text-terminal-muted mb-1">Enterprise Value</div>
            <span className="text-sm font-semibold">₹{valuation.total_enterprise_value_cr}Cr</span>
          </div>
          <div>
            <div className="text-[10px] uppercase tracking-wider text-terminal-muted mb-1">Net Debt Est.</div>
            <span className="text-sm font-semibold text-orange-400">₹{valuation.net_debt_estimate_cr}Cr</span>
          </div>
          <div>
            <div className="text-[10px] uppercase tracking-wider text-terminal-muted mb-1">Equity Value</div>
            <span className="text-sm font-semibold">₹{valuation.equity_value_cr}Cr</span>
          </div>
          <div>
            <div className="text-[10px] uppercase tracking-wider text-terminal-muted mb-1">Intrinsic Value/Share</div>
            <span className="text-sm font-bold text-cyan-400">₹{valuation.intrinsic_value_per_share}</span>
          </div>
        </div>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-1">
              <DollarSign size={12} className="text-terminal-muted" />
              <span className="text-xs text-terminal-muted">Current: ₹{valuation.current_price}</span>
            </div>
            <div className="flex items-center gap-1">
              <TrendingUp size={12} className="text-terminal-muted" />
              <span className={`text-xs font-semibold ${valuation.upside_pct > 0 ? 'text-green-400' : 'text-red-400'}`}>
                {valuation.upside_pct > 0 ? '+' : ''}{valuation.upside_pct}%
              </span>
            </div>
          </div>
          <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${verdictColor}`}>
            {valuation.verdict}
          </span>
        </div>
      </div>
    </div>
  )
}
