import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Plus, Star, Clock, TrendingUp, TrendingDown } from 'lucide-react'
import axios from 'axios'

interface Watchlist {
  id: number
  name: string
  symbols: string[]
}

export default function Sidebar() {
  const navigate = useNavigate()
  const [watchlists, setWatchlists] = useState<Watchlist[]>([])
  const [recentStocks, setRecentStocks] = useState<{symbol: string; price: number; pct_change: number}[]>([])

  useEffect(() => {
    const fetchData = async () => {
      try {
        const wlRes = await axios.get('/api/v1/watchlist')
        if (wlRes.data.success) {
          setWatchlists(wlRes.data.data)
        }
        
        // Fetch recent stocks from movers
        const moversRes = await axios.get('/api/v1/quotes/movers')
        if (moversRes.data.success) {
          const gainers = (moversRes.data.data?.gainers || []).slice(0, 5).map((s: any) => ({
            symbol: s.symbol,
            price: s.price,
            pct_change: s.pct_change,
          }))
          setRecentStocks(gainers)
        }
      } catch (error) {
        console.error('Failed to fetch sidebar data:', error)
        // Fallback data
        setRecentStocks([
          { symbol: 'RELIANCE', price: 2965.80, pct_change: 1.55 },
          { symbol: 'TCS', price: 4125.60, pct_change: 0.30 },
          { symbol: 'HDFCBANK', price: 1685.40, pct_change: 1.75 },
          { symbol: 'INFY', price: 1845.20, pct_change: 0.85 },
          { symbol: 'ICICIBANK', price: 985.60, pct_change: 0.87 },
        ])
      }
    }
    
    fetchData()
  }, [])

  const handleStockClick = (symbol: string) => {
    navigate(`/quotes?symbol=${symbol}`)
  }

  return (
    <div className="flex-1 overflow-auto p-3 border-t border-terminal-border">
      {/* Watchlists */}
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-semibold text-terminal-muted uppercase">Watchlists</span>
        <button className="p-1 hover:bg-terminal-border rounded">
          <Plus size={14} />
        </button>
      </div>
      
      <div className="space-y-2">
        {watchlists.length > 0 ? watchlists.map((watchlist) => (
          <div 
            key={watchlist.id}
            className="p-2 rounded-lg hover:bg-terminal-border cursor-pointer transition-colors"
          >
            <div className="flex items-center gap-2 mb-1">
              <Star size={12} className="text-terminal-warning" />
              <span className="text-sm">{watchlist.name}</span>
            </div>
            <div className="text-xs text-terminal-muted">
              {watchlist.symbols.join(' • ')}
            </div>
          </div>
        )) : (
          <div className="p-2 text-xs text-terminal-muted">
            No watchlists yet
          </div>
        )}
      </div>

      {/* Recent Stocks */}
      <div className="mt-4">
        <span className="text-xs font-semibold text-terminal-muted uppercase">Top Gainers</span>
        <div className="mt-2 space-y-1">
          {recentStocks.map((stock) => (
            <div 
              key={stock.symbol}
              onClick={() => handleStockClick(stock.symbol)}
              className="flex items-center justify-between p-2 text-sm hover:bg-terminal-border rounded cursor-pointer transition-colors"
            >
              <div className="flex items-center gap-2">
                {stock.pct_change >= 0 ? (
                  <TrendingUp size={14} className="text-terminal-success" />
                ) : (
                  <TrendingDown size={14} className="text-terminal-danger" />
                )}
                <span className="font-medium">{stock.symbol}</span>
              </div>
              <div className={`font-mono ${stock.pct_change >= 0 ? 'text-terminal-success' : 'text-terminal-danger'}`}>
                {stock.pct_change >= 0 ? '+' : ''}{stock.pct_change.toFixed(2)}%
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Quick Links */}
      <div className="mt-4 pt-4 border-t border-terminal-border">
        <span className="text-xs font-semibold text-terminal-muted uppercase">Quick Links</span>
        <div className="mt-2 space-y-1">
          <button 
            onClick={() => navigate('/screener')}
            className="w-full text-left p-2 text-sm text-terminal-muted hover:bg-terminal-border rounded cursor-pointer"
          >
            Stock Screener
          </button>
          <button 
            onClick={() => navigate('/graph')}
            className="w-full text-left p-2 text-sm text-terminal-muted hover:bg-terminal-border rounded cursor-pointer"
          >
            Knowledge Graph
          </button>
          <button 
            onClick={() => navigate('/ai')}
            className="w-full text-left p-2 text-sm text-terminal-muted hover:bg-terminal-border rounded cursor-pointer"
          >
            Ask AI
          </button>
        </div>
      </div>
    </div>
  )
}
