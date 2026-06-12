import { TrendingUp, DollarSign, BarChart3, Target, PieChart } from 'lucide-react'

interface QuoteCardProps {
  symbol: string
  data: Record<string, any>
}

export default function QuoteCard({ symbol, data }: QuoteCardProps) {
  const metrics = [
    { label: 'Price', value: data.price ? `₹${Number(data.price).toLocaleString()}` : null, icon: DollarSign },
    { label: 'P/E', value: data.pe, icon: BarChart3 },
    { label: 'P/B', value: data.pb, icon: PieChart },
    { label: 'ROE', value: data.roe ? `${data.roe}%` : null, icon: TrendingUp },
    { label: 'ROCE', value: data.roce ? `${data.roce}%` : null, icon: Target },
    { label: 'Market Cap', value: data.market_cap ? `₹${(Number(data.market_cap) / 10000000).toFixed(2)}Cr` : null, icon: BarChart3 },
    { label: 'EPS', value: data.eps, icon: DollarSign },
    { label: 'Debt/Equity', value: data.debt_equity, icon: PieChart },
  ]

  return (
    <div className="bg-terminal-card border border-terminal-border rounded-xl overflow-hidden">
      <div className="flex items-center gap-3 p-3 bg-gradient-to-r from-blue-500/10 to-purple-500/10 border-b border-terminal-border">
        <div className="p-2 bg-blue-500/20 rounded-lg">
          <TrendingUp size={18} className="text-blue-400" />
        </div>
        <div>
          <h3 className="font-semibold text-sm">{symbol}</h3>
          <p className="text-xs text-terminal-muted">Quote Snapshot</p>
        </div>
      </div>
      <div className="grid grid-cols-4 gap-px bg-terminal-border">
        {metrics.map(m => {
          const Icon = m.icon
          return (
            <div key={m.label} className="bg-terminal-card p-3">
              <div className="flex items-center gap-1.5 text-terminal-muted mb-1">
                <Icon size={12} />
                <span className="text-[10px] uppercase tracking-wider">{m.label}</span>
              </div>
              <span className="text-sm font-semibold">{m.value ?? '—'}</span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
