import { useState, useEffect, useRef, useCallback } from 'react'
import { Search, Plus, X, ArrowUpDown, Save, Play, Loader2, Trash2, Columns, Filter, ListRestart } from 'lucide-react'
import { builderAPI } from '../../services/api'
import type { ScreenerConfig, ScreenerFilter, FilterOp } from './types'

const FIELD_LABELS: Record<string, string> = {
  symbol: 'Symbol', name: 'Name', sector: 'Sector', industry: 'Industry',
  market_cap_cr: 'Market Cap (Cr)', price: 'Price', volume: 'Volume',
  pe: 'P/E', pb: 'P/B', roe: 'ROE (%)', roce: 'ROCE (%)', eps: 'EPS',
  debt_equity: 'D/E', current_ratio: 'Current Ratio',
  gross_margin: 'Gross Margin (%)', net_margin: 'Net Margin (%)',
  dividend_yield: 'Div Yield (%)', revenue: 'Revenue', profit: 'Profit',
}

const OP_LABELS: Record<FilterOp, string> = {
  eq: '=', neq: '≠', gte: '≥', lte: '≤', gt: '>', lt: '<', contains: 'contains', between: 'between',
}

const ALL_FIELDS = Object.keys(FIELD_LABELS)
const DEFAULT_COLUMNS = ['symbol', 'name', 'sector', 'price', 'pe', 'roe', 'market_cap_cr']
const NUMERIC_FIELDS = new Set(['price', 'volume', 'pe', 'pb', 'roe', 'roce', 'eps', 'debt_equity', 'current_ratio', 'gross_margin', 'net_margin', 'dividend_yield', 'revenue', 'profit', 'market_cap_cr'])

function emptyConfig(): ScreenerConfig {
  return { title: '', filters: [], logic: 'AND', columns: [...DEFAULT_COLUMNS], sort: null, limit: 20 }
}

function formatVal(v: any): string {
  if (v === null || v === undefined) return '—'
  if (typeof v === 'number') return v.toLocaleString()
  return String(v)
}

function formatNum(v: any): string {
  if (v === null || v === undefined) return '—'
  if (typeof v === 'number') return v.toLocaleString(undefined, { maximumFractionDigits: 2 })
  return String(v)
}

interface SavedScreenerItem {
  id: number
  title: string
  config: any
  created_at: string | null
}

