import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { MessageSquare, Bell, Bot, TrendingUp, Plus, ArrowRight, Loader2, Brain, Sparkles, Zap, Users } from 'lucide-react'
import { agentAPI, alertsAPI } from '../../services/api'

interface Conversation {
  id: number
  title: string | null
  symbol: string | null
  created_at: string | null
  updated_at: string | null
}

interface AIAlert {
  id: number
  symbol: string | null
  alert_type: string
  severity: string
  title: string
  summary: string | null
  is_read: boolean
  created_at: string | null
}

export default function AgentDashboard() {
  const navigate = useNavigate()
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [alerts, setAlerts] = useState<AIAlert[]>([])
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState({ total: 0, unreadAlerts: 0, todayCount: 0 })

  useEffect(() => {
    Promise.all([fetchConversations(), fetchAlerts()]).finally(() => setLoading(false))
  }, [])

  const fetchConversations = async () => {
    try {
      const res = await agentAPI.conversations()
      if (res.data.success) {
        const data = res.data.data
        setConversations(data)
        const today = new Date().toDateString()
        setStats(prev => ({
          ...prev,
          total: data.length,
          todayCount: data.filter((c: Conversation) =>
            c.created_at && new Date(c.created_at).toDateString() === today
          ).length,
        }))
      }
    } catch {
      // ignore
    }
  }

  const fetchAlerts = async () => {
    try {
      const res = await alertsAPI.list(10)
      if (res.data.success) {
        const data = res.data.data
        setAlerts(data)
        setStats(prev => ({ ...prev, unreadAlerts: data.filter((a: AIAlert) => !a.is_read).length }))
      }
    } catch {
      // ignore
    }
  }

  const markAlertRead = async (id: number) => {
    try {
      await alertsAPI.markRead(id)
      setAlerts(prev => prev.map(a => a.id === id ? { ...a, is_read: true } : a))
      setStats(prev => ({ ...prev, unreadAlerts: Math.max(0, prev.unreadAlerts - 1) }))
    } catch {
      // ignore
    }
  }

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return ''
    const d = new Date(dateStr)
    const now = new Date()
    const diffMs = now.getTime() - d.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    if (diffMins < 60) return `${diffMins}m ago`
    const diffHours = Math.floor(diffMins / 60)
    if (diffHours < 24) return `${diffHours}h ago`
    return d.toLocaleDateString()
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 size={24} className="animate-spin text-terminal-muted" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold flex items-center gap-2">
            <Brain size={24} className="text-terminal-accent" />
            AI Agent Dashboard
          </h1>
          <p className="text-sm text-terminal-muted mt-1">Powered by GPT-4 with 20+ financial tools</p>
        </div>
        <button
          onClick={() => navigate('/ai')}
          className="flex items-center gap-2 px-4 py-2 bg-terminal-accent text-white rounded-lg text-sm hover:bg-terminal-accent/90 transition-colors"
        >
          <Plus size={16} />
          New Chat
        </button>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-terminal-card border border-terminal-border rounded-xl p-4">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm text-terminal-muted">Total Conversations</span>
            <div className="p-2 bg-terminal-accent/20 rounded-lg">
              <MessageSquare size={18} className="text-terminal-accent" />
            </div>
          </div>
          <div className="text-2xl font-bold">{stats.total}</div>
          <div className="text-xs text-terminal-muted mt-1">
            {stats.todayCount} today
          </div>
        </div>

        <div className="bg-terminal-card border border-terminal-border rounded-xl p-4">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm text-terminal-muted">Unread Alerts</span>
            <div className="p-2 bg-orange-500/20 rounded-lg">
              <Bell size={18} className="text-orange-400" />
            </div>
          </div>
          <div className="text-2xl font-bold">{stats.unreadAlerts}</div>
          <div className="text-xs text-terminal-muted mt-1">
            {alerts.length > 0 ? `${alerts.filter(a => a.is_read).length} read` : 'No alerts'}
          </div>
        </div>

        <div className="bg-terminal-card border border-terminal-border rounded-xl p-4">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm text-terminal-muted">Tools Available</span>
            <div className="p-2 bg-purple-500/20 rounded-lg">
              <Zap size={18} className="text-purple-400" />
            </div>
          </div>
          <div className="text-2xl font-bold">22</div>
          <div className="text-xs text-terminal-muted mt-1">
            Quotes, fundamentals, risk & more
          </div>
        </div>

        <div className="bg-terminal-card border border-terminal-border rounded-xl p-4">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm text-terminal-muted">Agent Status</span>
            <div className="p-2 bg-green-500/20 rounded-lg">
              <Bot size={18} className="text-green-400" />
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
            <span className="text-sm font-medium">Online</span>
          </div>
          <div className="text-xs text-terminal-muted mt-1">
            GPT-4 + function calling
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-6">
        {/* Recent Conversations */}
        <div className="bg-terminal-card border border-terminal-border rounded-xl">
          <div className="flex items-center justify-between p-4 border-b border-terminal-border">
            <h2 className="font-semibold flex items-center gap-2">
              <MessageSquare size={16} className="text-terminal-accent" />
              Recent Conversations
            </h2>
            <button
              onClick={() => navigate('/ai')}
              className="text-xs text-terminal-accent hover:underline flex items-center gap-1"
            >
              View all <ArrowRight size={12} />
            </button>
          </div>
          <div className="divide-y divide-terminal-border">
            {conversations.length > 0 ? (
              conversations.slice(0, 8).map(conv => (
                <div
                  key={conv.id}
                  onClick={() => navigate(`/ai?conv=${conv.id}`)}
                  className="flex items-center gap-3 p-3 hover:bg-terminal-border/50 cursor-pointer transition-colors"
                >
                  <div className="p-1.5 bg-terminal-bg rounded-lg">
                    <MessageSquare size={14} className="text-terminal-muted" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm truncate">{conv.title || 'Untitled'}</div>
                    <div className="text-xs text-terminal-muted">
                      {formatDate(conv.updated_at || conv.created_at)}
                      {conv.symbol && <> · {conv.symbol}</>}
                    </div>
                  </div>
                  <ArrowRight size={14} className="text-terminal-muted" />
                </div>
              ))
            ) : (
              <div className="p-8 text-center text-terminal-muted">
                <Bot size={32} className="mx-auto mb-2 opacity-50" />
                <p className="text-sm">No conversations yet</p>
                <button
                  onClick={() => navigate('/ai')}
                  className="mt-3 text-xs text-terminal-accent hover:underline"
                >
                  Start your first chat
                </button>
              </div>
            )}
          </div>
        </div>

        {/* AI Alerts */}
        <div className="bg-terminal-card border border-terminal-border rounded-xl">
          <div className="flex items-center justify-between p-4 border-b border-terminal-border">
            <h2 className="font-semibold flex items-center gap-2">
              <Bell size={16} className="text-orange-400" />
              Recent AI Alerts
            </h2>
          </div>
          <div className="divide-y divide-terminal-border">
            {alerts.length > 0 ? (
              alerts.slice(0, 8).map(alert => (
                <div
                  key={alert.id}
                  className={`p-3 ${!alert.is_read ? 'bg-terminal-accent/5 border-l-2 border-l-terminal-accent' : ''}`}
                >
                  <div className="flex items-start gap-3">
                    <div className={`p-1.5 rounded-lg ${
                      alert.severity === 'high' ? 'bg-red-500/20' :
                      alert.severity === 'medium' ? 'bg-orange-500/20' :
                      'bg-blue-500/20'
                    }`}>
                      <Sparkles size={14} className={
                        alert.severity === 'high' ? 'text-red-400' :
                        alert.severity === 'medium' ? 'text-orange-400' :
                        'text-blue-400'
                      } />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium truncate">{alert.title}</span>
                        {!alert.is_read && (
                          <button
                            onClick={(e) => { e.stopPropagation(); markAlertRead(alert.id) }}
                            className="text-[10px] text-terminal-muted hover:text-white ml-2 flex-shrink-0"
                          >
                            Dismiss
                          </button>
                        )}
                      </div>
                      {alert.summary && (
                        <p className="text-xs text-terminal-muted mt-1 line-clamp-2">{alert.summary}</p>
                      )}
                      <div className="flex items-center gap-2 mt-1.5">
                        <span className="text-[10px] text-terminal-muted">{formatDate(alert.created_at)}</span>
                        {alert.symbol && (
                          <span className="text-[10px] px-1.5 py-0.5 bg-terminal-bg rounded font-mono">
                            {alert.symbol}
                          </span>
                        )}
                        <span className={`text-[10px] px-1.5 py-0.5 rounded ${
                          alert.severity === 'high' ? 'bg-red-500/10 text-red-400' :
                          alert.severity === 'medium' ? 'bg-orange-500/10 text-orange-400' :
                          'bg-blue-500/10 text-blue-400'
                        }`}>
                          {alert.alert_type.replace(/_/g, ' ')}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="p-8 text-center text-terminal-muted">
                <Bell size={32} className="mx-auto mb-2 opacity-50" />
                <p className="text-sm">No alerts yet</p>
                <p className="text-xs mt-1">Alerts appear here when the AI detects actionable insights</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-terminal-card border border-terminal-border rounded-xl p-4">
        <h2 className="font-semibold mb-3 flex items-center gap-2">
          <Zap size={16} className="text-terminal-accent" />
          Quick Actions
        </h2>
        <div className="grid grid-cols-4 gap-3">
          {[
            { label: 'Analyze Stock', desc: 'Get fundamentals and quote', icon: TrendingUp, action: () => navigate('/ai?q=Analyze+RELIANCE') },
            { label: 'Compare Companies', desc: 'Side-by-side comparison', icon: Users, action: () => navigate('/ai?q=Compare+TCS+vs+INFY') },
            { label: 'Screen Stocks', desc: 'Filter by PE, ROE, sector', icon: Zap, action: () => navigate('/ai?q=Screen+stocks+PE+<+20+ROE+>+15') },
            { label: 'Risk Analysis', desc: 'VaR, Monte Carlo, stress test', icon: Brain, action: () => navigate('/ai?q=Risk+analysis+for+ICICIBANK') },
          ].map((item, idx) => (
            <button
              key={idx}
              onClick={item.action}
              className="flex items-start gap-3 p-3 bg-terminal-bg border border-terminal-border rounded-lg hover:bg-terminal-border transition-colors text-left"
            >
              <div className="p-2 bg-terminal-accent/20 rounded-lg flex-shrink-0">
                <item.icon size={16} className="text-terminal-accent" />
              </div>
              <div>
                <div className="text-sm font-medium">{item.label}</div>
                <div className="text-xs text-terminal-muted mt-0.5">{item.desc}</div>
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
