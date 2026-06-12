"use client"

import { useState, useRef, useEffect } from "react"
import { PageHeader } from "@/components/ui/page-header"
import { GlassCard } from "@/components/ui/glass-card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import {
  BotMessageSquare,
  Send,
  TrendingUp,
  TrendingDown,
  LineChart,
  Sparkles,
  Lightbulb,
  Plus,
  Search,
  BarChart3,
} from "lucide-react"
import { formatTimeAgo } from "@/lib/utils"

type Message = {
  id: string
  role: "user" | "assistant"
  content: string
  timestamp: Date
}

const suggestions = [
  "Analyze AAPL stock",
  "Find momentum stocks",
  "Explain market conditions",
  "Build a mean reversion strategy",
  "Optimize my portfolio",
  "What's the market outlook?",
]

const sampleMessages: Message[] = [
  {
    id: "1",
    role: "assistant",
    content:
      "Hello! I'm your AI trading copilot. I can analyze stocks, build strategies, backtest ideas, and monitor markets. What would you like to explore today?",
    timestamp: new Date(Date.now() - 3600000),
  },
]

export default function CopilotPage() {
  const [messages, setMessages] = useState<Message[]>(sampleMessages)
  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages])

  const handleSend = async () => {
    if (!input.trim() || loading) return

    const userMsg: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content: input,
      timestamp: new Date(),
    }
    setMessages((prev) => [...prev, userMsg])
    setInput("")
    setLoading(true)

    setTimeout(() => {
      const responseMap: Record<string, string> = {
        analyze: "**AAPL Analysis**\n\n**Price:** $198.45 (+1.2%)\n**Market Cap:** $3.02T\n**P/E:** 28.4\n**EPS:** $6.98\n\n**Technical Indicators:**\n- RSI(14): 62 — Neutral\n- MACD: Bullish crossover\n- SMA(50): $192.30\n- SMA(200): $182.15\n\n**AI Verdict:** Apple shows strong technical momentum with bullish MACD signal. Support at $195, resistance at $205. The upcoming earnings (Jul 25) could be a catalyst. Consider accumulating on dips.",
        momentum: "**Momentum Stocks 📈**\n\nBased on screening 500+ stocks, here are the top momentum picks:\n\n| Symbol | Price | 1W Return | Volume |\n|--------|-------|-----------|--------|\n| NVDA | $892.50 | +8.4% | 2.5x avg |\n| META | $512.60 | +5.2% | 1.8x avg |\n| AMZN | $188.75 | +3.9% | 1.4x avg |\n| SOL | $178.90 | +12.5% | 3.2x avg |\n\n**Top pick:** NVDA — Strong volume confirmation and institutional accumulation.",
        strategy: "**Mean Reversion Strategy**\n\n```python\ndef should_buy(data):\n    rsi = compute_rsi(data, 14)\n    bb_lower = compute_bollinger_lower(data, 20)\n    \n    return (\n        rsi < 30 and\n        data.close < bb_lower and\n        data.volume > average_volume(data, 20) * 1.5\n    )\n\ndef should_sell(data):\n    rsi = compute_rsi(data, 14)\n    bb_upper = compute_bollinger_upper(data, 20)\n    \n    return rsi > 70 and data.close > bb_upper\n```\n\n**Parameters:**\n- RSI oversold threshold: 30\n- RSI overbought threshold: 70\n- BB period: 20\n- Min volume ratio: 1.5x\n\nWant me to backtest this strategy?",
        market: "**Market Conditions Summary**\n\n**Overall:** Bullish 🟢\n- S&P 500: +0.8% (5,432)\n- VIX: 14.2 (low volatility)\n- 10Y Yield: 4.28%\n\n**Sector Performance:**\n- Technology: +1.2% (leading)\n- Healthcare: +0.5%\n- Energy: -0.8%\n- Financials: +0.3%\n\n**Key Themes:**\n1. AI rally continues — NVDA leading\n2. Rate cut expectations supporting growth\n3. Earnings season showing resilience\n\n**Risk Factors:**\n- Geopolitical tensions\n- Inflation data this week",
      }

      let response = responseMap["default"] || "I'll analyze that and get back to you with insights."

      for (const [key, val] of Object.entries(responseMap)) {
        if (input.toLowerCase().includes(key)) {
          response = val
          break
        }
      }

      const assistantMsg: Message = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: response,
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, assistantMsg])
      setLoading(false)
    }, 1500)
  }

  return (
    <div className="flex h-[calc(100vh-7rem)] animate-fade-in">
      <div className="flex-1 flex flex-col">
        <PageHeader
          title="AI Copilot"
          description="Your AI trading assistant"
          className="mb-4"
        />

        <GlassCard className="flex-1 flex flex-col p-0 overflow-hidden">
          <ScrollArea className="flex-1 p-6" ref={scrollRef}>
            <div className="space-y-6">
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex gap-4 ${
                    msg.role === "user" ? "flex-row-reverse" : ""
                  }`}
                >
                  <Avatar className="h-8 w-8 shrink-0">
                    <AvatarFallback
                      className={
                        msg.role === "assistant"
                          ? "bg-primary/10 text-primary"
                          : "bg-muted text-foreground"
                      }
                    >
                      {msg.role === "assistant" ? "AI" : "U"}
                    </AvatarFallback>
                  </Avatar>
                  <div
                    className={`max-w-[80%] ${
                      msg.role === "user"
                        ? "bg-primary/10 rounded-2xl rounded-tr-sm px-4 py-3"
                        : "space-y-2"
                    }`}
                  >
                    <div className="prose prose-sm prose-invert max-w-none leading-relaxed whitespace-pre-wrap">
                      {msg.content}
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {formatTimeAgo(msg.timestamp)}
                    </p>
                  </div>
                </div>
              ))}
              {loading && (
                <div className="flex gap-4">
                  <Avatar className="h-8 w-8">
                    <AvatarFallback className="bg-primary/10 text-primary">
                      AI
                    </AvatarFallback>
                  </Avatar>
                  <div className="flex items-center gap-1.5 py-2">
                    <span className="h-2 w-2 rounded-full bg-primary animate-bounce" />
                    <span
                      className="h-2 w-2 rounded-full bg-primary animate-bounce"
                      style={{ animationDelay: "0.1s" }}
                    />
                    <span
                      className="h-2 w-2 rounded-full bg-primary animate-bounce"
                      style={{ animationDelay: "0.2s" }}
                    />
                  </div>
                </div>
              )}
            </div>
          </ScrollArea>

          {/* Suggestions */}
          {messages.length <= 2 && (
            <div className="px-6 pb-4">
              <div className="flex flex-wrap gap-2">
                {suggestions.map((s) => (
                  <button
                    key={s}
                    onClick={() => {
                      setInput(s)
                      handleSend()
                    }}
                    className="inline-flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-full border border-border bg-muted/30 text-muted-foreground hover:bg-muted/50 hover:text-foreground transition-colors"
                  >
                    <Sparkles className="h-3 w-3" />
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Input */}
          <div className="border-t border-border p-4">
            <form
              onSubmit={(e) => {
                e.preventDefault()
                handleSend()
              }}
              className="flex gap-3"
            >
              <Input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask me anything about trading..."
                className="flex-1 h-11"
                disabled={loading}
              />
              <Button
                type="submit"
                size="icon"
                className="h-11 w-11 shrink-0"
                disabled={loading || !input.trim()}
              >
                <Send className="h-4 w-4" />
              </Button>
            </form>
          </div>
        </GlassCard>
      </div>
    </div>
  )
}