export default function ScreenerBuilder() {
  const [config, setConfig] = useState<ScreenerConfig>(emptyConfig)
  const [results, setResults] = useState<any[] | null>(null)
  const [loading, setLoading] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [chatInput, setChatInput] = useState('')
  const [messages, setMessages] = useState<{ role: string; content: string }[]>([
    { role: 'assistant', content: 'Describe the stocks you want to screen for. For example: "Find IT stocks with PE less than 25 and ROE above 15"' },
  ])
  const [savedScreeners, setSavedScreeners] = useState<SavedScreenerItem[]>([])
  const [showSaved, setShowSaved] = useState(false)
  const [saving, setSaving] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  useEffect(() => { fetchSaved() }, [])

  const fetchSaved = async () => {
    try {
      const res = await builderAPI.screener.saved()
      if (res.data.success) setSavedScreeners(res.data.data)
    } catch { /* ignore */ }
  }

  const handleGenerate = useCallback(async (description: string) => {
    if (!description.trim()) return
    setGenerating(true)
    setMessages(prev => [...prev, { role: 'user', content: description }])
    try {
      const res = await builderAPI.screener.generate(description)
      if (res.data.success && res.data.data && !res.data.data.error) {
        const cfg = res.data.data
        setConfig({
          title: cfg.title || '',
          filters: (cfg.filters || []).map((f: any) => ({
            field: f.field,
            op: f.op as FilterOp,
            value: f.value,
          })),
          logic: cfg.logic || 'AND',
          columns: cfg.columns || DEFAULT_COLUMNS,
          sort: cfg.sort_field ? { field: cfg.sort_field, direction: cfg.sort_direction || 'desc' } : null,
          limit: cfg.limit || 20,
        })
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: `Generated screener with ${(cfg.filters || []).length} filter${(cfg.filters || []).length !== 1 ? 's' : ''}. Tweak the settings on the right or type "add a market cap filter" to refine.`,
        }])
        setResults(null)
      } else {
        setMessages(prev => [...prev, { role: 'assistant', content: 'Sorry, I could not generate a screener from that description. Try being more specific.' }])
      }
    } catch {
      setMessages(prev => [...prev, { role: 'assistant', content: 'Connection error. Please try again.' }])
    } finally {
      setGenerating(false)
      setChatInput('')
    }
  }, [])

  const handleRun = useCallback(async () => {
    setLoading(true)
    try {
      const payload = {
        title: config.title,
        filters: config.filters,
        logic: config.logic,
        columns: config.columns,
        sort_field: config.sort?.field || null,
        sort_direction: config.sort?.direction || 'desc',
        limit: config.limit,
      }
      const res = await builderAPI.screener.execute(payload)
      if (res.data.success) {
        setResults(res.data.data)
      }
    } catch { /* ignore */ }
    finally { setLoading(false) }
  }, [config])

  const handleSave = async () => {
    if (!config.title.trim()) {
      const t = config.filters.map(f => `${FIELD_LABELS[f.field] || f.field} ${OP_LABELS[f.op]} ${Array.isArray(f.value) ? f.value.join('-') : f.value}`).join(', ') || 'Untitled'
      setConfig(prev => ({ ...prev, title: t }))
    }
    setSaving(true)
    try {
      const title = config.title.trim() || 'Untitled Screener'
      const payload = {
        title,
        filters: config.filters.map(f => ({ field: f.field, op: f.op, value: f.value })),
        logic: config.logic,
        columns: config.columns,
        sort_field: config.sort?.field || null,
        sort_direction: config.sort?.direction || 'desc',
        limit: config.limit,
      }
      await builderAPI.screener.save(title, payload)
      fetchSaved()
    } catch { /* ignore */ }
    finally { setSaving(false) }
  }

  const handleDelete = async (id: number) => {
    try {
      await builderAPI.screener.delete(id)
      setSavedScreeners(prev => prev.filter(s => s.id !== id))
    } catch { /* ignore */ }
  }

  const loadSaved = (item: SavedScreenerItem) => {
    const cfg = item.config
    setConfig({
      title: cfg.title || item.title,
      filters: (cfg.filters || []).map((f: any) => ({ field: f.field, op: f.op as FilterOp, value: f.value })),
      logic: cfg.logic || 'AND',
      columns: cfg.columns || DEFAULT_COLUMNS,
      sort: cfg.sort_field ? { field: cfg.sort_field, direction: cfg.sort_direction || 'desc' } : null,
      limit: cfg.limit || 20,
    })
    setResults(null)
    setShowSaved(false)
  }

  const addFilter = () => {
    setConfig(prev => ({
      ...prev,
      filters: [...prev.filters, { field: 'sector', op: 'eq', value: '' }],
    }))
  }

  const updateFilter = (idx: number, patch: Partial<ScreenerFilter>) => {
    setConfig(prev => {
      const filters = [...prev.filters]
      filters[idx] = { ...filters[idx], ...patch }
      return { ...prev, filters }
    })
  }

  const removeFilter = (idx: number) => {
    setConfig(prev => ({
      ...prev,
      filters: prev.filters.filter((_, i) => i !== idx),
    }))
  }

  const toggleColumn = (field: string) => {
    setConfig(prev => {
      const cols = prev.columns.includes(field)
        ? prev.columns.filter(c => c !== field)
        : [...prev.columns, field]
      return { ...prev, columns: cols }
    })
  }

  const resetAll = () => {
    setConfig(emptyConfig())
    setResults(null)
    setMessages([{ role: 'assistant', content: 'Describe the stocks you want to screen for.' }])
  }

  const toggleSort = (field: string) => {
    setConfig(prev => {
      if (prev.sort?.field === field) {
        const nextDir = prev.sort.direction === 'desc' ? 'asc' : 'desc'
        return { ...prev, sort: { field, direction: nextDir } }
      }
      return { ...prev, sort: { field, direction: 'desc' } }
    })
  }

  const resultColumns = results && results.length > 0
    ? Object.keys(results[0]).filter(k => config.columns.includes(k))
    : []

  return (
    <div className="flex h-full gap-4">
      {/* Left: Chat Panel */}
      <div className="w-96 flex flex-col bg-terminal-card border border-terminal-border rounded-xl overflow-hidden flex-shrink-0">
        <div className="p-3 border-b border-terminal-border bg-terminal-bg">
          <h3 className="text-sm font-semibold flex items-center gap-2">
            <Filter size={14} className="text-terminal-accent" />
            Screener Assistant
          </h3>
          <p className="text-xs text-terminal-muted mt-0.5">Describe filters in plain English</p>
        </div>
        <div className="flex-1 overflow-auto p-3 space-y-3">
          {messages.map((msg, idx) => (
            <div key={idx} className={`flex gap-2 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
              <div className={`max-w-[85%] rounded-xl px-3 py-2 text-sm ${
                msg.role === 'user'
                  ? 'bg-terminal-accent text-white'
                  : 'bg-terminal-bg border border-terminal-border'
              }`}>
                {msg.content}
              </div>
            </div>
          ))}
          {generating && (
            <div className="flex gap-2">
              <div className="bg-terminal-bg border border-terminal-border rounded-xl px-3 py-2 text-sm flex items-center gap-2 text-terminal-muted">
                <Loader2 size={14} className="animate-spin" />
                Generating...
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
        <form
          onSubmit={(e) => { e.preventDefault(); handleGenerate(chatInput) }}
          className="p-3 border-t border-terminal-border"
        >
          <div className="flex gap-2">
            <input
              type="text"
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              placeholder="Describe stocks to screen..."
              className="flex-1 px-3 py-2 bg-terminal-bg border border-terminal-border rounded-lg text-sm outline-none focus:border-terminal-accent"
              disabled={generating}
            />
            <button
              type="submit"
              disabled={generating || !chatInput.trim()}
              className="px-3 py-2 bg-terminal-accent text-white rounded-lg hover:bg-terminal-accent/90 disabled:opacity-50 transition-colors"
            >
              {generating ? <Loader2 size={16} className="animate-spin" /> : <Search size={16} />}
            </button>
          </div>
        </form>
      </div>

      {/* Right: Builder Panel */}
      <div className="flex-1 flex flex-col gap-4 overflow-auto">
        {/* Top Bar */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3 flex-1 min-w-0">
            <input
              type="text"
              value={config.title}
              onChange={(e) => setConfig(prev => ({ ...prev, title: e.target.value }))}
              placeholder="Screener title..."
              className="bg-transparent border-b border-transparent hover:border-terminal-border focus:border-terminal-accent outline-none text-lg font-semibold px-1 py-0.5 min-w-0 flex-1 transition-colors"
            />
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowSaved(!showSaved)}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-terminal-bg border border-terminal-border rounded-lg text-sm hover:bg-terminal-border transition-colors"
            >
              <ListRestart size={14} />
              Saved
            </button>
            <button
              onClick={resetAll}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-terminal-bg border border-terminal-border rounded-lg text-sm hover:bg-terminal-border transition-colors"
            >
              <X size={14} />
              Reset
            </button>
            <button
              onClick={handleSave}
              disabled={saving}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-terminal-bg border border-terminal-border rounded-lg text-sm hover:bg-terminal-border transition-colors"
            >
              <Save size={14} />
              {saving ? 'Saving...' : 'Save'}
            </button>
            <button
              onClick={handleRun}
              disabled={loading || config.filters.length === 0}
              className="flex items-center gap-1.5 px-4 py-1.5 bg-terminal-accent text-white rounded-lg text-sm hover:bg-terminal-accent/90 disabled:opacity-50 transition-colors"
            >
              {loading ? <Loader2 size={14} className="animate-spin" /> : <Play size={14} />}
              Run
            </button>
          </div>
        </div>

        {/* Filters */}
        <div className="bg-terminal-card border border-terminal-border rounded-xl p-4">
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-sm font-semibold flex items-center gap-2">
              <Filter size={14} className="text-terminal-accent" />
              Filters
            </h4>
            <div className="flex items-center gap-3">
              <label className="flex items-center gap-1.5 text-xs text-terminal-muted">
                <select
                  value={config.logic}
                  onChange={(e) => setConfig(prev => ({ ...prev, logic: e.target.value as 'AND' | 'OR' }))}
                  className="bg-terminal-bg border border-terminal-border rounded px-1.5 py-0.5 text-xs outline-none"
                >
                  <option value="AND">AND</option>
                  <option value="OR">OR</option>
                </select>
              </label>
              <button onClick={addFilter} className="flex items-center gap-1 text-xs text-terminal-accent hover:underline">
                <Plus size={12} /> Add filter
              </button>
            </div>
          </div>
          {config.filters.length === 0 ? (
            <p className="text-sm text-terminal-muted text-center py-6">
              No filters yet. Type a description in the chat panel or click "Add filter"
            </p>
          ) : (
            <div className="space-y-2">
              {config.filters.map((filter, idx) => (
                <div key={idx} className="flex items-center gap-2 bg-terminal-bg border border-terminal-border rounded-lg p-2">
                  <select
                    value={filter.field}
                    onChange={(e) => updateFilter(idx, { field: e.target.value })}
                    className="bg-terminal-card border border-terminal-border rounded px-2 py-1 text-sm outline-none min-w-[130px]"
                  >
                    {ALL_FIELDS.map(f => (
                      <option key={f} value={f}>{FIELD_LABELS[f] || f}</option>
                    ))}
                  </select>
                  <select
                    value={filter.op}
                    onChange={(e) => updateFilter(idx, { op: e.target.value as FilterOp })}
                    className="bg-terminal-card border border-terminal-border rounded px-2 py-1 text-sm outline-none"
                  >
                    {Object.entries(OP_LABELS).map(([k, v]) => (
                      <option key={k} value={k}>{v}</option>
                    ))}
                  </select>
                  {filter.op === 'between' ? (
                    <div className="flex items-center gap-1">
                      <input
                        type="number"
                        placeholder="Min"
                        value={Array.isArray(filter.value) ? filter.value[0] : ''}
                        onChange={(e) => updateFilter(idx, { value: [parseFloat(e.target.value) || 0, Array.isArray(filter.value) ? filter.value[1] : 0] })}
                        className="w-20 bg-terminal-card border border-terminal-border rounded px-2 py-1 text-sm outline-none"
                      />
                      <span className="text-terminal-muted text-xs">to</span>
                      <input
                        type="number"
                        placeholder="Max"
                        value={Array.isArray(filter.value) ? filter.value[1] : ''}
                        onChange={(e) => updateFilter(idx, { value: [Array.isArray(filter.value) ? filter.value[0] : 0, parseFloat(e.target.value) || 0] })}
                        className="w-20 bg-terminal-card border border-terminal-border rounded px-2 py-1 text-sm outline-none"
                      />
                    </div>
                  ) : filter.op === 'contains' ? (
                    <input
                      type="text"
                      placeholder="Search text..."
                      value={typeof filter.value === 'string' ? filter.value : ''}
                      onChange={(e) => updateFilter(idx, { value: e.target.value })}
                      className="flex-1 bg-terminal-card border border-terminal-border rounded px-2 py-1 text-sm outline-none"
                    />
                  ) : (
                    <input
                      type={NUMERIC_FIELDS.has(filter.field) ? 'number' : 'text'}
                      placeholder={NUMERIC_FIELDS.has(filter.field) ? '0' : 'value'}
                      value={typeof filter.value === 'string' && !NUMERIC_FIELDS.has(filter.field) ? filter.value : ''}
                      onChange={(e) => {
                        const val = NUMERIC_FIELDS.has(filter.field) ? parseFloat(e.target.value) || 0 : e.target.value
                        updateFilter(idx, { value: val })
                      }}
                      className="flex-1 bg-terminal-card border border-terminal-border rounded px-2 py-1 text-sm outline-none"
                    />
                  )}
                  <button onClick={() => removeFilter(idx)} className="p-1 hover:text-red-400 transition-colors">
                    <X size={14} />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Columns + Sort + Limit */}
        <div className="bg-terminal-card border border-terminal-border rounded-xl p-4">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-4">
              <h4 className="text-sm font-semibold flex items-center gap-2">
                <Columns size={14} className="text-terminal-accent" />
                Columns
              </h4>
              <h4 className="text-sm font-semibold flex items-center gap-2">
                <ArrowUpDown size={14} className="text-terminal-accent" />
                Sort
              </h4>
            </div>
            <div className="flex items-center gap-2 text-sm text-terminal-muted">
              <span>Limit:</span>
              <input
                type="number"
                value={config.limit}
                onChange={(e) => setConfig(prev => ({ ...prev, limit: Math.max(1, Math.min(200, parseInt(e.target.value) || 20)) }))}
                className="w-16 bg-terminal-bg border border-terminal-border rounded px-2 py-1 text-sm outline-none text-center"
                min={1}
                max={200}
              />
            </div>
          </div>
          <div className="flex items-center gap-2 flex-wrap">
            {ALL_FIELDS.slice(0, 18).map(field => (
              <button
                key={field}
                onClick={() => toggleColumn(field)}
                className={`px-2.5 py-1 rounded-lg text-xs border transition-colors ${
                  config.columns.includes(field)
                    ? 'bg-terminal-accent/20 border-terminal-accent/40 text-terminal-accent'
                    : 'bg-terminal-bg border-terminal-border text-terminal-muted hover:text-white'
                }`}
              >
                {FIELD_LABELS[field] || field}
                {config.sort?.field === field && (
                  <span className="ml-1 text-[10px]">{config.sort.direction === 'asc' ? '↑' : '↓'}</span>
                )}
              </button>
            ))}
          </div>
          <div className="mt-3 flex items-center gap-2 flex-wrap">
            {ALL_FIELDS.slice(0, 18).map(field => (
              <button
                key={field}
                onClick={() => toggleSort(field)}
                className={`px-2.5 py-1 rounded-lg text-xs border transition-colors ${
                  config.sort?.field === field
                    ? 'bg-orange-500/20 border-orange-500/40 text-orange-400'
                    : 'bg-terminal-bg border-terminal-border text-terminal-muted hover:text-white'
                }`}
              >
                {FIELD_LABELS[field] || field} sort
              </button>
            ))}
          </div>
        </div>

        {/* Saved Screeners */}
        {showSaved && (
          <div className="bg-terminal-card border border-terminal-border rounded-xl p-4">
            <h4 className="text-sm font-semibold mb-3">Saved Screeners</h4>
            {savedScreeners.length === 0 ? (
              <p className="text-sm text-terminal-muted">No saved screeners yet</p>
            ) : (
              <div className="space-y-2">
                {savedScreeners.map(item => (
                  <div key={item.id} className="flex items-center justify-between bg-terminal-bg border border-terminal-border rounded-lg p-2">
                    <div className="flex-1 min-w-0">
                      <div className="text-sm truncate">{item.title}</div>
                      <div className="text-xs text-terminal-muted">{(item.config?.filters || []).length} filters</div>
                    </div>
                    <div className="flex items-center gap-2">
                      <button onClick={() => loadSaved(item)} className="text-xs text-terminal-accent hover:underline">Load</button>
                      <button onClick={() => handleDelete(item.id)} className="p-1 hover:text-red-400"><Trash2 size={12} /></button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Results Table */}
        {loading && (
          <div className="flex items-center justify-center py-12">
            <Loader2 size={24} className="animate-spin text-terminal-muted" />
          </div>
        )}
        {results !== null && !loading && (
          <div className="bg-terminal-card border border-terminal-border rounded-xl overflow-hidden">
            <div className="p-3 border-b border-terminal-border flex items-center justify-between">
              <h4 className="text-sm font-semibold">
                Results
                <span className="text-terminal-muted font-normal ml-2">({results.length} stocks)</span>
              </h4>
            </div>
            {results.length === 0 ? (
              <div className="p-8 text-center text-terminal-muted text-sm">No stocks match your filters</div>
            ) : (
              <div className="overflow-auto max-h-96">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="bg-terminal-bg border-b border-terminal-border">
                      {resultColumns.map(col => (
                        <th
                          key={col}
                          onClick={() => toggleSort(col)}
                          className={`px-3 py-2 text-left text-xs font-medium text-terminal-muted cursor-pointer hover:text-white whitespace-nowrap ${
                            config.sort?.field === col ? 'text-terminal-accent' : ''
                          }`}
                        >
                          {FIELD_LABELS[col] || col}
                          {config.sort?.field === col && (
                            <span className="ml-1">{config.sort.direction === 'asc' ? '↑' : '↓'}</span>
                          )}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-terminal-border">
                    {results.map((row, idx) => (
                      <tr key={idx} className="hover:bg-terminal-border/50 transition-colors">
                        {resultColumns.map(col => (
                          <td key={col} className="px-3 py-2 whitespace-nowrap">
                            {col === 'symbol' ? (
                              <span className="font-mono font-medium">{row[col]}</span>
                            ) : col === 'price' || col === 'market_cap_cr' ? (
                              <span className="font-mono">
                                {col === 'market_cap_cr' ? '₹' : '₹'}{formatNum(row[col])}
                              </span>
                            ) : col === 'pe' || col === 'pb' || col === 'debt_equity' ? (
                              <span className="font-mono">{formatNum(row[col])}</span>
                            ) : col === 'roe' || col === 'net_margin' || col === 'gross_margin' ? (
                              <span className="font-mono">{formatNum(row[col])}%</span>
                            ) : (
                              <span>{formatVal(row[col])}</span>
                            )}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
