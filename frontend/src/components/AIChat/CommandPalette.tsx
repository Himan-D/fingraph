import { useState, useEffect, useRef, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search, MessageSquare, TrendingUp, Filter, Share2, LineChart, Brain, Network, Bell, Layers, Zap, Command, ArrowRight } from 'lucide-react'

interface Command {
  id: string
  label: string
  description: string
  icon: React.ReactNode
  action: () => void
  shortcut?: string
  category: string
}

export default function CommandPalette() {
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [selectedIndex, setSelectedIndex] = useState(0)
  const inputRef = useRef<HTMLInputElement>(null)
  const navigate = useNavigate()

  const commands: Command[] = [
    { id: 'ai', label: 'AI Assistant', description: 'Ask anything about Indian markets', icon: <MessageSquare size={16} />, action: () => navigate('/ai'), shortcut: 'Alt+A', category: 'Navigate' },
    { id: 'dashboard', label: 'Dashboard', description: 'Market overview and indices', icon: <TrendingUp size={16} />, action: () => navigate('/'), shortcut: 'Alt+D', category: 'Navigate' },
    { id: 'quotes', label: 'Quotes', description: 'Stock quotes and prices', icon: <TrendingUp size={16} />, action: () => navigate('/quotes'), shortcut: 'Alt+Q', category: 'Navigate' },
    { id: 'screener', label: 'Screener', description: 'Filter stocks by fundamentals', icon: <Filter size={16} />, action: () => navigate('/screener'), shortcut: 'Alt+S', category: 'Navigate' },
    { id: 'charts', label: 'Charts', description: 'Advanced charting with indicators', icon: <LineChart size={16} />, action: () => navigate('/charts'), shortcut: 'Alt+C', category: 'Navigate' },
    { id: 'graph', label: 'Knowledge Graph', description: 'Explore company relationships', icon: <Share2 size={16} />, action: () => navigate('/graph'), shortcut: 'Alt+G', category: 'Navigate' },
    { id: 'gds', label: 'GDS Analytics', description: 'Advanced graph analytics', icon: <Network size={16} />, action: () => navigate('/gds'), category: 'Navigate' },
    { id: 'risk', label: 'Risk Engine', description: 'Monte Carlo, VaR, stress tests', icon: <Brain size={16} />, action: () => navigate('/risk'), shortcut: 'Alt+R', category: 'Navigate' },
    { id: 'options', label: 'Option Chain', description: 'F&O chain with OI/volume', icon: <Layers size={16} />, action: () => navigate('/options'), category: 'Navigate' },
    { id: 'news', label: 'News', description: 'Market news and headlines', icon: <Bell size={16} />, action: () => navigate('/news'), shortcut: 'Alt+N', category: 'Navigate' },

    { id: 'ask-reliance', label: 'Ask AI: Analyze RELIANCE', description: 'Get fundamentals and analysis for Reliance', icon: <Zap size={16} />, action: () => { navigate('/ai'); setTimeout(() => window.dispatchEvent(new CustomEvent('ai-query', { detail: 'Analyze RELIANCE fundamentals' })), 100) }, category: 'Quick Actions' },
    { id: 'ask-comparison', label: 'Ask AI: Compare TCS vs INFY', description: 'Side-by-side comparison of TCS and Infosys', icon: <Zap size={16} />, action: () => { navigate('/ai'); setTimeout(() => window.dispatchEvent(new CustomEvent('ai-query', { detail: 'Compare TCS vs INFY' })), 100) }, category: 'Quick Actions' },
    { id: 'ask-screener', label: 'Ask AI: PE < 20, ROE > 15', description: 'Screen for value stocks', icon: <Zap size={16} />, action: () => { navigate('/ai'); setTimeout(() => window.dispatchEvent(new CustomEvent('ai-query', { detail: 'Screen stocks with PE < 20 and ROE > 15' })), 100) }, category: 'Quick Actions' },
    { id: 'ask-risk', label: 'Ask AI: Risk analysis ICICI', description: 'Run risk models for ICICI Bank', icon: <Zap size={16} />, action: () => { navigate('/ai'); setTimeout(() => window.dispatchEvent(new CustomEvent('ai-query', { detail: 'Run risk analysis for ICICIBANK' })), 100) }, category: 'Quick Actions' },
  ]

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        setOpen(prev => !prev)
        setQuery('')
        setSelectedIndex(0)
      }
      if (e.key === 'Escape') {
        setOpen(false)
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [])

  useEffect(() => {
    if (open) {
      setTimeout(() => inputRef.current?.focus(), 50)
    }
  }, [open])

  const filtered = query.trim()
    ? commands.filter(c =>
        c.label.toLowerCase().includes(query.toLowerCase()) ||
        c.description.toLowerCase().includes(query.toLowerCase())
      )
    : commands

  const handleSelect = useCallback((cmd: Command) => {
    cmd.action()
    setOpen(false)
    setQuery('')
  }, [])

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setSelectedIndex(i => Math.min(i + 1, filtered.length - 1))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setSelectedIndex(i => Math.max(i - 1, 0))
    } else if (e.key === 'Enter' && filtered[selectedIndex]) {
      handleSelect(filtered[selectedIndex])
    }
  }

  if (!open) return null

  const grouped = filtered.reduce((acc, cmd) => {
    if (!acc[cmd.category]) acc[cmd.category] = []
    acc[cmd.category].push(cmd)
    return acc
  }, {} as Record<string, Command[]>)

  return (
    <div className="fixed inset-0 z-[100] flex items-start justify-center pt-[15vh]" onClick={() => setOpen(false)}>
      <div className="fixed inset-0 bg-black/60 backdrop-blur-sm" />
      <div
        className="relative w-full max-w-xl bg-terminal-card border border-terminal-border rounded-xl shadow-2xl overflow-hidden"
        onClick={e => e.stopPropagation()}
      >
        <div className="flex items-center gap-3 p-4 border-b border-terminal-border">
          <Search size={18} className="text-terminal-muted" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={e => { setQuery(e.target.value); setSelectedIndex(0) }}
            onKeyDown={handleKeyDown}
            placeholder="Search commands, stocks, or actions..."
            className="flex-1 bg-transparent outline-none text-sm placeholder:text-terminal-muted"
            autoComplete="off"
            spellCheck={false}
          />
          <kbd className="hidden sm:inline-flex items-center gap-1 px-1.5 py-0.5 bg-terminal-bg border border-terminal-border rounded text-[10px] text-terminal-muted">
            <Command size={10} />
            K
          </kbd>
        </div>

        <div className="max-h-80 overflow-y-auto p-2">
          {Object.entries(grouped).map(([category, cmds]) => (
            <div key={category}>
              <div className="px-2 py-1.5 text-[10px] uppercase tracking-wider text-terminal-muted font-semibold">
                {category}
              </div>
              {cmds.map(cmd => {
                const globalIdx = filtered.indexOf(cmd)
                return (
                  <div
                    key={cmd.id}
                    onClick={() => handleSelect(cmd)}
                    className={`flex items-center gap-3 px-3 py-2.5 rounded-lg cursor-pointer transition-colors ${
                      globalIdx === selectedIndex
                        ? 'bg-terminal-accent/20 text-terminal-accent'
                        : 'hover:bg-terminal-border text-white'
                    }`}
                    onMouseEnter={() => setSelectedIndex(globalIdx)}
                  >
                    <span className={`p-1.5 rounded-lg ${
                      globalIdx === selectedIndex ? 'bg-terminal-accent/30' : 'bg-terminal-bg'
                    }`}>
                      {cmd.icon}
                    </span>
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium">{cmd.label}</div>
                      <div className="text-xs text-terminal-muted truncate">{cmd.description}</div>
                    </div>
                    <div className="flex items-center gap-2">
                      {cmd.shortcut && (
                        <kbd className="text-[10px] text-terminal-muted bg-terminal-bg px-1.5 py-0.5 rounded border border-terminal-border">
                          {cmd.shortcut}
                        </kbd>
                      )}
                      <ArrowRight size={14} className="text-terminal-muted opacity-0 group-hover:opacity-100" />
                    </div>
                  </div>
                )
              })}
            </div>
          ))}
          {filtered.length === 0 && (
            <div className="p-8 text-center text-terminal-muted text-sm">
              No commands found for "{query}"
            </div>
          )}
        </div>

        <div className="flex items-center gap-4 px-4 py-2 border-t border-terminal-border bg-terminal-bg text-[10px] text-terminal-muted">
          <span><kbd className="px-1 py-0.5 bg-terminal-card border border-terminal-border rounded mx-0.5">↑↓</kbd> Navigate</span>
          <span><kbd className="px-1 py-0.5 bg-terminal-card border border-terminal-border rounded mx-0.5">↵</kbd> Open</span>
          <span><kbd className="px-1 py-0.5 bg-terminal-card border border-terminal-border rounded mx-0.5">Esc</kbd> Close</span>
        </div>
      </div>
    </div>
  )
}
