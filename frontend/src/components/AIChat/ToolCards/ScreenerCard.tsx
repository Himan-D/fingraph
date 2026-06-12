import { Filter, TrendingUp, TrendingDown } from 'lucide-react'

interface ScreenerCardProps {
  results: Array<Record<string, any>>
}

export default function ScreenerCard({ results }: ScreenerCardProps) {
  if (!results.length) return null

  const cols = Object.keys(results[0]).filter(k => k !== 'symbol')
  const topCols = cols.slice(0, 5)

  return (
    <div className="bg-terminal-card border border-terminal-border rounded-xl overflow-hidden">
      <div className="flex items-center gap-2 p-3 border-b border-terminal-border bg-gradient-to-r from-green-500/10 to-emerald-500/10">
        <Filter size={16} className="text-green-400" />
        <h3 className="font-semibold text-sm">Screener Results ({results.length})</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-terminal-border">
              <th className="text-left p-2 text-[10px] uppercase text-terminal-muted font-medium">Symbol</th>
              {topCols.map(col => (
                <th key={col} className="text-right p-2 text-[10px] uppercase text-terminal-muted font-medium">
                  {col.replace(/_/g, ' ')}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {results.slice(0, 20).map((row, i) => (
              <tr key={i} className="border-b border-terminal-border/50 hover:bg-terminal-bg/50 transition-colors">
                <td className="p-2 font-medium">{row.symbol}</td>
                {topCols.map(col => {
                  const val = row[col]
                  const isPct = typeof val === 'number' && col.toLowerCase().includes('return') || col.toLowerCase().includes('growth')
                  const isPos = typeof val === 'number' && val > 0
                  return (
                    <td key={col} className={`p-2 text-right font-mono text-xs ${isPct ? (isPos ? 'text-green-400' : 'text-red-400') : ''}`}>
                      {val != null ? (
                        <span className="inline-flex items-center gap-1">
                          {isPct && (isPos ? <TrendingUp size={10} /> : <TrendingDown size={10} />)}
                          {typeof val === 'number' ? val.toFixed(2) : String(val)}
                          {isPct ? '%' : ''}
                        </span>
                      ) : '—'}
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
