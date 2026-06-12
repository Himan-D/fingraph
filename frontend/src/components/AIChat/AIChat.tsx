import { useState, useEffect, useRef, useCallback } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Send, Bot, User, Loader2, MessageSquare, Plus, Trash2, ChevronRight, Wrench } from 'lucide-react'
import { agentAPI } from '../../services/api'
import { ToolResultRenderer } from './ToolCards'

interface ToolCall {
  name: string
  args: Record<string, unknown>
}

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  toolCalls?: ToolCall[]
  toolResults?: Record<string, any>
  isStreaming?: boolean
}

interface Conversation {
  id: number
  title: string | null
  symbol: string | null
  created_at: string | null
}

export default function AIChat() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [symbol] = useState<string | null>(() => {
    const params = new URLSearchParams(window.location.search)
    return params.get('symbol')
  })
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [activeConvId, setActiveConvId] = useState<number | null>(null)
  const [activeTools, setActiveTools] = useState<Record<string, { name: string; args: Record<string, unknown> }>>({})
  const toolResultsRef = useRef<Record<string, any>>({})
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const abortRef = useRef<AbortController | null>(null)

  const fetchConversations = async () => {
    try {
      const res = await agentAPI.conversations()
      if (res.data.success) {
        setConversations(res.data.data)
      }
    } catch {
      // ignore
    }
  }

  const loadConversation = useCallback(async (id: number) => {
    try {
      const res = await agentAPI.conversation(id)
      if (res.data.success) {
        const conv = res.data.data
        setActiveConvId(id)
        setMessages(
          conv.messages.map((m: { id: number; role: string; content: string; tool_calls?: ToolCall[]; created_at: string }) => ({
            id: String(m.id),
            role: m.role as 'user' | 'assistant',
            content: m.content || '',
            timestamp: new Date(m.created_at),
            toolCalls: m.tool_calls || undefined,
          }))
        )
      }
    } catch {
      // ignore
    }
  }, [])

  const deleteConversation = async (id: number) => {
    try {
      await agentAPI.deleteConversation(id)
      if (activeConvId === id) {
        setActiveConvId(null)
        setMessages([])
      }
      fetchConversations()
    } catch {
      // ignore
    }
  }

  const newConversation = () => {
    setActiveConvId(null)
    setMessages([])
  }

  useEffect(() => {
    fetchConversations()
    const params = new URLSearchParams(window.location.search)
    const convParam = params.get('conv')
    const queryParam = params.get('q')
    if (convParam) {
      loadConversation(parseInt(convParam))
    }
    if (queryParam) {
      setInput(queryParam.replace(/\+/g, ' '))
    }
  }, [loadConversation])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  useEffect(() => {
    const handler = (e: CustomEvent) => {
      setInput(e.detail)
    }
    window.addEventListener('ai-query', handler as EventListener)
    return () => window.removeEventListener('ai-query', handler as EventListener)
  }, [])

  const handleSubmit = async (e?: React.FormEvent) => {
    e?.preventDefault()
    if (!input.trim() || loading) return

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: input,
      timestamp: new Date(),
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)

    const assistantId = `assistant-${Date.now()}`
    const assistantMessage: Message = {
      id: assistantId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      isStreaming: true,
    }
    setMessages(prev => [...prev, assistantMessage])

    try {
      abortRef.current = new AbortController()
      const response = await fetch(agentAPI.chatURL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: input,
          conversation_id: activeConvId,
          symbol: symbol,
        }),
        signal: abortRef.current.signal,
      })

      if (!response.ok) throw new Error('Failed to connect')

      const reader = response.body?.getReader()
      if (!reader) throw new Error('No reader')

      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          try {
            const data = JSON.parse(line.slice(6))

            if (data.type === 'token') {
              setMessages(prev =>
                prev.map(m =>
                  m.id === assistantId
                    ? { ...m, content: m.content + data.content }
                    : m
                )
              )
            } else if (data.type === 'tool_start') {
              setActiveTools(prev => ({
                ...prev,
                [data.tool]: { name: data.tool, args: data.args || {} },
              }))
            } else if (data.type === 'tool_end') {
              setActiveTools(prev => {
                const next = { ...prev }
                delete next[data.tool]
                return next
              })
            } else if (data.type === 'tool_result') {
              toolResultsRef.current[data.tool] = data.data
            } else if (data.type === 'done') {
              if (data.conversation_id && !activeConvId) {
                setActiveConvId(data.conversation_id)
                fetchConversations()
              }
              const tr = { ...toolResultsRef.current }
              toolResultsRef.current = {}
              setMessages(prev =>
                prev.map(m =>
                  m.id === assistantId ? { ...m, isStreaming: false, toolResults: Object.keys(tr).length > 0 ? tr : undefined } : m
                )
              )
            } else if (data.type === 'error') {
              setMessages(prev =>
                prev.map(m =>
                  m.id === assistantId
                    ? { ...m, content: `Error: ${data.message}`, isStreaming: false }
                    : m
                )
              )
            }
          } catch {
            // ignore parse errors
          }
        }
      }
    } catch (err) {
      if (err instanceof Error && err.name !== 'AbortError') {
        setMessages(prev =>
          prev.map(m =>
            m.id === assistantId
              ? { ...m, content: 'Connection error. Please try again.', isStreaming: false }
              : m
          )
        )
      }
    } finally {
      setLoading(false)
      setActiveTools({})
    }
  }

  const toolNames = Object.keys(activeTools)

  const quickActions = [
    'Analyze RELIANCE fundamentals',
    'Compare TCS vs INFY',
    'Screen stocks with PE < 20 and ROE > 15',
    'What is the sentiment for HDFCBANK?',
    'Run risk analysis for ICICIBANK',
    'Latest news about ADANIENT',
  ]

  return (
    <div className="flex h-full">
      {/* Sidebar */}
      <div className="w-64 border-r border-terminal-border bg-terminal-card flex flex-col">
        <div className="p-3 border-b border-terminal-border">
          <button
            onClick={newConversation}
            className="w-full flex items-center gap-2 px-3 py-2 bg-terminal-accent text-white rounded-lg text-sm hover:bg-terminal-accent/90 transition-colors"
          >
            <Plus size={16} />
            New Chat
          </button>
        </div>
        <div className="flex-1 overflow-auto p-2 space-y-1">
          {conversations.map(conv => (
            <div
              key={conv.id}
              className={`group flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer transition-colors ${
                activeConvId === conv.id
                  ? 'bg-terminal-accent/20 text-terminal-accent'
                  : 'hover:bg-terminal-border text-terminal-muted'
              }`}
              onClick={() => loadConversation(conv.id)}
            >
              <MessageSquare size={14} className="flex-shrink-0" />
              <span className="text-sm truncate flex-1">{conv.title || 'Untitled'}</span>
              <button
                onClick={(e) => { e.stopPropagation(); deleteConversation(conv.id) }}
                className="opacity-0 group-hover:opacity-100 p-1 hover:text-red-400 transition-opacity"
              >
                <Trash2 size={12} />
              </button>
            </div>
          ))}
          {conversations.length === 0 && (
            <p className="text-xs text-terminal-muted text-center py-4">No conversations yet</p>
          )}
        </div>
      </div>

      {/* Main Chat */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-terminal-border bg-terminal-card">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-terminal-accent/20 rounded-lg">
              <Bot size={24} className="text-terminal-accent" />
            </div>
            <div>
              <h2 className="font-semibold">AI Assistant</h2>
              <p className="text-xs text-terminal-muted">Powered by GPT-4 with real-time market tools</p>
            </div>
          </div>
          {symbol && (
            <span className="px-3 py-1 bg-terminal-accent text-white rounded-full text-sm font-medium">
              {symbol}
            </span>
          )}
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-auto p-4 space-y-4">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full text-terminal-muted">
              <Bot size={48} className="mb-4 opacity-50" />
              <h3 className="text-lg font-medium mb-2">Ask me anything about Indian markets</h3>
              <p className="text-sm mb-6">I can analyze stocks, run risk models, search news, and more</p>
              <div className="grid grid-cols-2 gap-2 max-w-lg">
                {quickActions.map((action, idx) => (
                  <button
                    key={idx}
                    onClick={() => { setInput(action); }}
                    className="flex items-center gap-2 px-3 py-2 bg-terminal-bg border border-terminal-border rounded-lg text-sm hover:bg-terminal-border transition-colors text-left"
                  >
                    <ChevronRight size={12} className="text-terminal-accent flex-shrink-0" />
                    {action}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex gap-3 ${message.role === 'user' ? 'flex-row-reverse' : ''}`}
            >
              <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                message.role === 'user' ? 'bg-terminal-accent' : 'bg-terminal-border'
              }`}>
                {message.role === 'user' ? (
                  <User size={16} className="text-white" />
                ) : (
                  <Bot size={16} />
                )}
              </div>
              <div className={`max-w-[75%] rounded-xl p-3 ${
                message.role === 'user'
                  ? 'bg-terminal-accent text-white'
                  : 'bg-terminal-card border border-terminal-border'
              }`}>
                {message.role === 'assistant' ? (
                  <div className="max-w-none text-sm">
                    {!message.isStreaming && message.content && (
                      <ToolResultRenderer content={message.content} role={message.role} toolResults={message.toolResults} />
                    )}
                    <div className="prose prose-invert prose-sm max-w-none">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {message.content || ''}
                      </ReactMarkdown>
                      {message.isStreaming && !message.content && (
                        <div className="flex items-center gap-2 text-terminal-muted">
                          <Loader2 size={14} className="animate-spin" />
                          <span>Thinking...</span>
                        </div>
                      )}
                    </div>
                  </div>
                ) : (
                  <div className="text-sm whitespace-pre-wrap">{message.content}</div>
                )}
                <div className={`text-xs mt-2 ${
                  message.role === 'user' ? 'text-white/60' : 'text-terminal-muted'
                }`}>
                  {message.timestamp.toLocaleTimeString()}
                </div>
              </div>
            </div>
          ))}

          {/* Active tools indicator */}
          {toolNames.length > 0 && (
            <div className="flex gap-2 flex-wrap">
              {toolNames.map(name => (
                <div key={name} className="flex items-center gap-2 px-3 py-1.5 bg-terminal-accent/10 border border-terminal-accent/30 rounded-full text-sm text-terminal-accent">
                  <Wrench size={12} />
                  <span>{name.replace(/_/g, ' ')}</span>
                  <Loader2 size={12} className="animate-spin" />
                </div>
              ))}
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <form onSubmit={handleSubmit} className="p-4 border-t border-terminal-border bg-terminal-card">
          <div className="flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about stocks, risk, news, fundamentals..."
              className="flex-1 px-4 py-2 bg-terminal-bg border border-terminal-border rounded-lg text-sm focus:border-terminal-accent outline-none"
              disabled={loading}
            />
            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="px-4 py-2 bg-terminal-accent text-white rounded-lg hover:bg-terminal-accent/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? <Loader2 size={18} className="animate-spin" /> : <Send size={18} />}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
