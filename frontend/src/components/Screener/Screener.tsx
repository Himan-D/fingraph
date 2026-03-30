import { useState, useEffect } from 'react'
import axios from 'axios'
import { Filter, SlidersHorizontal, ArrowUpDown, Play, Save, Download, Star } from 'lucide-react'

interface ScreenerResult {
  symbol: string
  name: string
  sector: string
  industry: string
  price: number
  change: number
  pct_change: number
  volume: number
  market_cap: number
  pe_ratio: number
  roe: number
  debt_equity: number
  dividend_yield: number
}

interface Template {
  id: number
  name: string
  description: string
  filters: Record<string, any>
}

interface FilterState {
  market_cap_min: number | null
  market_cap_max: number | null
  pe_min: number | null
  pe_max: number | null
  roe_min: number | null
  debt_equity_max: number | null
  dividend_yield_min: number | null
  sector: string
}

export default function Screener() {
  const [results, setResults] = useState<ScreenerResult[]>([])
  const [loading, setLoading] = useState(false)
  const [showFilters, setShowFilters] = useState(true)
  const [sortBy, setSortBy] = useState('market_cap')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')
  const [templates, setTemplates] = useState<Template[]>([])
  const [activeTab, setActiveTab] = useState<'custom' | 'templates'>('templates')
  const [filters, setFilters] = useState<FilterState>({
    market_cap_min: null,
    market_cap_max: null,
    pe_min: null,
    pe_max: null,
    roe_min: null,
    debt_equity_max: null,
    dividend_yield_min: null,
    sector: '',
  })

  useEffect(() => {
    fetchTemplates()
    runScreener()
  }, [])

  const fetchTemplates = async () => {
    try {
      const response = await axios.get('/api/v1/screen/templates')
      if (response.data.success) {
        setTemplates(response.data.data)
      }
    } catch (error) {
      console.error('Failed to fetch templates:', error)
    }
  }

  const runScreener = async () => {
    setLoading(true)
    try {
      const params: Record<string, any> = {
        sort_by: sortBy,
        sort_order: sortOrder,
        limit: 50,
      }
      
      if (filters.market_cap_min) params.market_cap_min = filters.market_cap_min * 10000000
      if (filters.market_cap_max) params.market_cap_max = filters.market_cap_max * 10000000
      if (filters.pe_min) params.pe_min = filters.pe_min
      if (filters.pe_max) params.pe_max = filters.pe_max
      if (filters.roe_min) params.roe_min = filters.roe_min
      if (filters.debt_equity_max) params.debt_equity_max = filters.debt_equity_max
      if (filters.dividend_yield_min) params.dividend_yield_min = filters.dividend_yield_min
      if (filters.sector) params.sector = filters.sector

      const response = await axios.get('/api/v1/screen/run', { params })
      if (response.data.success) {
        setResults(response.data.data || [])
      }
    } catch (error) {
      console.error('Screener failed:', error)
    } finally {
      setLoading(false)
    }
  }

  const applyTemplate = (template: Template) => {
    const newFilters: FilterState = { ...filters }
    Object.entries(template.filters).forEach(([key, value]) => {
      if (key in newFilters && value !== undefined) {
        (newFilters as any)[key] = value
      }
    })
    setFilters(newFilters)
    setTimeout(runScreener, 100)
  }

  const formatMarketCap = (value: number) => {
    if (!value) return '-'
    const cr = value / 10000000
    if (cr >= 100000) return `${(cr / 100000).toFixed(1)}L Cr`
    if (cr >= 1000) return `${(cr / 1000).toFixed(1)}K Cr`
    return `${cr.toFixed(1)} Cr`
  }

  const formatVolume = (value: number) => {
    if (!value) return '-'
    if (value >= 10000000) return `${(value / 10000000).toFixed(1)}Cr`
    if (value >= 100000) return `${(value / 100000).toFixed(1)}L`
    if (value >= 1000) return `${(value / 1000).toFixed(1)}K`
    return value.toString()
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-terminal-border bg-terminal-card">
        <div className="flex items-center gap-3">
          <Filter size={20} className="text-terminal-accent" />
          <h2 className="font-semibold">Stock Screener</h2>
          <span className="text-sm text-terminal-muted">({results.length} stocks)</span>
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
          <button className="flex items-center gap-2 px-3 py-1.5 bg-terminal-border rounded-lg text-sm hover:bg-terminal-border/80">
            <Save size={16} />
            Save
          </button>
          <button className="flex items-center gap-2 px-3 py-1.5 bg-terminal-border rounded-lg text-sm hover:bg-terminal-border/80">
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
                {templates.map((template) => (
                  <button
                    key={template.id}
                    onClick={() => applyTemplate(template)}
                    className="w-full text-left p-3 bg-terminal-bg rounded-lg hover:bg-terminal-border transition-colors"
                  >
                    <div className="flex items-center gap-2">
                      <Star size={14} className="text-terminal-warning" />
                      <span className="font-medium text-sm">{template.name}</span>
                    </div>
                    <p className="text-xs text-terminal-muted mt-1">{template.description}</p>
                  </button>
                ))}
              </div>
            ) : (
              <div className="space-y-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Market Cap (Cr)</label>
                  <div className="flex gap-2">
                    <input
                      type="number"
                      placeholder="Min"
                      value={filters.market_cap_min || ''}
                      onChange={(e) => setFilters({...filters, market_cap_min: e.target.value ? Number(e.target.value) : null})}
                      className="w-full px-3 py-2 bg-terminal-bg border border-terminal-border rounded text-sm"
                    />
                    <input
                      type="number"
                      placeholder="Max"
                      value={filters.market_cap_max || ''}
                      onChange={(e) => setFilters({...filters, market_cap_max: e.target.value ? Number(e.target.value) : null})}
                      className="w-full px-3 py-2 bg-terminal-bg border border-terminal-border rounded text-sm"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">P/E Ratio</label>
                  <div className="flex gap-2">
                    <input
                      type="number"
                      placeholder="Min"
                      value={filters.pe_min || ''}
                      onChange={(e) => setFilters({...filters, pe_min: e.target.value ? Number(e.target.value) : null})}
                      className="w-full px-3 py-2 bg-terminal-bg border border-terminal-border rounded text-sm"
                    />
                    <input
                      type="number"
                      placeholder="Max"
                      value={filters.pe_max || ''}
                      onChange={(e) => setFilters({...filters, pe_max: e.target.value ? Number(e.target.value) : null})}
                      className="w-full px-3 py-2 bg-terminal-bg border border-terminal-border rounded text-sm"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">ROE (%)</label>
                  <input
                    type="number"
                    placeholder="Minimum ROE"
                    value={filters.roe_min || ''}
                    onChange={(e) => setFilters({...filters, roe_min: e.target.value ? Number(e.target.value) : null})}
                    className="w-full px-3 py-2 bg-terminal-bg border border-terminal-border rounded text-sm"
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">Sector</label>
                  <select
                    value={filters.sector}
                    onChange={(e) => setFilters({...filters, sector: e.target.value})}
                    className="w-full px-3 py-2 bg-terminal-bg border border-terminal-border rounded text-sm"
                  >
                    <option value="">All Sectors</option>
                    <option value="Technology">Technology</option>
                    <option value="Financial Services">Financial Services</option>
                    <option value="Energy">Energy</option>
                    <option value="Automobile">Automobile</option>
                    <option value="Healthcare">Healthcare</option>
                    <option value="FMCG">FMCG</option>
                  </select>
                </div>

                <button
                  onClick={runScreener}
                  disabled={loading}
                  className="w-full py-2 bg-terminal-accent text-white rounded-lg hover:bg-terminal-accent/90 disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  {loading ? 'Loading...' : (
                    <>
                      <Play size={16} />
                      Apply Filters
                    </>
                  )}
                </button>

                <button
                  onClick={() => setFilters({
                    market_cap_min: null,
                    market_cap_max: null,
                    pe_min: null,
                    pe_max: null,
                    roe_min: null,
                    debt_equity_max: null,
                    dividend_yield_min: null,
                    sector: '',
                  })}
                  className="w-full py-2 bg-terminal-bg border border-terminal-border rounded-lg hover:bg-terminal-border text-sm"
                >
                  Clear Filters
                </button>
              </div>
            )}
          </div>
        )}

        {/* Results Table */}
        <div className="flex-1 overflow-auto">
          <div className="p-4">
            {/* Sort Controls */}
            <div className="flex items-center gap-2 mb-4">
              <span className="text-sm text-terminal-muted">Sort by:</span>
              <select
                value={sortBy}
                onChange={(e) => { setSortBy(e.target.value); setTimeout(runScreener, 100) }}
                className="px-3 py-1 bg-terminal-bg border border-terminal-border rounded text-sm"
              >
                <option value="market_cap">Market Cap</option>
                <option value="price">Price</option>
                <option value="pct_change">Change %</option>
                <option value="volume">Volume</option>
                <option value="pe_ratio">P/E Ratio</option>
                <option value="roe">ROE</option>
              </select>
              <button
                onClick={() => { setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc'); setTimeout(runScreener, 100) }}
                className="p-1 hover:bg-terminal-border rounded"
              >
                <ArrowUpDown size={16} className={sortOrder === 'asc' ? 'rotate-180' : ''} />
              </button>
            </div>

            {/* Table */}
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
                    <th className="p-3 font-medium">D/E</th>
                    <th className="p-3 font-medium">Sector</th>
                  </tr>
                </thead>
                <tbody>
                  {results.map((stock) => (
                    <tr
                      key={stock.symbol}
                      onClick={() => window.location.href = `/charts?symbol=${stock.symbol}`}
                      className="border-t border-terminal-border cursor-pointer hover:bg-terminal-border transition-colors"
                    >
                      <td className="p-3">
                        <div className="font-medium">{stock.symbol}</div>
                        <div className="text-xs text-terminal-muted truncate max-w-[120px]">{stock.name}</div>
                      </td>
                      <td className="p-3 font-mono">₹{stock.price?.toLocaleString()}</td>
                      <td className={`p-3 font-mono ${stock.pct_change >= 0 ? 'text-terminal-success' : 'text-terminal-danger'}`}>
                        {stock.pct_change >= 0 ? '+' : ''}{stock.pct_change?.toFixed(2)}%
                      </td>
                      <td className="p-3 font-mono text-sm">{formatVolume(stock.volume)}</td>
                      <td className="p-3 font-mono text-sm">{formatMarketCap(stock.market_cap)}</td>
                      <td className="p-3 font-mono text-sm">{stock.pe_ratio?.toFixed(1) || '-'}</td>
                      <td className={`p-3 font-mono text-sm ${stock.roe >= 15 ? 'text-terminal-success' : ''}`}>
                        {stock.roe?.toFixed(1) || '-'}%
                      </td>
                      <td className={`p-3 font-mono text-sm ${stock.debt_equity > 1 ? 'text-terminal-danger' : ''}`}>
                        {stock.debt_equity?.toFixed(2) || '-'}
                      </td>
                      <td className="p-3 text-sm text-terminal-muted">{stock.sector}</td>
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
