import { useState, useEffect } from 'react'
import { ArrowUp, ArrowDown } from 'lucide-react'
import axios from 'axios'

interface Quote {
  symbol: string
  price: number
  change: number
  pctChange: number
}

const defaultQuotes: Quote[] = [
  { symbol: 'RELIANCE', price: 2965.80, change: 45.25, pctChange: 1.55 },
  { symbol: 'TCS', price: 4125.60, change: -12.40, pctChange: -0.30 },
  { symbol: 'HDFCBANK', price: 1685.40, change: 28.90, pctChange: 1.75 },
  { symbol: 'INFY', price: 1845.20, change: 15.60, pctChange: 0.85 },
  { symbol: 'ICICIBANK', price: 985.60, change: 8.45, pctChange: 0.87 },
  { symbol: 'SBIN', price: 725.80, change: -5.20, pctChange: -0.71 },
  { symbol: 'WIPRO', price: 485.20, change: 6.80, pctChange: 1.42 },
  { symbol: 'LT', price: 3256.40, change: 42.10, pctChange: 1.31 },
  { symbol: 'HINDUNILVR', price: 2685.90, change: 18.30, pctChange: 0.69 },
  { symbol: 'KOTAKBANK', price: 1785.60, change: 22.40, pctChange: 1.27 },
]

export default function QuoteBoard() {
  const [quotes, setQuotes] = useState<Quote[]>(defaultQuotes)

  useEffect(() => {
    const fetchQuotes = async () => {
      try {
        const symbols = quotes.map(q => q.symbol).join(',')
        const response = await axios.get(`/api/v1/quotes/batch?symbols=${symbols}`)
        if (response.data.success && response.data.data.length > 0) {
          const mapped = response.data.data.map((q: Record<string, unknown>) => ({
            symbol: q.symbol as string,
            price: (q.price as number) || 0,
            change: (q.change as number) || 0,
            pctChange: (q.pct_change as number) || 0
          }))
          setQuotes(mapped)
        }
      } catch (error) {
        // Use default quotes on error
      }
    }

    const interval = setInterval(fetchQuotes, 60000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="h-10 bg-terminal-bg border-b border-terminal-border overflow-hidden">
      <div className="flex items-center h-full">
        {quotes.map((quote) => (
          <div 
            key={quote.symbol}
            className="flex items-center gap-2 px-4 h-full border-r border-terminal-border whitespace-nowrap"
          >
            <span className="font-mono text-sm font-medium">{quote.symbol}</span>
            <span className="font-mono text-sm">{quote.price.toFixed(2)}</span>
            <span className={`flex items-center text-xs font-mono ${quote.change >= 0 ? 'text-terminal-success' : 'text-terminal-danger'}`}>
              {quote.change >= 0 ? <ArrowUp size={12} /> : <ArrowDown size={12} />}
              {Math.abs(quote.pctChange).toFixed(2)}%
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
