import { useState, useEffect, useRef } from 'react'
import { BrowserRouter, Routes, Route, useNavigate, useLocation } from 'react-router-dom'
import { Search, Bell, Settings, Menu, X, LayoutDashboard, TrendingUp, Filter, Share2, LineChart, MessageSquare, Plus, Star, TrendingDown, TrendingUpIcon, Activity, RefreshCw, Wifi, WifiOff, Moon, Sun, ArrowRight, Layers } from 'lucide-react'
import Dashboard from './components/Dashboard/Dashboard'
import QuoteBoard from './components/Dashboard/QuoteBoard'
import Quotes from './components/Quotes/Quotes'
import Charts from './components/Charts/Charts'
import GraphExplorer from './components/Graph/GraphExplorer'
import AIChat from './components/AIChat/AIChat'
import Screener from './components/Screener/Screener'
import News from './components/News/News'
import OptionChain from './components/OptionChain/OptionChain'
import axios from 'axios'

interface Notification {
  id: number
  type: 'alert' | 'news' | 'price'
  title: string
  message: string
  symbol?: string
  time: string
  read: boolean
}

interface MarketStatus {
  isOpen: boolean
  nifty: { price: number; change: number }
  bankNifty: { price: number; change: number }
}

function AppContent() {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [showSearch, setShowSearch] = useState(false)
  const [searchResults, setSearchResults] = useState<{stocks: any[]; sectors: any[]; news: any[]}>({ stocks: [], sectors: [], news: [] })
  const [showNotifications, setShowNotifications] = useState(false)
  const [showSettings, setShowSettings] = useState(false)
  const [darkMode, setDarkMode] = useState(true)
  const [autoRefresh, setAutoRefresh] = useState(true)
  const [refreshInterval, setRefreshInterval] = useState(60)
  const [isConnected, setIsConnected] = useState(true)
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [marketStatus, setMarketStatus] = useState<MarketStatus | null>(null)
  const [trending, setTrending] = useState<any[]>([])
  const [searchLoading, setSearchLoading] = useState(false)
  const [refreshStatus, setRefreshStatus] = useState<{last?: string; loading?: boolean}>({})
  const searchRef = useRef<HTMLDivElement>(null)
  const navigate = useNavigate()
  const location = useLocation()

  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: <LayoutDashboard size={18} />, path: '/' },
    { id: 'quotes', label: 'Quotes', icon: <TrendingUp size={18} />, path: '/quotes' },
    { id: 'screener', label: 'Screener', icon: <Filter size={18} />, path: '/screener' },
    { id: 'graph', label: 'Knowledge Graph', icon: <Share2 size={18} />, path: '/graph' },
    { id: 'charts', label: 'Charts', icon: <LineChart size={18} />, path: '/charts' },
    { id: 'options', label: 'Option Chain', icon: <Layers size={18} />, path: '/options' },
    { id: 'news', label: 'News', icon: <Bell size={18} />, path: '/news' },
    { id: 'ai', label: 'AI Assistant', icon: <MessageSquare size={18} />, path: '/ai' },
  ]

  const currentNav = navItems.find(item => item.path === location.pathname) || navItems[0]

  // Close search when clicking outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(e.target as Node)) {
        setShowSearch(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  useEffect(() => {
    fetchNotifications()
    fetchMarketStatus()
    fetchTrending()
    
    if (autoRefresh) {
      const interval = setInterval(() => {
        fetchMarketStatus()
        fetchNotifications()
      }, refreshInterval * 1000)
      return () => clearInterval(interval)
    }
  }, [autoRefresh, refreshInterval])

  // Search with debounce
  useEffect(() => {
    if (searchQuery.length >= 1) {
      const timer = setTimeout(() => {
        performSearch(searchQuery)
      }, 150)
      return () => clearTimeout(timer)
    } else {
      setSearchResults({ stocks: [], sectors: [], news: [] })
      setShowSearch(false)
    }
  }, [searchQuery])

  const performSearch = async (query: string) => {
    if (!query.trim()) return
    
    setSearchLoading(true)
    try {
      const res = await axios.get(`/api/v1/search/search?q=${encodeURIComponent(query)}`, { timeout: 2000 })
      if (res.data.success) {
        setSearchResults(res.data.data)
        setShowSearch(true)
      }
    } catch (error) {
      console.error('Search failed:', error)
    } finally {
      setSearchLoading(false)
    }
  }

  const fetchTrending = async () => {
    try {
      const res = await axios.get('/api/v1/search/trending', { timeout: 5000 })
      if (res.data.success) {
        setTrending(res.data.data)
      }
    } catch (error) {
      console.error('Failed to fetch trending:', error)
    }
  }

  const fetchNotifications = async () => {
    try {
      const newsRes = await axios.get('/api/v1/news?limit=5', { timeout: 5000 }).catch(() => null)
      const moversRes = await axios.get('/api/v1/quotes/movers', { timeout: 5000 }).catch(() => null)
      
      const notifs: Notification[] = []
      
      if (newsRes?.data?.success) {
        newsRes.data.data.slice(0, 3).forEach((item: any, idx: number) => {
          notifs.push({
            id: idx + 1,
            type: 'news',
            title: item.headline?.substring(0, 50) + '...',
            message: item.source,
            time: item.timestamp ? new Date(item.timestamp).toLocaleTimeString() : 'Now',
            read: false,
          })
        })
      }
      
      if (moversRes?.data?.success) {
        const topGainer = moversRes.data.data?.gainers?.[0]
        if (topGainer) {
          notifs.push({
            id: 100,
            type: 'price',
            title: `${topGainer.symbol} is top gainer`,
            message: `+${topGainer.pct_change?.toFixed(2)}% today`,
            symbol: topGainer.symbol,
            time: 'Live',
            read: false,
          })
        }
      }
      
      setNotifications(notifs)
      setIsConnected(true)
    } catch (error) {
      setIsConnected(false)
    }
  }

  const fetchMarketStatus = async () => {
    try {
      const res = await axios.get('/api/v1/quotes/indices', { timeout: 5000 })
      if (res.data.success) {
        const indices = res.data.data
        const nifty = indices.find((i: any) => i.symbol === 'NIFTY50')
        const bankNifty = indices.find((i: any) => i.symbol === 'BANKNIFTY')
        
        setMarketStatus({
          isOpen: true,
          nifty: { price: nifty?.price || 0, change: nifty?.pct_change || 0 },
          bankNifty: { price: bankNifty?.price || 0, change: bankNifty?.pct_change || 0 },
        })
      }
    } catch (error) {
      console.error('Failed to fetch market status')
    }
  }

  const triggerDataRefresh = async () => {
    setRefreshStatus({ loading: true })
    try {
      await axios.post('/api/v1/webhooks/refresh/all')
      await fetchNotifications()
      await fetchMarketStatus()
      await fetchTrending()
      setRefreshStatus({ last: new Date().toLocaleTimeString(), loading: false })
    } catch (error) {
      console.error('Refresh failed:', error)
      setRefreshStatus({ loading: false })
    }
  }

  const handleSearchSelect = (type: string, item: any) => {
    setShowSearch(false)
    setSearchQuery('')
    
    if (type === 'stock') {
      navigate(`/charts?symbol=${item.symbol}`)
    } else if (type === 'sector') {
      navigate(`/screener?sector=${encodeURIComponent(item.name)}`)
    } else if (type === 'news') {
      // Could open news modal
    }
  }

  const markAllRead = () => {
    setNotifications(notifs => notifs.map(n => ({ ...n, read: true })))
  }

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    if (searchQuery.trim()) {
      setShowSearch(false)
      navigate(`/quotes?symbol=${searchQuery.trim().toUpperCase()}`)
    }
  }

  const unreadCount = notifications.filter(n => !n.read).length

  return (
    <div className={`h-full flex flex-col ${darkMode ? 'bg-[#0d1117] text-white' : 'bg-gray-100 text-gray-900'} transition-colors`}>
      {/* Header */}
      <header className={`h-14 ${darkMode ? 'bg-[#161b22] border-[#30363d]' : 'bg-white border-gray-200'} border-b flex items-center px-4 gap-4`}>
        <button 
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className={`p-2 ${darkMode ? 'hover:bg-[#21262d]' : 'hover:bg-gray-200'} rounded-lg transition-colors`}
        >
          {sidebarOpen ? <X size={20} /> : <Menu size={20} />}
        </button>
        
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center font-bold text-white">
            F
          </div>
          <span className="font-bold text-lg bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">FinGraph</span>
        </div>
        
        {/* Search Bar */}
        <div ref={searchRef} className="flex-1 max-w-2xl mx-4 relative">
          <form onSubmit={handleSearch}>
            <div className="relative">
              <Search className={`absolute left-3 top-1/2 -translate-y-1/2 ${darkMode ? 'text-gray-400' : 'text-gray-500'}`} size={18} />
              <input
                type="text"
                placeholder="Search stocks, sectors, news... (Press / to focus)"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onFocus={() => searchQuery && setShowSearch(true)}
                className={`w-full pl-10 pr-4 py-2 ${darkMode ? 'bg-[#0d1117] border-[#30363d]' : 'bg-gray-100 border-gray-200'} border rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all`}
                autoComplete="off"
              />
              {searchLoading && (
                <div className="absolute right-3 top-1/2 -translate-y-1/2">
                  <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                </div>
              )}
            </div>
          </form>
          
          {/* Search Results Dropdown */}
          {showSearch && (searchResults.stocks.length > 0 || searchResults.sectors.length > 0 || searchResults.news.length > 0) && (
            <div className={`absolute top-full left-0 right-0 mt-2 ${darkMode ? 'bg-[#161b22] border-[#30363d]' : 'bg-white border-gray-200'} border rounded-xl shadow-2xl z-50 max-h-96 overflow-auto`}>
              {/* Stocks */}
              {searchResults.stocks.length > 0 && (
                <div>
                  <div className={`px-4 py-2 text-xs font-semibold uppercase ${darkMode ? 'text-gray-400 bg-[#0d1117]' : 'text-gray-500 bg-gray-50'}`}>
                    Stocks
                  </div>
                  {searchResults.stocks.slice(0, 6).map((stock, idx) => (
                    <div
                      key={idx}
                      onClick={() => handleSearchSelect('stock', stock)}
                      className={`px-4 py-3 cursor-pointer flex items-center justify-between ${darkMode ? 'hover:bg-[#21262d]' : 'hover:bg-gray-50'}`}
                    >
                      <div className="flex items-center gap-3">
                        <div className={`w-10 h-10 ${darkMode ? 'bg-[#21262d]' : 'bg-gray-100'} rounded-lg flex items-center justify-center font-bold text-sm`}>
                          {stock.symbol?.substring(0, 2)}
                        </div>
                        <div>
                          <div className="font-medium">{stock.symbol}</div>
                          <div className={`text-xs ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>{stock.name}</div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="font-mono">₹{stock.price?.toLocaleString()}</div>
                        <div className={`text-xs ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>{stock.sector}</div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
              
              {/* Sectors */}
              {searchResults.sectors.length > 0 && (
                <div className={`border-t ${darkMode ? 'border-[#30363d]' : 'border-gray-200'}`}>
                  <div className={`px-4 py-2 text-xs font-semibold uppercase ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                    Sectors
                  </div>
                  {searchResults.sectors.map((sector, idx) => (
                    <div
                      key={idx}
                      onClick={() => handleSearchSelect('sector', sector)}
                      className={`px-4 py-3 cursor-pointer flex items-center gap-3 ${darkMode ? 'hover:bg-[#21262d]' : 'hover:bg-gray-50'}`}
                    >
                      <span className="text-2xl">{sector.icon}</span>
                      <div>
                        <div className="font-medium">{sector.name}</div>
                        <div className={`text-xs ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>{sector.description}</div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
              
              {/* News */}
              {searchResults.news.length > 0 && (
                <div className={`border-t ${darkMode ? 'border-[#30363d]' : 'border-gray-200'}`}>
                  <div className={`px-4 py-2 text-xs font-semibold uppercase ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                    News
                  </div>
                  {searchResults.news.slice(0, 5).map((news, idx) => (
                    <a
                      key={idx}
                      href={news.url || `https://www.google.com/search?q=${encodeURIComponent(news.headline)}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className={`px-4 py-3 cursor-pointer flex items-center justify-between group ${darkMode ? 'hover:bg-[#21262d]' : 'hover:bg-gray-50'}`}
                    >
                      <div>
                        <div className="font-medium text-sm line-clamp-1">{news.headline}</div>
                        <div className={`text-xs ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>{news.source}</div>
                      </div>
                      <ArrowRight size={14} className="opacity-0 group-hover:opacity-100 transition-opacity" />
                    </a>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
        
        {/* Connection Status */}
        <div className={`flex items-center gap-1 px-2 py-1 rounded ${isConnected ? 'text-green-500' : 'text-red-500'}`}>
          {isConnected ? <Wifi size={14} /> : <WifiOff size={14} />}
          <span className="text-xs font-medium">{isConnected ? 'Live' : 'Offline'}</span>
        </div>
        
        <div className="flex items-center gap-2">
          <button 
            onClick={triggerDataRefresh}
            disabled={refreshStatus.loading}
            className={`p-2 ${darkMode ? 'hover:bg-[#21262d]' : 'hover:bg-gray-200'} rounded-lg transition-colors disabled:opacity-50`}
            title={refreshStatus.last ? `Last updated: ${refreshStatus.last}` : 'Refresh all data'}
          >
            <RefreshCw size={20} className={refreshStatus.loading ? 'animate-spin' : ''} />
          </button>
          
          <button 
            onClick={() => setShowNotifications(!showNotifications)}
            className={`p-2 ${darkMode ? 'hover:bg-[#21262d]' : 'hover:bg-gray-200'} rounded-lg transition-colors relative`}
          >
            <Bell size={20} />
            {unreadCount > 0 && (
              <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center font-bold">
                {unreadCount > 9 ? '9+' : unreadCount}
              </span>
            )}
          </button>
          
          <button 
            onClick={() => setShowSettings(!showSettings)}
            className={`p-2 ${darkMode ? 'hover:bg-[#21262d]' : 'hover:bg-gray-200'} rounded-lg transition-colors`}
          >
            <Settings size={20} />
          </button>
        </div>
      </header>
      
      <div className="flex-1 flex overflow-hidden">
        {sidebarOpen && (
          <aside className={`w-64 ${darkMode ? 'bg-[#161b22] border-[#30363d]' : 'bg-white border-gray-200'} border-r flex flex-col`}>
            <nav className="p-3">
              <div className="space-y-1">
                {navItems.map((item) => (
                  <button
                    key={item.id}
                    onClick={() => navigate(item.path)}
                    className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                      currentNav.id === item.id 
                        ? 'bg-gradient-to-r from-blue-500/20 to-purple-500/20 text-blue-400 border border-blue-500/30' 
                        : `${darkMode ? 'hover:bg-[#21262d] text-gray-300' : 'hover:bg-gray-100 text-gray-700'}`
                    }`}
                  >
                    {item.icon}
                    {item.label}
                  </button>
                ))}
              </div>
            </nav>
            
            <WatchlistSection darkMode={darkMode} trending={trending} />
          </aside>
        )}
        
        <main className="flex-1 flex flex-col overflow-hidden">
          <QuoteBoard />
          
          <div className="flex-1 overflow-auto p-4">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/quotes" element={<Quotes />} />
              <Route path="/screener" element={<Screener />} />
              <Route path="/graph" element={<GraphExplorer />} />
              <Route path="/charts" element={<Charts />} />
              <Route path="/options" element={<OptionChain />} />
              <Route path="/news" element={<News />} />
              <Route path="/ai" element={<AIChat />} />
            </Routes>
          </div>
        </main>
      </div>
      
      {/* Notifications Panel */}
      {showNotifications && (
        <div className={`fixed top-14 right-4 w-96 ${darkMode ? 'bg-[#161b22] border-[#30363d]' : 'bg-white border-gray-200'} border rounded-xl shadow-2xl z-50 backdrop-blur-lg bg-opacity-95`}>
          <div className="p-4 border-b border-[#30363d] flex items-center justify-between">
            <h3 className="font-bold flex items-center gap-2">
              <Bell size={18} className="text-blue-400" />
              Notifications
              {unreadCount > 0 && <span className="text-xs bg-blue-500 text-white px-2 py-0.5 rounded-full">{unreadCount} new</span>}
            </h3>
            <div className="flex items-center gap-2">
              <button onClick={markAllRead} className="text-xs text-blue-400 hover:underline">Mark all read</button>
              <button onClick={() => setShowNotifications(false)} className={`p-1 ${darkMode ? 'hover:bg-[#21262d]' : 'hover:bg-gray-200'} rounded`}>
                <X size={16} />
              </button>
            </div>
          </div>
          <div className="max-h-96 overflow-auto">
            {notifications.length > 0 ? notifications.map((notif) => (
              <div 
                key={notif.id} 
                className={`p-4 border-b border-[#30363d] hover:bg-[#21262d] cursor-pointer transition-colors ${!notif.read ? 'bg-blue-500/5 border-l-4 border-l-blue-500' : ''}`}
                onClick={() => {
                  if (notif.symbol) navigate(`/charts?symbol=${notif.symbol}`)
                  setNotifications(n => n.map(n2 => n2.id === notif.id ? { ...n2, read: true } : n2))
                }}
              >
                <div className="flex items-start gap-3">
                  <div className={`mt-1 p-2 rounded-full ${notif.type === 'alert' ? 'bg-red-500/20 text-red-400' : notif.type === 'price' ? 'bg-green-500/20 text-green-400' : 'bg-blue-500/20 text-blue-400'}`}>
                    {notif.type === 'alert' ? <TrendingDown size={14} /> : notif.type === 'price' ? <TrendingUpIcon size={14} /> : <Activity size={14} />}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium">{notif.title}</span>
                      <span className="text-xs text-gray-500">{notif.time}</span>
                    </div>
                    <p className="text-xs text-gray-400 mt-1">{notif.message}</p>
                  </div>
                  {!notif.read && <div className="w-2 h-2 bg-blue-500 rounded-full mt-2"></div>}
                </div>
              </div>
            )) : (
              <div className="p-8 text-center text-gray-500">
                <Bell size={32} className="mx-auto mb-2 opacity-50" />
                No notifications
              </div>
            )}
          </div>
        </div>
      )}

      {/* Settings Panel */}
      {showSettings && (
        <div className={`fixed top-14 right-4 w-80 ${darkMode ? 'bg-[#161b22] border-[#30363d]' : 'bg-white border-gray-200'} border rounded-xl shadow-2xl z-50`}>
          <div className="p-4 border-b border-[#30363d] flex items-center justify-between">
            <h3 className="font-bold flex items-center gap-2">
              <Settings size={18} className="text-blue-400" />
              Settings
            </h3>
            <button onClick={() => setShowSettings(false)} className={`p-1 ${darkMode ? 'hover:bg-[#21262d]' : 'hover:bg-gray-200'} rounded`}>
              <X size={16} />
            </button>
          </div>
          <div className="p-4 space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm flex items-center gap-2">
                {darkMode ? <Moon size={16} /> : <Sun size={16} />}
                Dark Mode
              </span>
              <button onClick={() => setDarkMode(!darkMode)} className={`w-12 h-6 rounded-full relative transition-colors ${darkMode ? 'bg-blue-500' : 'bg-gray-300'}`}>
                <div className={`absolute top-1 w-4 h-4 bg-white rounded-full transition-transform ${darkMode ? 'right-1' : 'left-1'}`}></div>
              </button>
            </div>
            
            <div className="flex items-center justify-between">
              <span className="text-sm flex items-center gap-2">
                <RefreshCw size={16} />
                Auto Refresh
              </span>
              <button onClick={() => setAutoRefresh(!autoRefresh)} className={`w-12 h-6 rounded-full relative transition-colors ${autoRefresh ? 'bg-blue-500' : 'bg-gray-300'}`}>
                <div className={`absolute top-1 w-4 h-4 bg-white rounded-full transition-transform ${autoRefresh ? 'right-1' : 'left-1'}`}></div>
              </button>
            </div>
            
            {autoRefresh && (
              <div className="space-y-2">
                <label className="text-sm text-gray-400">Refresh Interval</label>
                <select
                  value={refreshInterval}
                  onChange={(e) => setRefreshInterval(Number(e.target.value))}
                  className={`w-full px-3 py-2 ${darkMode ? 'bg-[#0d1117] border-[#30363d]' : 'bg-gray-100 border-gray-200'} border rounded-lg text-sm`}
                >
                  <option value={30}>30 seconds</option>
                  <option value={60}>1 minute</option>
                  <option value={300}>5 minutes</option>
                </select>
              </div>
            )}
            
            <div className="border-t border-[#30363d] pt-4">
              <label className="text-sm text-gray-400 mb-2 block">Market Status</label>
              {marketStatus && (
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>Nifty 50</span>
                    <span className={marketStatus.nifty.change >= 0 ? 'text-green-400' : 'text-red-400'}>
                      {marketStatus.nifty.change >= 0 ? '+' : ''}{marketStatus.nifty.change.toFixed(2)}%
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>Bank Nifty</span>
                    <span className={marketStatus.bankNifty.change >= 0 ? 'text-green-400' : 'text-red-400'}>
                      {marketStatus.bankNifty.change >= 0 ? '+' : ''}{marketStatus.bankNifty.change.toFixed(2)}%
                    </span>
                  </div>
                </div>
              )}
            </div>
            
            <div className="border-t border-[#30363d] pt-4 text-center text-xs text-gray-500">
              FinGraph Terminal v1.0.0
            </div>
          </div>
        </div>
      )}
      
      {/* Footer */}
      <footer className={`h-8 ${darkMode ? 'bg-[#161b22] border-[#30363d] text-gray-400' : 'bg-white border-gray-200 text-gray-600'} border-t flex items-center px-4 text-xs`}>
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
            Market Open
          </span>
          {marketStatus && (
            <>
              <span>NSE: {marketStatus.nifty.price.toLocaleString()} ({marketStatus.nifty.change >= 0 ? '+' : ''}{marketStatus.nifty.change.toFixed(2)}%)</span>
              <span>BankNifty: {marketStatus.bankNifty.price.toLocaleString()} ({marketStatus.bankNifty.change >= 0 ? '+' : ''}{marketStatus.bankNifty.change.toFixed(2)}%)</span>
            </>
          )}
        </div>
        <div className="ml-auto flex items-center gap-2">
          <span>{isConnected ? <Wifi size={12} className="text-green-500" /> : <WifiOff size={12} className="text-red-500" />}</span>
          <span className="text-[10px]">Refresh: {refreshStatus.last || 'Manual'}</span>
        </div>
      </footer>
    </div>
  )
}

function WatchlistSection({ darkMode, trending }: { darkMode: boolean; trending: any[] }) {
  const [watchlists, setWatchlists] = useState<{id: number; name: string; symbols: string[]}[]>([])
  const [stockPrices, setStockPrices] = useState<Record<string, any>>({})
  const [selectedWatchlist, setSelectedWatchlist] = useState<number | null>(null)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [newWatchlistName, setNewWatchlistName] = useState('')
  const [newWatchlistSymbols, setNewWatchlistSymbols] = useState('')
  const navigate = useNavigate()

  useEffect(() => {
    fetchWatchlists()
  }, [])

  useEffect(() => {
    const symbols = watchlists.flatMap(w => w.symbols)
    if (symbols.length > 0) {
      fetchPrices(symbols)
    }
    // Auto-refresh prices every 30 seconds
    const interval = setInterval(() => {
      if (symbols.length > 0) {
        fetchPrices(symbols)
      }
    }, 30000)
    return () => clearInterval(interval)
  }, [watchlists])

  const fetchWatchlists = async () => {
    try {
      const res = await axios.get('/api/v1/watchlist')
      if (res.data.success) {
        setWatchlists(res.data.data)
      }
    } catch (error) {
      console.error('Failed to fetch watchlists')
    }
  }

  const fetchPrices = async (symbols: string[]) => {
    try {
      const res = await axios.get(`/api/v1/quotes/batch?symbols=${symbols.join(',')}`)
      if (res.data.success) {
        const prices: Record<string, any> = {}
        res.data.data.forEach((stock: any) => {
          prices[stock.symbol] = stock
        })
        setStockPrices(prices)
      }
    } catch (error) {
      console.error('Failed to fetch prices')
    }
  }

  const createWatchlist = async () => {
    if (!newWatchlistName.trim()) return
    try {
      const symbols = newWatchlistSymbols.split(',').map(s => s.trim().toUpperCase()).filter(Boolean)
      await axios.post('/api/v1/watchlist', { name: newWatchlistName, symbols })
      setNewWatchlistName('')
      setNewWatchlistSymbols('')
      setShowCreateModal(false)
      fetchWatchlists()
    } catch (error) {
      console.error('Failed to create watchlist')
    }
  }

  const deleteWatchlist = async (id: number) => {
    try {
      await axios.delete(`/api/v1/watchlist/${id}`)
      setSelectedWatchlist(null)
      fetchWatchlists()
    } catch (error) {
      console.error('Failed to delete watchlist')
    }
  }

  const handleStockClick = (symbol: string) => {
    navigate(`/charts?symbol=${symbol}`)
  }

  const selectedWL = watchlists.find(w => w.id === selectedWatchlist)

  return (
    <div className={`flex-1 overflow-auto p-3 border-t ${darkMode ? 'border-[#30363d]' : 'border-gray-200'}`}>
      {/* Watchlists */}
      <div className="flex items-center justify-between mb-3">
        <span className={`text-xs font-bold uppercase ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>Watchlists</span>
        <button onClick={() => setShowCreateModal(true)} className={`p-1 ${darkMode ? 'hover:bg-[#21262d]' : 'hover:bg-gray-200'} rounded`}>
          <Plus size={14} />
        </button>
      </div>
      
      {selectedWL ? (
        <div>
          <button onClick={() => setSelectedWatchlist(null)} className={`text-xs mb-2 ${darkMode ? 'text-gray-400 hover:text-white' : 'text-gray-500 hover:text-black'}`}>
            ← Back to all
          </button>
          <div className="space-y-1">
            {selectedWL.symbols.map((symbol) => {
              const stock = stockPrices[symbol]
              return (
                <div
                  key={symbol}
                  onClick={() => handleStockClick(symbol)}
                  className={`flex items-center justify-between p-2 text-sm ${darkMode ? 'hover:bg-[#21262d]' : 'hover:bg-gray-100'} rounded-lg cursor-pointer transition-colors`}
                >
                  <span className="font-medium">{symbol}</span>
                  <div className="text-right">
                    <div className="font-mono text-xs">₹{stock?.price?.toLocaleString() || '—'}</div>
                    <div className={`text-[10px] font-mono ${(stock?.pct_change || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {stock ? `${(stock.pct_change || 0) >= 0 ? '+' : ''}${stock.pct_change?.toFixed(2)}%` : '—'}
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
          <button
            onClick={() => deleteWatchlist(selectedWL.id)}
            className={`mt-2 text-xs ${darkMode ? 'text-red-400 hover:text-red-300' : 'text-red-500 hover:text-red-600'}`}
          >
            Delete watchlist
          </button>
        </div>
      ) : (
        <div className="space-y-2">
          {watchlists.length > 0 ? watchlists.map((watchlist) => (
            <div 
              key={watchlist.id}
              onClick={() => setSelectedWatchlist(watchlist.id)}
              className={`p-2 rounded-lg ${darkMode ? 'hover:bg-[#21262d]' : 'hover:bg-gray-100'} cursor-pointer transition-colors`}
            >
              <div className="flex items-center gap-2 mb-1">
                <Star size={12} className="text-yellow-500" />
                <span className="text-sm font-medium">{watchlist.name}</span>
              </div>
              <div className={`text-xs ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                {watchlist.symbols.slice(0, 3).join(' • ')}
              </div>
            </div>
          )) : (
            <div className={`p-2 text-xs ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
              No watchlists
            </div>
          )}
        </div>
      )}

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center">
          <div className={`${darkMode ? 'bg-[#161b22]' : 'bg-white'} p-4 rounded-lg w-72 border ${darkMode ? 'border-[#30363d]' : 'border-gray-200'}`}>
            <h3 className="font-bold mb-3">Create Watchlist</h3>
            <input
              type="text"
              placeholder="Watchlist name"
              value={newWatchlistName}
              onChange={(e) => setNewWatchlistName(e.target.value)}
              className={`w-full px-3 py-2 mb-2 rounded text-sm ${darkMode ? 'bg-[#0d1117] border-[#30363d]' : 'bg-gray-100 border-gray-200'} border`}
            />
            <input
              type="text"
              placeholder="Symbols (e.g. RELIANCE, TCS)"
              value={newWatchlistSymbols}
              onChange={(e) => setNewWatchlistSymbols(e.target.value)}
              className={`w-full px-3 py-2 mb-3 rounded text-sm ${darkMode ? 'bg-[#0d1117] border-[#30363d]' : 'bg-gray-100 border-gray-200'} border`}
            />
            <div className="flex gap-2">
              <button onClick={createWatchlist} className="flex-1 py-2 bg-[#238636] text-white rounded text-sm hover:bg-[#2ea043]">
                Create
              </button>
              <button onClick={() => setShowCreateModal(false)} className={`flex-1 py-2 ${darkMode ? 'bg-[#21262d]' : 'bg-gray-200'} rounded text-sm`}>
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Trending */}
      <div className="mt-4">
        <div className="flex items-center gap-2 mb-2">
          <TrendingUp size={14} className="text-orange-500" />
          <span className={`text-xs font-bold uppercase ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>Trending</span>
        </div>
        <div className="space-y-1">
          {trending.slice(0, 5).map((stock, idx) => (
            <div 
              key={stock.symbol}
              onClick={() => handleStockClick(stock.symbol)}
              className={`flex items-center justify-between p-2 text-sm ${darkMode ? 'hover:bg-[#21262d]' : 'hover:bg-gray-100'} rounded-lg cursor-pointer transition-colors`}
            >
              <div className="flex items-center gap-2">
                <span className={`w-5 h-5 rounded flex items-center justify-center text-xs font-bold ${darkMode ? 'bg-[#21262d]' : 'bg-gray-100'}`}>
                  {idx + 1}
                </span>
                <span className="font-medium">{stock.symbol}</span>
              </div>
              <div className="text-right">
                <div className="font-mono text-xs">₹{stock.price?.toLocaleString()}</div>
                <div className={`text-xs font-mono ${stock.change >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                  {(stock.change || 0) >= 0 ? '+' : ''}{(stock.change || 0).toFixed(2)}%
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Quick Links */}
      <div className={`mt-4 pt-4 border-t ${darkMode ? 'border-[#30363d]' : 'border-gray-200'}`}>
        <span className={`text-xs font-bold uppercase ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>Quick Links</span>
        <div className="mt-2 space-y-1">
          <button onClick={() => navigate('/screener')} className={`w-full text-left p-2 text-sm ${darkMode ? 'text-gray-300 hover:bg-[#21262d]' : 'text-gray-700 hover:bg-gray-100'} rounded-lg cursor-pointer flex items-center justify-between`}>
            <span>Stock Screener</span>
            <ArrowRight size={14} />
          </button>
          <button onClick={() => navigate('/graph')} className={`w-full text-left p-2 text-sm ${darkMode ? 'text-gray-300 hover:bg-[#21262d]' : 'text-gray-700 hover:bg-gray-100'} rounded-lg cursor-pointer flex items-center justify-between`}>
            <span>Knowledge Graph</span>
            <ArrowRight size={14} />
          </button>
          <button onClick={() => navigate('/ai')} className={`w-full text-left p-2 text-sm ${darkMode ? 'text-gray-300 hover:bg-[#21262d]' : 'text-gray-700 hover:bg-gray-100'} rounded-lg cursor-pointer flex items-center justify-between`}>
            <span>Ask AI</span>
            <ArrowRight size={14} />
          </button>
        </div>
      </div>
    </div>
  )
}

function App() {
  return (
    <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <AppContent />
    </BrowserRouter>
  )
}

export default App
