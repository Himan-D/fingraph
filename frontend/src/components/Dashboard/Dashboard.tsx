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
  summary?: string
  source: string
  url?: string
  timestamp: string
}

interface SectorData {
  sector: string
  change: number
  volume: number
  count?: number
}

export default function Dashboard() {
  const [indices, setIndices] = useState<IndexData[]>([])
  const [gainers, setGainers] = useState<Mover[]>([])
  const [losers, setLosers] = useState<Mover[]>([])
  const [sectors, setSectors] = useState<SectorData[]>([])
  const [selectedSector, setSelectedSector] = useState<string | null>(null)
  const [sectorStocks, setSectorStocks] = useState<any[]>([])
  const [showSectorModal, setShowSectorModal] = useState(false)
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
          setSectors(sectorsRes.data.data?.slice(0, 12) || [])
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
    const interval = setInterval(fetchData, 30000)
    return () => clearInterval(interval)
  }, [])

  const handleStockClick = (symbol: string) => {
    navigate(`/quotes?symbol=${symbol}`)
  }

  const handleNewsClick = (newsItem: NewsItem) => {
    if (newsItem.url) {
      window.open(newsItem.url, '_blank', 'noopener,noreferrer')
    }
  }

  const handleSectorClick = async (sectorName: string) => {
    setSelectedSector(sectorName)
    setShowSectorModal(true)
    try {
      const res = await axios.get(`/api/v1/screen/run?sector=${encodeURIComponent(sectorName)}&limit=20`)
      if (res.data.success) {
        setSectorStocks(res.data.data || [])
      } else {
        setSectorStocks([])
      }
    } catch (error) {
      console.error('Failed to fetch sector stocks:', error)
      setSectorStocks([])
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-terminal-muted">Loading...</div>
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 xl:grid-cols-12 gap-4 h-full">
      <div className="xl:col-span-8 space-y-4">
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
      
      <div className="xl:col-span-4 space-y-4">
        {/* Market Stats */}
        <div className="bg-terminal-card rounded-xl p-4 border border-terminal-border">
          <h3 className="text-sm font-semibold text-terminal-muted mb-3 flex items-center gap-2">
            <BarChart3 size={16} />
            Market Snapshot
          </h3>
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-[#0d1117] rounded-lg p-3">
              <div className="text-[10px] text-terminal-muted uppercase tracking-wide mb-1">Highs</div>
              <div className="text-2xl font-bold text-green-400">{gainers.length || 8}</div>
              <div className="text-[10px] text-terminal-muted mt-1">stocks advancing</div>
            </div>
            <div className="bg-[#0d1117] rounded-lg p-3">
              <div className="text-[10px] text-terminal-muted uppercase tracking-wide mb-1">Lows</div>
              <div className="text-2xl font-bold text-red-400">{losers.length || 5}</div>
              <div className="text-[10px] text-terminal-muted mt-1">stocks declining</div>
            </div>
            <div className="bg-[#0d1117] rounded-lg p-3">
              <div className="text-[10px] text-terminal-muted uppercase tracking-wide mb-1">Avg Change</div>
              <div className="text-2xl font-bold font-mono text-[#58a6ff]">
                {gainers.length > 0 ? '+' : ''}{(gainers.reduce((acc, g) => acc + (g.pct_change || 0), 0) / Math.max(gainers.length, 1)).toFixed(1)}%
              </div>
              <div className="text-[10px] text-terminal-muted mt-1">top gainers avg</div>
            </div>
            <div className="bg-[#0d1117] rounded-lg p-3">
              <div className="text-[10px] text-terminal-muted uppercase tracking-wide mb-1">Vol Leaders</div>
              <div className="text-2xl font-bold font-mono text-[#a371f7]">{gainers.length > 0 ? gainers[0]?.symbol : 'RELIANCE'}</div>
              <div className="text-[10px] text-terminal-muted mt-1">most active</div>
            </div>
          </div>
        </div>
        
        {/* Sector Heatmap */}
        <div className="bg-terminal-card rounded-xl p-4 border border-terminal-border">
          <h3 className="text-sm font-semibold text-terminal-muted mb-3 flex items-center gap-2">
            <PieChart size={16} />
            Sector Heatmap
          </h3>
          <div className="grid grid-cols-3 gap-2">
            {sectors.map((sector) => {
              const isPositive = (sector.change || 0) >= 0
              const textColor = isPositive ? 'text-green-400' : 'text-red-400'
              return (
                <button
                  key={sector.sector}
                  onClick={() => handleSectorClick(sector.sector)}
                  className="bg-[#0d1117] hover:bg-[#161b22] p-2 rounded-lg border border-[#30363d] hover:border-[#58a6ff] transition-all text-left"
                >
                  <div className="text-xs font-medium text-[#c9d1d9] truncate mb-1">{sector.sector}</div>
                  <div className={`text-sm font-bold ${textColor}`}>
                    {(sector.change || 0) >= 0 ? '+' : ''}{(sector.change || 0).toFixed(2)}%
                  </div>
                </button>
              )
            })}
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

      {/* Sector Detail Modal */}
      {showSectorModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-[#161b22] border border-[#30363d] rounded-xl w-full max-w-2xl max-h-[80vh] overflow-hidden">
            <div className="p-4 border-b border-[#30363d] flex items-center justify-between">
              <div>
                <h2 className="text-lg font-bold">{selectedSector}</h2>
                <p className="text-sm text-[#8b949e]">{sectorStocks.length} stocks in this sector</p>
              </div>
              <button 
                onClick={() => setShowSectorModal(false)}
                className="p-2 hover:bg-[#21262d] rounded-lg transition-colors"
              >
                <span className="text-xl">×</span>
              </button>
            </div>
            <div className="p-4 overflow-auto max-h-[60vh]">
              {sectorStocks.length > 0 ? (
                <div className="space-y-2">
                  {sectorStocks.slice(0, 20).map((stock) => (
                    <div
                      key={stock.symbol}
                      onClick={() => {
                        setShowSectorModal(false)
                        navigate(`/charts?symbol=${stock.symbol}`)
                      }}
                      className="flex items-center justify-between p-3 bg-[#0d1117] rounded-lg hover:bg-[#21262d] cursor-pointer transition-colors"
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-[#21262d] rounded-lg flex items-center justify-center font-bold text-sm">
                          {stock.symbol?.substring(0, 2)}
                        </div>
                        <div>
                          <div className="font-medium">{stock.symbol}</div>
                          <div className="text-xs text-[#8b949e]">{stock.name}</div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="font-mono font-medium">₹{(stock.price || 0).toLocaleString()}</div>
                        <div className={`text-xs font-mono ${(stock.pct_change || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                          {(stock.pct_change || 0) >= 0 ? '+' : ''}{(stock.pct_change || 0).toFixed(2)}%
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-[#8b949e]">
                  No stocks found in this sector
                </div>
              )}
            </div>
            <div className="p-4 border-t border-[#30363d]">
              <button
                onClick={() => {
                  setShowSectorModal(false)
                  navigate(`/screener?sector=${encodeURIComponent(selectedSector || '')}`)
                }}
                className="w-full py-2 bg-[#58a6ff] hover:bg-[#4393e4] text-white rounded-lg font-medium transition-colors"
              >
                View Full Screener
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
