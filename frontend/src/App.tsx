import { useState } from 'react'
import { BrowserRouter, Routes, Route, useNavigate, useLocation } from 'react-router-dom'
import { Search, Bell, Settings, Menu, X, LayoutDashboard, TrendingUp, Filter, Share2, LineChart, MessageSquare } from 'lucide-react'
import Dashboard from './components/Dashboard/Dashboard'
import QuoteBoard from './components/Dashboard/QuoteBoard'
import Sidebar from './components/common/Sidebar'
import Quotes from './components/Quotes/Quotes'
import Charts from './components/Charts/Charts'
import GraphExplorer from './components/Graph/GraphExplorer'
import AIChat from './components/AIChat/AIChat'
import Screener from './components/Screener/Screener'

function AppContent() {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const navigate = useNavigate()
  const location = useLocation()

  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: <LayoutDashboard size={18} />, path: '/' },
    { id: 'quotes', label: 'Quotes', icon: <TrendingUp size={18} />, path: '/quotes' },
    { id: 'screener', label: 'Screener', icon: <Filter size={18} />, path: '/screener' },
    { id: 'graph', label: 'Knowledge Graph', icon: <Share2 size={18} />, path: '/graph' },
    { id: 'charts', label: 'Charts', icon: <LineChart size={18} />, path: '/charts' },
    { id: 'ai', label: 'AI Assistant', icon: <MessageSquare size={18} />, path: '/ai' },
  ]

  const currentNav = navItems.find(item => item.path === location.pathname) || navItems[0]

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    if (searchQuery.trim()) {
      navigate(`/quotes?symbol=${searchQuery.trim().toUpperCase()}`)
    }
  }

  return (
    <div className="h-full flex flex-col bg-terminal-bg">
      {/* Header */}
      <header className="h-14 bg-terminal-card border-b border-terminal-border flex items-center px-4 gap-4">
        <button 
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="p-2 hover:bg-terminal-border rounded-lg transition-colors"
        >
          {sidebarOpen ? <X size={20} /> : <Menu size={20} />}
        </button>
        
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-terminal-accent rounded-lg flex items-center justify-center font-bold text-white">
            F
          </div>
          <span className="font-semibold text-lg">FinGraph</span>
        </div>
        
        <form onSubmit={handleSearch} className="flex-1 max-w-xl mx-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-terminal-muted" size={18} />
            <input
              type="text"
              placeholder="Search symbols, companies... (Press /)"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-terminal-bg border border-terminal-border rounded-lg text-sm focus:border-terminal-accent transition-colors"
            />
          </div>
        </form>
        
        <div className="flex items-center gap-2">
          <button className="p-2 hover:bg-terminal-border rounded-lg transition-colors relative">
            <Bell size={20} />
            <span className="absolute top-1 right-1 w-2 h-2 bg-terminal-danger rounded-full"></span>
          </button>
          <button className="p-2 hover:bg-terminal-border rounded-lg transition-colors">
            <Settings size={20} />
          </button>
        </div>
      </header>
      
      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar */}
        {sidebarOpen && (
          <aside className="w-64 bg-terminal-card border-r border-terminal-border flex flex-col">
            <nav className="p-3">
              <div className="space-y-1">
                {navItems.map((item) => (
                  <button
                    key={item.id}
                    onClick={() => navigate(item.path)}
                    className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                      currentNav.id === item.id 
                        ? 'bg-terminal-accent/10 text-terminal-accent' 
                        : 'hover:bg-terminal-border text-terminal-text'
                    }`}
                  >
                    {item.icon}
                    {item.label}
                  </button>
                ))}
              </div>
            </nav>
            
            <Sidebar />
          </aside>
        )}
        
        {/* Main Content */}
        <main className="flex-1 flex flex-col overflow-hidden">
          {/* Quote Ticker */}
          <QuoteBoard />
          
          {/* Page Content */}
          <div className="flex-1 overflow-auto p-4">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/quotes" element={<Quotes />} />
              <Route path="/screener" element={<Screener />} />
              <Route path="/graph" element={<GraphExplorer />} />
              <Route path="/charts" element={<Charts />} />
              <Route path="/ai" element={<AIChat />} />
            </Routes>
          </div>
        </main>
      </div>
      
      {/* Footer */}
      <footer className="h-8 bg-terminal-card border-t border-terminal-border flex items-center px-4 text-xs text-terminal-muted">
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 bg-terminal-success rounded-full"></span>
            Market Open
          </span>
          <span>NSE: 22,450.25 (+0.45%)</span>
          <span>BSE: 74,250.80 (+0.38%)</span>
        </div>
        <div className="ml-auto">
          Last Updated: {new Date().toLocaleTimeString()}
        </div>
      </footer>
    </div>
  )
}

function App() {
  return (
    <BrowserRouter>
      <AppContent />
    </BrowserRouter>
  )
}

export default App
