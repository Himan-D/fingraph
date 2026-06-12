import { Brain, AlertTriangle, TrendingDown, Gauge } from 'lucide-react'

interface RiskCardProps {
  symbol: string
  data: Record<string, any>
}

export default function RiskCard({ symbol, data }: RiskCardProps) {
  const sections = [
    { label: 'VaR (95%)', value: data.var_95, icon: AlertTriangle, color: data.var_95 && Math.abs(data.var_95) > 5 ? 'text-red-400' : 'text-yellow-400' },
    { label: 'VaR (99%)', value: data.var_99, icon: AlertTriangle, color: 'text-orange-400' },
    { label: 'Expected Shortfall', value: data.expected_shortfall, icon: TrendingDown, color: 'text-red-400' },
    { label: 'Beta', value: data.beta, icon: Gauge, color: data.beta && data.beta > 1.2 ? 'text-red-400' : 'text-green-400' },
    { label: 'Volatility', value: data.volatility ? `${(data.volatility * 100).toFixed(1)}%` : null, icon: TrendingDown, color: 'text-yellow-400' },
    { label: 'Stress Loss', value: data.stress_loss ? `₹${Number(data.stress_loss).toLocaleString()}` : null, icon: AlertTriangle, color: data.stress_loss && Math.abs(data.stress_loss) > 100000 ? 'text-red-400' : 'text-yellow-400' },
  ]

  return (
    <div className="bg-terminal-card border border-terminal-border rounded-xl overflow-hidden">
      <div className="flex items-center gap-3 p-3 border-b border-terminal-border bg-gradient-to-r from-red-500/10 to-orange-500/10">
        <div className="p-2 bg-red-500/20 rounded-lg">
          <Brain size={18} className="text-red-400" />
        </div>
        <div>
          <h3 className="font-semibold text-sm">Risk Analysis — {symbol}</h3>
          <p className="text-xs text-terminal-muted">Monte Carlo • VaR • Stress Test</p>
        </div>
      </div>
      <div className="grid grid-cols-3 gap-px bg-terminal-border">
        {sections.map(s => (
          <div key={s.label} className="bg-terminal-card p-3">
            <div className="flex items-center gap-1.5 text-terminal-muted mb-1">
              <s.icon size={12} />
              <span className="text-[10px] uppercase tracking-wider">{s.label}</span>
            </div>
            <span className={`text-sm font-semibold ${s.color}`}>{s.value != null ? s.value : '—'}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
