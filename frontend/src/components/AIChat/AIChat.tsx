import { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import { Send, Bot, User, BarChart2, TrendingUp, AlertTriangle, Lightbulb, Loader2 } from 'lucide-react'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

export default function AIChat() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [symbol, setSymbol] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    // Check for symbol in URL
    const params = new URLSearchParams(window.location.search)
    const symbolParam = params.get('symbol')
    if (symbolParam) {
      setSymbol(symbolParam)
      setMessages([
        {
          id: '1',
          role: 'assistant',
          content: `Hello! I'm your AI financial assistant. I can help you analyze stocks, explain market trends, answer questions about companies, and more. What would you like to know about ${symbolParam}?`,
          timestamp: new Date(),
        },
      ])
    } else {
      setMessages([
        {
          id: '1',
          role: 'assistant',
          content: 'Hello! I\'m your AI financial assistant. I can help you analyze stocks, explain market trends, answer questions about companies, and more. What would you like to know?',
          timestamp: new Date(),
        },
      ])
    }
  }, [])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || loading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date(),
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      const response = await axios.post('/api/v1/ai/query', {
        query: input,
        symbol: symbol,
      })

      if (response.data.success) {
        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: response.data.data?.response || response.data.data?.answer || 'I apologize, but I could not generate a response. Please try again.',
          timestamp: new Date(),
        }
        setMessages(prev => [...prev, assistantMessage])
      }
    } catch (error) {
      console.error('AI query failed:', error)
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'I apologize, but I encountered an error processing your request. Please try again.',
        timestamp: new Date(),
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  const quickActions = [
    { label: 'Analyze Stock', icon: BarChart2, action: 'Analyze RELIANCE stock' },
    { label: 'Market Trend', icon: TrendingUp, action: 'What is the current market trend?' },
    { label: 'Stock Alert', icon: AlertTriangle, action: 'What are the top gainers today?' },
    { label: 'Investment Idea', icon: Lightbulb, action: 'Suggest a good IT stock to invest' },
  ]

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-terminal-border bg-terminal-card">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-terminal-accent/20 rounded-lg">
            <Bot size={24} className="text-terminal-accent" />
          </div>
          <div>
            <h2 className="font-semibold">AI Assistant</h2>
            <p className="text-xs text-terminal-muted">Powered by OpenAI</p>
          </div>
        </div>
        
        {symbol && (
          <div className="flex items-center gap-2">
            <span className="text-sm text-terminal-muted">Analyzing:</span>
            <span className="px-3 py-1 bg-terminal-accent text-white rounded-full text-sm font-medium">
              {symbol}
            </span>
          </div>
        )}
      </div>

      {/* Quick Actions */}
      <div className="flex gap-2 p-4 border-b border-terminal-border overflow-x-auto">
        {quickActions.map((action, index) => (
          <button
            key={index}
            onClick={() => setInput(action.action)}
            className="flex items-center gap-2 px-3 py-1.5 bg-terminal-bg border border-terminal-border rounded-full text-sm whitespace-nowrap hover:bg-terminal-border transition-colors"
          >
            <action.icon size={14} />
            {action.label}
          </button>
        ))}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-auto p-4 space-y-4">
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
            <div className={`max-w-[70%] rounded-xl p-3 ${
              message.role === 'user' 
                ? 'bg-terminal-accent text-white' 
                : 'bg-terminal-card border border-terminal-border'
            }`}>
              <div className="text-sm whitespace-pre-wrap">{message.content}</div>
              <div className={`text-xs mt-2 ${
                message.role === 'user' ? 'text-white/60' : 'text-terminal-muted'
              }`}>
                {message.timestamp.toLocaleTimeString()}
              </div>
            </div>
          </div>
        ))}
        
        {loading && (
          <div className="flex gap-3">
            <div className="w-8 h-8 rounded-full bg-terminal-border flex items-center justify-center">
              <Bot size={16} />
            </div>
            <div className="bg-terminal-card border border-terminal-border rounded-xl p-3">
              <div className="flex items-center gap-2 text-terminal-muted">
                <Loader2 size={16} className="animate-spin" />
                <span className="text-sm">Thinking...</span>
              </div>
            </div>
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
            placeholder="Ask me about stocks, markets, or companies..."
            className="flex-1 px-4 py-2 bg-terminal-bg border border-terminal-border rounded-lg text-sm focus:border-terminal-accent"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="px-4 py-2 bg-terminal-accent text-white rounded-lg hover:bg-terminal-accent/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Send size={18} />
          </button>
        </div>
      </form>
    </div>
  )
}
