import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { TrendingUp, TrendingDown, Activity, BarChart3, PieChart, Clock, ChevronRight } from 'lucide-react'
import axios from 'axios'

interface IndexData {
  symbol: string
  name: string
  price: number
  change: number
  pct_change: number
}

interface Mover {
  symbol: string
  name: string
  price: number
  change: number
  pct_change: number
}

interface NewsItem {
  id: number
  headline: string
  source: string
  timestamp: string
}

export default function Dashboard() {
  const [indices, setIndices] = useState<IndexData[]>([])
  const [gainers, setGainers] = useState<Mover[]>([])
  const [losers, setLosers] = useState<Mover[]>([])
  const [sectors, setSectors] = useState<{sector: string; change: number}[]>([])
  const [news, setNews] = useState<NewsItem[]>([])
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [indicesRes, moversRes, sectorsRes, newsRes] = await Promise.all([
          axios.get('/api/v1/quotes/indices'),
          axios.get('/api/v1/quotes/movers'),
          axios.get('/api/v1/quotes/sectors'),
          axios.get('/api/v1/news'),
        ])
        
        if (indicesRes.data.success) {
          setIndices(indicesRes.data.data || [])
        }
        
        if (moversRes.data.success) {
          setGainers(moversRes.data.data?.gainers?.slice(0, 5) || [])
          setLosers(moversRes.data.data?.losers?.slice(0, 5) || [])
        }
        
        if (sectorsRes.data.success) {
          setSectors(sectorsRes.data.data?.slice(0, 6) || [])
        }
        
        if (newsRes.data.success) {
          setNews(newsRes.data.data?.slice(0, 6) || [])
        }
      } catch (error) {
        console.error('Failed to fetch dashboard data:', error)
        // Fallback data
        setIndices([
          { symbol: 'NIFTY50', name: 'Nifty 50', price: 22815.26, change: 365.26, pct_change: 1.63 },
          { symbol: 'BANKNIFTY', name: 'Bank Nifty', price: 48520.5, change: 420.8, pct_change: 0.87 },
        ])
        setGainers([
          { symbol: 'ONGC', name: 'ONGC', price: 281.95, change: 11.45, pct_change: 4.23 },
          { symbol: 'WIPRO', name: 'Wipro', price: 191.6, change: 2.55, pct_change: 1.35 },
        ])
        setNews([
          { id: 1, headline: 'Market update: Nifty hits new high', source: 'ET', timestamp: new Date().toISOString() },
        ])
      } finally {
        setLoading(false)
      }
    }
    
    fetchData()
    const interval = setInterval(fetchData, 60000)
    return () => clearInterval(interval)
  }, [])

  const handleStockClick = (symbol: string) => {
    navigate(`/quotes?symbol=${symbol}`)
  }

  const handleNewsClick = (newsItem: NewsItem) => {
    // Could open news detail modal or external link
    console.log('News clicked:', newsItem)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-terminal-muted">Loading...</div>
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
      <div className="lg:col-span-2 space-y-4">
        {/* Market Overview */}
        <div className="bg-terminal-card rounded-xl p-4 border border-terminal-border">
          <h3 className="text-sm font-semibold text-terminal-muted mb-3 flex items-center gap-2">
            <Activity size={16} />
            Market Overview
            <button 
              onClick={() => navigate('/quotes')}
              className="ml-auto text-xs text-terminal-accent hover:underline flex items-center gap-1"
            >
              View All <ChevronRight size={12} />
            </button>
          </h3>
          <div className="grid grid-cols-2 gap-3">
            {indices.map((index) => (
              <div 
                key={index.symbol} 
                className="bg-terminal-bg rounded-lg p-3 cursor-pointer hover:bg-terminal-border transition-colors"
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs text-terminal-muted">{index.name}</span>
                  <span className={`text-xs ${(index.pct_change || 0) >= 0 ? 'text-terminal-success' : 'text-terminal-danger'}`}>
                    {(index.pct_change || 0) >= 0 ? <TrendingUp size={12} className="inline" /> : <TrendingDown size={12} className="inline" />}
                  </span>
                </div>
                <div className="font-mono text-lg font-semibold">{(index.price || 0).toLocaleString()}</div>
                <div className={`text-xs font-mono ${(index.change || 0) >= 0 ? 'text-terminal-success' : 'text-terminal-danger'}`}>
                  {(index.change || 0) >= 0 ? '+' : ''}{(index.change || 0).toFixed(2)} ({(index.pct_change || 0).toFixed(2)}%)
                </div>
              </div>
            ))}
          </div>
        </div>
        
        {/* Gainers & Losers */}
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-terminal-card rounded-xl p-4 border border-terminal-border">
            <h3 className="text-sm font-semibold text-terminal-success mb-3 flex items-center gap-2">
              <TrendingUp size={16} />
              Top Gainers
            </h3>
            <div className="space-y-2">
              {gainers.map((stock) => (
                <div 
                  key={stock.symbol} 
                  onClick={() => handleStockClick(stock.symbol)}
                  className="flex items-center justify-between p-2 bg-terminal-bg rounded-lg hover:bg-terminal-border cursor-pointer transition-colors"
                >
                  <div>
                    <div className="font-medium text-sm">{stock.symbol}</div>
                    <div className="text-xs text-terminal-muted truncate max-w-[100px]">{stock.name}</div>
                  </div>
                  <div className="text-right">
                    <div className="font-mono text-sm">{(stock.price || 0).toFixed(2)}</div>
                    <div className="text-xs text-terminal-success font-mono">+{(stock.pct_change || 0).toFixed(2)}%</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
          
          <div className="bg-terminal-card rounded-xl p-4 border border-terminal-border">
            <h3 className="text-sm font-semibold text-terminal-danger mb-3 flex items-center gap-2">
              <TrendingDown size={16} />
              Top Losers
            </h3>
            <div className="space-y-2">
              {losers.map((stock) => (
                <div 
                  key={stock.symbol} 
                  onClick={() => handleStockClick(stock.symbol)}
                  className="flex items-center justify-between p-2 bg-terminal-bg rounded-lg hover:bg-terminal-border cursor-pointer transition-colors"
                >
                  <div>
                    <div className="font-medium text-sm">{stock.symbol}</div>
                    <div className="text-xs text-terminal-muted truncate max-w-[100px]">{stock.name}</div>
                  </div>
                  <div className="text-right">
                    <div className="font-mono text-sm">{(stock.price || 0).toFixed(2)}</div>
                    <div className="text-xs text-terminal-danger font-mono">{(stock.pct_change || 0).toFixed(2)}%</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
      
      <div className="space-y-4">
        {/* Market Stats */}
        <div className="bg-terminal-card rounded-xl p-4 border border-terminal-border">
          <h3 className="text-sm font-semibold text-terminal-muted mb-3 flex items-center gap-2">
            <BarChart3 size={16} />
            Market Stats
          </h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-sm text-terminal-muted">Advance/Decline</span>
              <span className="text-sm text-terminal-success">1250 / 850</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-terminal-muted">Circuit Breakers</span>
              <span className="text-sm">2</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-terminal-muted">Total Volume</span>
              <span className="text-sm font-mono">45,250 Cr</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-terminal-muted">FII Net Buy</span>
              <span className="text-sm text-terminal-success">+2,450 Cr</span>
            </div>
          </div>
        </div>
        
        {/* Sector Heatmap */}
        <div className="bg-terminal-card rounded-xl p-4 border border-terminal-border">
          <h3 className="text-sm font-semibold text-terminal-muted mb-3 flex items-center gap-2">
            <PieChart size={16} />
            Sector Heatmap
          </h3>
          <div className="space-y-2">
            {sectors.map((sector) => (
              <div 
                key={sector.sector} 
                className="flex items-center justify-between cursor-pointer hover:bg-terminal-bg rounded p-1 -mx-1 transition-colors"
              >
                <span className="text-sm">{sector.sector}</span>
                <div className="flex items-center gap-2">
                  <div className="w-16 h-2 bg-terminal-border rounded-full overflow-hidden">
                    <div 
                      className={`h-full ${(sector.change || 0) >= 0 ? 'bg-terminal-success' : 'bg-terminal-danger'}`}
                      style={{ width: `${Math.min(Math.abs(sector.change || 0) * 20, 100)}%` }}
                    />
                  </div>
                  <span className={`text-xs font-mono w-12 text-right ${(sector.change || 0) >= 0 ? 'text-terminal-success' : 'text-terminal-danger'}`}>
                    {(sector.change || 0) >= 0 ? '+' : ''}{(sector.change || 0).toFixed(2)}%
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
        
        {/* Latest News */}
        <div className="bg-terminal-card rounded-xl p-4 border border-terminal-border">
          <h3 className="text-sm font-semibold text-terminal-muted mb-3 flex items-center gap-2">
            <Clock size={16} />
            Latest News
          </h3>
          <div className="space-y-2">
            {news.map((item) => (
              <div 
                key={item.id} 
                onClick={() => handleNewsClick(item)}
                className="text-sm p-2 bg-terminal-bg rounded cursor-pointer hover:bg-terminal-border transition-colors"
              >
                <div className="font-medium mb-1 line-clamp-2">{item.headline}</div>
                <div className="text-xs text-terminal-muted flex items-center justify-between">
                  <span>{item.source}</span>
                  <span>{new Date(item.timestamp).toLocaleTimeString()}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
