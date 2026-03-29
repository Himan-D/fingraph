import { useState, useEffect } from 'react'
import { Search, TrendingUp, TrendingDown, Star, Filter, ChevronRight } from 'lucide-react'
import axios from 'axios'

interface Stock {
  symbol: string
  name: string
  price: number
  change: number
  pct_change: number
  volume: number
}

interface StockDetail {
  symbol: string
  name: string
  sector: string
  industry: string
  price: number
  change: number
  pct_change: number
  open: number
  high: number
  low: number
  volume: number
  market_cap: number
  pe_ratio: number
  week52_high: number
  week52_low: number
}

export default function Quotes() {
  const [stocks, setStocks] = useState<Stock[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedStock, setSelectedStock] = useState<string | null>(null)
  const [stockDetail, setStockDetail] = useState<StockDetail | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchStocks()
  }, [])

  const fetchStocks = async () => {
    try {
      const response = await axios.get('/api/v1/quotes/movers')
      if (response.data.success) {
        const allStocks = [
          ...(response.data.data?.gainers || []),
          ...(response.data.data?.losers || [])
        ]
        setStocks(allStocks)
      }
    } catch (error) {
      console.error('Failed to fetch stocks:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchStockDetail = async (symbol: string) => {
    try {
      const response = await axios.get(`/api/v1/quotes/${symbol}`)
      if (response.data.success) {
        setStockDetail(response.data.data)
      }
    } catch (error) {
      console.error('Failed to fetch stock detail:', error)
    }
  }

  const handleStockClick = (symbol: string) => {
    setSelectedStock(symbol)
    fetchStockDetail(symbol)
  }

  const filteredStocks = stocks.filter(stock =>
    stock.symbol.toLowerCase().includes(searchQuery.toLowerCase()) ||
    stock.name?.toLowerCase().includes(searchQuery.toLowerCase())
  )

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-terminal-muted">Loading stocks...</div>
      </div>
    )
  }

  return (
    <div className="flex h-full gap-4">
      {/* Stock List */}
      <div className="w-1/2 flex flex-col bg-terminal-card rounded-xl border border-terminal-border overflow-hidden">
        <div className="p-4 border-b border-terminal-border">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-terminal-muted" size={16} />
            <input
              type="text"
              placeholder="Search stocks..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-4 py-2 bg-terminal-bg border border-terminal-border rounded-lg text-sm focus:border-terminal-accent transition-colors"
            />
          </div>
        </div>
        
        <div className="flex-1 overflow-auto">
          <table className="w-full">
            <thead className="bg-terminal-bg sticky top-0">
              <tr className="text-left text-xs text-terminal-muted">
                <th className="p-3 font-medium">Symbol</th>
                <th className="p-3 font-medium">Price</th>
                <th className="p-3 font-medium">Change</th>
                <th className="p-3 font-medium">Volume</th>
              </tr>
            </thead>
            <tbody>
              {filteredStocks.map((stock) => (
                <tr
                  key={stock.symbol}
                  onClick={() => handleStockClick(stock.symbol)}
                  className={`border-t border-terminal-border cursor-pointer hover:bg-terminal-border transition-colors ${
                    selectedStock === stock.symbol ? 'bg-terminal-accent/10' : ''
                  }`}
                >
                  <td className="p-3">
                    <div className="font-medium">{stock.symbol}</div>
                    <div className="text-xs text-terminal-muted truncate max-w-[150px]">{stock.name}</div>
                  </td>
                  <td className="p-3 font-mono">{(stock.price || 0).toFixed(2)}</td>
                  <td className={`p-3 font-mono ${(stock.pct_change || 0) >= 0 ? 'text-terminal-success' : 'text-terminal-danger'}`}>
                    {(stock.pct_change || 0) >= 0 ? '+' : ''}{(stock.pct_change || 0).toFixed(2)}%
                  </td>
                  <td className="p-3 font-mono text-sm text-terminal-muted">
                    {((stock.volume || 0) / 1000000).toFixed(1)}M
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Stock Detail */}
      <div className="w-1/2 flex flex-col bg-terminal-card rounded-xl border border-terminal-border overflow-hidden">
        {stockDetail ? (
          <>
            <div className="p-4 border-b border-terminal-border">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-xl font-semibold">{stockDetail.symbol}</h2>
                  <p className="text-sm text-terminal-muted">{stockDetail.name}</p>
                </div>
                <button className="p-2 hover:bg-terminal-border rounded-lg transition-colors">
                  <Star size={20} className="text-terminal-warning" />
                </button>
              </div>
            </div>

            <div className="flex-1 overflow-auto p-4 space-y-4">
              {/* Price Card */}
              <div className="bg-terminal-bg rounded-xl p-4">
                <div className="text-3xl font-bold font-mono mb-1">
                  ₹{(stockDetail.price || 0).toFixed(2)}
                </div>
                <div className={`flex items-center gap-2 text-lg font-mono ${
                  (stockDetail.pct_change || 0) >= 0 ? 'text-terminal-success' : 'text-terminal-danger'
                }`}>
                  {(stockDetail.pct_change || 0) >= 0 ? <TrendingUp size={20} /> : <TrendingDown size={20} />}
                  {(stockDetail.change || 0) >= 0 ? '+' : ''}{(stockDetail.change || 0).toFixed(2)} ({(stockDetail.pct_change || 0).toFixed(2)}%)
                </div>
              </div>

              {/* Key Stats */}
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-terminal-bg rounded-lg p-3">
                  <div className="text-xs text-terminal-muted mb-1">Open</div>
                  <div className="font-mono">₹{(stockDetail.open || 0).toFixed(2)}</div>
                </div>
                <div className="bg-terminal-bg rounded-lg p-3">
                  <div className="text-xs text-terminal-muted mb-1">High</div>
                  <div className="font-mono">₹{(stockDetail.high || 0).toFixed(2)}</div>
                </div>
                <div className="bg-terminal-bg rounded-lg p-3">
                  <div className="text-xs text-terminal-muted mb-1">Low</div>
                  <div className="font-mono">₹{(stockDetail.low || 0).toFixed(2)}</div>
                </div>
                <div className="bg-terminal-bg rounded-lg p-3">
                  <div className="text-xs text-terminal-muted mb-1">Volume</div>
                  <div className="font-mono">{((stockDetail.volume || 0) / 1000000).toFixed(1)}M</div>
                </div>
              </div>

              {/* More Stats */}
              <div className="space-y-2">
                <div className="flex justify-between py-2 border-b border-terminal-border">
                  <span className="text-terminal-muted">Sector</span>
                  <span>{stockDetail.sector || 'N/A'}</span>
                </div>
                <div className="flex justify-between py-2 border-b border-terminal-border">
                  <span className="text-terminal-muted">Industry</span>
                  <span>{stockDetail.industry || 'N/A'}</span>
                </div>
                <div className="flex justify-between py-2 border-b border-terminal-border">
                  <span className="text-terminal-muted">Market Cap</span>
                  <span className="font-mono">{((stockDetail.market_cap || 0) / 10000000).toFixed(1)}L Cr</span>
                </div>
                <div className="flex justify-between py-2 border-b border-terminal-border">
                  <span className="text-terminal-muted">P/E Ratio</span>
                  <span className="font-mono">{(stockDetail.pe_ratio || 0).toFixed(2)}</span>
                </div>
                <div className="flex justify-between py-2 border-b border-terminal-border">
                  <span className="text-terminal-muted">52W High</span>
                  <span className="font-mono text-terminal-success">₹{(stockDetail.week52_high || 0).toFixed(2)}</span>
                </div>
                <div className="flex justify-between py-2">
                  <span className="text-terminal-muted">52W Low</span>
                  <span className="font-mono text-terminal-danger">₹{(stockDetail.week52_low || 0).toFixed(2)}</span>
                </div>
              </div>

              {/* Quick Actions */}
              <div className="flex gap-2 pt-2">
                <button 
                  onClick={() => window.location.href = `/charts?symbol=${stockDetail.symbol}`}
                  className="flex-1 py-2 bg-terminal-accent text-white rounded-lg hover:opacity-90 transition-opacity text-sm font-medium"
                >
                  View Chart
                </button>
                <button 
                  onClick={() => window.location.href = `/ai?symbol=${stockDetail.symbol}`}
                  className="flex-1 py-2 bg-terminal-bg border border-terminal-border rounded-lg hover:bg-terminal-border transition-colors text-sm font-medium"
                >
                  Ask AI
                </button>
              </div>
            </div>
          </>
        ) : (
          <div className="flex flex-col items-center justify-center h-full text-terminal-muted">
            <ChevronRight size={48} className="mb-4 opacity-50" />
            <p>Select a stock to view details</p>
          </div>
        )}
      </div>
    </div>
  )
}
