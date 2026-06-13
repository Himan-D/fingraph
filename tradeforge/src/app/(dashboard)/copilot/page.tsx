"use client"

import { useState, useRef, useEffect, useCallback } from "react"
import { PageHeader } from "@/components/ui/page-header"
import { GlassCard } from "@/components/ui/glass-card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Send, Sparkles } from "lucide-react"
import { formatTimeAgo } from "@/lib/utils"
import { streamChat, parseSSELines, type SSEEvent } from "@/lib/api"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"

type Message = {
  id: string
  role: "user" | "assistant"
  content: string
  timestamp: Date
  toolCalls?: SSEEvent[]
}

const suggestions = [
  "Analyze RELIANCE stock",
  "Compare TCS vs INFY",
  "Run risk analysis on HDFCBANK",
  "Show top gainers today",
  "What's NIFTY doing?",
  "Get sentiment on ADANI PORTS",
]

const sampleMessages: Message[] = [
  {
    id: "1",
    role: "assistant",
    content:
      "Hello! I'm your AI trading copilot powered by FinGraph. I can analyze Indian stocks, compare companies, run risk analysis, backtest strategies, and much more. What would you like to explore?",
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

  const handleSend = useCallback(
    async (overrideInput?: string) => {
      const msgText = overrideInput || input
      if (!msgText.trim() || loading) return

      const userMsg: Message = {
        id: crypto.randomUUID(),
        role: "user",
        content: msgText,
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, userMsg])
      setInput("")
      setLoading(true)

      const assistantId = crypto.randomUUID()
      setMessages((prev) => [
        ...prev,
        { id: assistantId, role: "assistant", content: "", timestamp: new Date(), toolCalls: [] },
      ])

      try {
        const body = await streamChat(msgText)
        const reader = body.getReader()
        const decoder = new TextDecoder()
        let buffer = ""
        let allLines: string[] = []

        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          buffer += decoder.decode(value, { stream: true })
          const lines = buffer.split("\n")
          buffer = lines.pop() || ""

          const newLines = lines.filter((l) => l.startsWith("data: "))
          allLines = [...allLines, ...newLines]

          const { events, fullContent } = parseSSELines(allLines)

          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId
                ? { ...m, content: fullContent || "Analyzing...", toolCalls: events }
                : m,
            ),
          )
        }

        if (buffer.startsWith("data: ")) {
          allLines.push(buffer)
        }
        const final = parseSSELines(allLines)

        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId
              ? {
                  ...m,
                  content: final.finalContent || final.fullContent || "Analysis complete.",
                  toolCalls: final.events,
                }
              : m,
          ),
        )
      } catch {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId
              ? { ...m, content: "Sorry, I couldn't process your request. Please try again." }
              : m,
          ),
        )
      } finally {
        setLoading(false)
      }
    },
    [input, loading],
  )

  return (
    <div className="flex h-[calc(100vh-7rem)] animate-fade-in">
      <div className="flex-1 flex flex-col">
        <PageHeader
          title="AI Copilot"
          description="Your AI trading assistant — powered by FinGraph"
          className="mb-4"
        />

        <GlassCard className="flex-1 flex flex-col p-0 overflow-hidden">
          <ScrollArea className="flex-1 p-6" ref={scrollRef}>
            <div className="space-y-6">
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex gap-4 ${msg.role === "user" ? "flex-row-reverse" : ""}`}
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
                    {/* Tool call indicators */}
                    {msg.toolCalls && msg.toolCalls.length > 0 && msg.role === "assistant" && (
                      <div className="flex flex-wrap gap-1.5 mb-2">
                        {msg.toolCalls
                          .filter((e) => e.type === "tool_start")
                          .map((e, i) => (
                            <span
                              key={i}
                              className="inline-flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full border border-border bg-muted/30 text-muted-foreground"
                            >
                              <Sparkles className="h-2.5 w-2.5" />
                              {e.tool}
                            </span>
                          ))}
                      </div>
                    )}
                    {msg.role === "assistant" ? (
                      <div className="prose prose-sm prose-invert max-w-none leading-relaxed">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                          {msg.content}
                        </ReactMarkdown>
                      </div>
                    ) : (
                      <div className="text-sm whitespace-pre-wrap">{msg.content}</div>
                    )}
                    <p className="text-xs text-muted-foreground">{formatTimeAgo(msg.timestamp)}</p>
                  </div>
                </div>
              ))}
              {loading && messages[messages.length - 1]?.content === "" && (
                <div className="flex gap-4">
                  <Avatar className="h-8 w-8">
                    <AvatarFallback className="bg-primary/10 text-primary">AI</AvatarFallback>
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
                    onClick={() => handleSend(s)}
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
                placeholder="Ask me anything about Indian markets..."
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
