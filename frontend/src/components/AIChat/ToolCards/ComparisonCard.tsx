import { ArrowRightLeft, TrendingUp, TrendingDown } from 'lucide-react'

interface ComparisonCardProps {
  symbols: string[]
  data: Array<Record<string, any>>
}

export default function ComparisonCard({ symbols, data }: ComparisonCardProps) {
  if (!data.length || !symbols.length) return null

  const metrics = ['pe', 'pb', 'roe', 'roce', 'eps', 'market_cap', 'debt_equity', 'dividend_yield']

  return (
    <div className="bg-terminal-card border border-terminal-border rounded-xl overflow-hidden">
      <div className="flex items-center gap-2 p-3 border-b border-terminal-border bg-gradient-to-r from-purple-500/10 to-pink-500/10">
        <ArrowRightLeft size={16} className="text-purple-400" />
        <h3 className="font-semibold text-sm">Comparison: {symbols.join(' vs ')}</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-terminal-border">
              <th className="text-left p-2 text-[10px] uppercase text-terminal-muted font-medium">Metric</th>
              {symbols.map(s => (
                <th key={s} className="text-right p-2 text-[10px] uppercase text-terminal-muted font-medium">{s}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {metrics.map(metric => {
              const vals = symbols.map(s => {
                const row = data.find(d => d.symbol === s)
                return row ? row[metric] : null
              })
              const isPct = metric === 'roe' || metric === 'roce' || metric === 'dividend_yield'
              return (
                <tr key={metric} className="border-b border-terminal-border/50 hover:bg-terminal-bg/50 transition-colors">
                  <td className="p-2 font-medium capitalize">{metric.replace(/_/g, ' ')}</td>
                  {vals.map((val, i) => (
                    <td key={i} className={`p-2 text-right font-mono text-xs ${typeof val === 'number' && metric === 'debt_equity' ? (val < 0.5 ? 'text-green-400' : 'text-orange-400') : ''}`}>
                      {val != null ? (
                        <span className="inline-flex items-center gap-1 justify-end">
                          {typeof val === 'number' && (metric === 'roe' || metric === 'roce') && (
                            val > 0 ? <TrendingUp size={10} className="text-green-400" /> : <TrendingDown size={10} className="text-red-400" />
                          )}
                          {typeof val === 'number' ? val.toFixed(2) : String(val)}
                          {isPct ? '%' : ''}
                        </span>
                      ) : '—'}
                    </td>
                  ))}
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
