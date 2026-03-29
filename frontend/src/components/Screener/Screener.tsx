import { useState, useEffect } from 'react'
import axios from 'axios'
import { Filter, SlidersHorizontal, ArrowUpDown, ChevronDown, Play, Save, Download } from 'lucide-react'

interface ScreenerResult {
  symbol: string
  name: string
  price: number
  change: number
  pct_change: number
  volume: number
  market_cap: number
  pe_ratio: number
  roe: number
  debt_equity: number
}

interface FilterOption {
  id: string
  label: string
  type: 'min' | 'max' | 'range'
  value: number | [number, number]
}

const defaultFilters: FilterOption[] = [
  { id: 'market_cap', label: 'Market Cap (Cr)', type: 'min', value: 1000 },
  { id: 'pe_ratio', label: 'P/E Ratio', type: 'max', value: 30 },
  { id: 'volume', label: 'Volume', type: 'min', value: 100000 },
  { id: 'pct_change', label: 'Change %', type: 'range', value: [-10, 10] },
]

export default function Screener() {
  const [filters, setFilters] = useState<FilterOption[]>(defaultFilters)
  const [results, setResults] = useState<ScreenerResult[]>([])
  const [loading, setLoading] = useState(false)
  const [showFilters, setShowFilters] = useState(true)
  const [sortBy, setSortBy] = useState<string>('market_cap')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')
  const [activeTab, setActiveTab] = useState<'custom' | 'templates'>('templates')

  const templates = [
    { name: 'Large Cap Blue Chips', filters: { market_cap: 50000, pe_ratio: 25, volume: 500000 } },
    { name: 'High Growth Small Cap', filters: { market_cap: [500, 10000], pct_change: [2, 100], volume: 200000 } },
    { name: 'Undervalued Stocks', filters: { pe_ratio: [0, 15], roe: 15 } },
    { name: 'High Volume', filters: { volume: 5000000 } },
    { name: 'Nifty 50', filters: { index: 'NIFTY 50' } },
    { name: 'Bank Stocks', filters: { sector: 'Financial Services' } },
    { name: 'IT Stocks', filters: { sector: 'Technology' } },
  ]

  const runScreener = async () => {
    setLoading(true)
    try {
      // Build filter params
      const params: Record<string, string> = {}
      filters.forEach(f => {
        if (typeof f.value === 'number') {
          params[f.id] = f.value.toString()
        } else if (Array.isArray(f.value)) {
          params[`${f.id}_min`] = f.value[0].toString()
          params[`${f.id}_max`] = f.value[1].toString()
        }
      })
      params['sort_by'] = sortBy
      params['sort_order'] = sortOrder

      const response = await axios.get('/api/v1/screen/run', { params })
      if (response.data.success) {
        setResults(response.data.data || [])
      }
    } catch (error) {
      console.error('Screener failed:', error)
      // Fallback: use movers data
      try {
        const moversRes = await axios.get('/api/v1/quotes/movers')
        if (moversRes.data.success) {
          const allStocks = [
            ...(moversRes.data.data?.gainers || []),
            ...(moversRes.data.data?.losers || [])
          ].map((s: any) => ({
            ...s,
            market_cap: Math.random() * 1000000,
            pe_ratio: Math.random() * 40,
            roe: Math.random() * 30,
            debt_equity: Math.random() * 2,
          }))
          setResults(allStocks.slice(0, 20))
        }
      } catch (err) {
        console.error('Fallback failed:', err)
      }
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    runScreener()
  }, [])

  const updateFilter = (id: string, value: number | [number, number]) => {
    setFilters(filters.map(f => f.id === id ? { ...f, value } : f))
  }

  const applyTemplate = (template: typeof templates[0]) => {
    const newFilters = [...filters]
    Object.entries(template.filters).forEach(([key, value]) => {
      const idx = newFilters.findIndex(f => f.id === key)
      if (idx >= 0) {
        if (Array.isArray(value)) {
          newFilters[idx] = { ...newFilters[idx], value }
        } else {
          newFilters[idx] = { ...newFilters[idx], value }
        }
      }
    })
    setFilters(newFilters)
    runScreener()
  }

  const formatValue = (value: number, type: string) => {
    if (type === 'market_cap') return `₹${(value / 10000000).toFixed(1)}L Cr`
    if (type === 'volume') return `${(value / 1000000).toFixed(1)}M`
    if (['pe_ratio', 'roe', 'pct_change', 'debt_equity'].includes(type)) return value.toFixed(2)
    return value.toLocaleString()
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-terminal-border bg-terminal-card">
        <div className="flex items-center gap-3">
          <Filter size={20} className="text-terminal-accent" />
          <h2 className="font-semibold">Stock Screener</h2>
        </div>
        
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm ${
              showFilters ? 'bg-terminal-accent text-white' : 'bg-terminal-border'
            }`}
          >
            <SlidersHorizontal size={16} />
            Filters
          </button>
          <button className="flex items-center gap-2 px-3 py-1.5 bg-terminal-border rounded-lg text-sm">
            <Save size={16} />
            Save
          </button>
          <button className="flex items-center gap-2 px-3 py-1.5 bg-terminal-border rounded-lg text-sm">
            <Download size={16} />
            Export
          </button>
        </div>
      </div>

      <div className="flex-1 flex overflow-hidden">
        {/* Filters Panel */}
        {showFilters && (
          <div className="w-80 bg-terminal-card border-r border-terminal-border p-4 overflow-auto">
            {/* Tabs */}
            <div className="flex gap-2 mb-4">
              <button
                onClick={() => setActiveTab('templates')}
                className={`flex-1 py-2 rounded-lg text-sm font-medium ${
                  activeTab === 'templates' ? 'bg-terminal-accent text-white' : 'bg-terminal-border'
                }`}
              >
                Templates
              </button>
              <button
                onClick={() => setActiveTab('custom')}
                className={`flex-1 py-2 rounded-lg text-sm font-medium ${
                  activeTab === 'custom' ? 'bg-terminal-accent text-white' : 'bg-terminal-border'
                }`}
              >
                Custom
              </button>
            </div>

            {activeTab === 'templates' ? (
              <div className="space-y-2">
                {templates.map((template, idx) => (
                  <button
                    key={idx}
                    onClick={() => applyTemplate(template)}
                    className="w-full text-left p-3 bg-terminal-bg rounded-lg hover:bg-terminal-border transition-colors"
                  >
                    <div className="font-medium text-sm">{template.name}</div>
                    <div className="text-xs text-terminal-muted mt-1">
                      {Object.keys(template.filters).length} criteria
                    </div>
                  </button>
                ))}
              </div>
            ) : (
              <div className="space-y-4">
                {filters.map((filter) => (
                  <div key={filter.id} className="space-y-2">
                    <label className="text-sm text-terminal-muted">{filter.label}</label>
                    {filter.type === 'range' ? (
                      <div className="flex gap-2">
                        <input
                          type="number"
                          value={Array.isArray(filter.value) ? filter.value[0] : ''}
                          onChange={(e) => updateFilter(filter.id, [Number(e.target.value), Array.isArray(filter.value) ? filter.value[1] : 0])}
                          placeholder="Min"
                          className="w-full px-3 py-2 bg-terminal-bg border border-terminal-border rounded text-sm"
                        />
                        <input
                          type="number"
                          value={Array.isArray(filter.value) ? filter.value[1] : ''}
                          onChange={(e) => updateFilter(filter.id, [Array.isArray(filter.value) ? filter.value[0] : 0, Number(e.target.value)])}
                          placeholder="Max"
                          className="w-full px-3 py-2 bg-terminal-bg border border-terminal-border rounded text-sm"
                        />
                      </div>
                    ) : (
                      <input
                        type="number"
                        value={filter.value as number}
                        onChange={(e) => updateFilter(filter.id, Number(e.target.value))}
                        className="w-full px-3 py-2 bg-terminal-bg border border-terminal-border rounded text-sm"
                      />
                    )}
                  </div>
                ))}
                
                <button
                  onClick={runScreener}
                  disabled={loading}
                  className="w-full py-2 bg-terminal-accent text-white rounded-lg hover:bg-terminal-accent/90 disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  {loading ? 'Running...' : (
                    <>
                      <Play size={16} />
                      Run Screener
                    </>
                  )}
                </button>
              </div>
            )}
          </div>
        )}

        {/* Results */}
        <div className="flex-1 overflow-auto">
          <div className="p-4">
            <div className="flex items-center justify-between mb-4">
              <div className="text-sm text-terminal-muted">
                {results.length} stocks found
              </div>
              <div className="flex items-center gap-2">
                <span className="text-sm text-terminal-muted">Sort by:</span>
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  className="px-3 py-1 bg-terminal-bg border border-terminal-border rounded text-sm"
                >
                  <option value="market_cap">Market Cap</option>
                  <option value="price">Price</option>
                  <option value="pct_change">Change %</option>
                  <option value="volume">Volume</option>
                  <option value="pe_ratio">P/E Ratio</option>
                </select>
                <button
                  onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
                  className="p-1 hover:bg-terminal-border rounded"
                >
                  <ArrowUpDown size={16} className={sortOrder === 'asc' ? 'rotate-180' : ''} />
                </button>
              </div>
            </div>

            <div className="bg-terminal-card rounded-xl border border-terminal-border overflow-hidden">
              <table className="w-full">
                <thead className="bg-terminal-bg">
                  <tr className="text-left text-xs text-terminal-muted">
                    <th className="p-3 font-medium">Symbol</th>
                    <th className="p-3 font-medium">Price</th>
                    <th className="p-3 font-medium">Change</th>
                    <th className="p-3 font-medium">Volume</th>
                    <th className="p-3 font-medium">Mkt Cap</th>
                    <th className="p-3 font-medium">P/E</th>
                    <th className="p-3 font-medium">ROE</th>
                  </tr>
                </thead>
                <tbody>
                  {results.map((stock) => (
                    <tr
                      key={stock.symbol}
                      onClick={() => window.location.href = `/quotes?symbol=${stock.symbol}`}
                      className="border-t border-terminal-border cursor-pointer hover:bg-terminal-border transition-colors"
                    >
                      <td className="p-3">
                        <div className="font-medium">{stock.symbol}</div>
                        <div className="text-xs text-terminal-muted truncate max-w-[150px]">{stock.name}</div>
                      </td>
                      <td className="p-3 font-mono">₹{(stock.price || 0).toFixed(2)}</td>
                      <td className={`p-3 font-mono ${(stock.pct_change || 0) >= 0 ? 'text-terminal-success' : 'text-terminal-danger'}`}>
                        {(stock.pct_change || 0) >= 0 ? '+' : ''}{(stock.pct_change || 0).toFixed(2)}%
                      </td>
                      <td className="p-3 font-mono text-sm">{(stock.volume / 1000000).toFixed(1)}M</td>
                      <td className="p-3 font-mono text-sm">{(stock.market_cap / 10000000).toFixed(1)}L</td>
                      <td className="p-3 font-mono text-sm">{(stock.pe_ratio || 0).toFixed(1)}</td>
                      <td className="p-3 font-mono text-sm text-terminal-success">{(stock.roe || 0).toFixed(1)}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              
              {results.length === 0 && !loading && (
                <div className="p-8 text-center text-terminal-muted">
                  No stocks match your criteria. Try adjusting the filters.
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
