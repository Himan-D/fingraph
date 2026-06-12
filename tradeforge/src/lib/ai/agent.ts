import { TOOL_DEFINITIONS, executeToolCall } from "./tools"
import type { AIAgentMessage, ToolCall } from "@/types"

type AgentOptions = {
  apiKey: string
  model?: string
  systemPrompt?: string
}

const DEFAULT_SYSTEM_PROMPT = `You are TradeForge AI, a professional trading copilot. You help traders analyze markets, build strategies, and make informed decisions.

You have access to tools that can:
- Get live market data and technical indicators
- Analyze fundamentals and news sentiment
- Generate and backtest trading strategies
- Optimize portfolios
- Explain market conditions
- Suggest trades with reasoning

Always:
1. Use data from your tools to support your analysis
2. Explain your reasoning clearly
3. Include risk warnings with trade suggestions
4. Use markdown formatting for readability
5. Show relevant numbers and metrics`

export class Agent {
  private apiKey: string
  private model: string
  private systemPrompt: string
  private messages: AIAgentMessage[] = []

  constructor(options: AgentOptions) {
    this.apiKey = options.apiKey
    this.model = options.model || "gpt-4"
    this.systemPrompt = options.systemPrompt || DEFAULT_SYSTEM_PROMPT
  }

  async send(message: string, onChunk?: (chunk: string) => void): Promise<string> {
    this.messages.push({ id: crypto.randomUUID(), role: "user", content: message, created_at: new Date().toISOString() })

    const response = await this.callLLM()
    const assistantMessage = response.choices[0].message

    if (assistantMessage.tool_calls) {
      const toolResults = await Promise.all(
        assistantMessage.tool_calls.map(async (tc: ToolCall) => {
          const result = await executeToolCall(tc)
          return result
        })
      )

      this.messages.push({
        id: crypto.randomUUID(),
        role: "assistant",
        content: assistantMessage.content || "",
        tool_calls: assistantMessage.tool_calls,
        created_at: new Date().toISOString(),
      })

      for (const result of toolResults) {
        this.messages.push({
          id: crypto.randomUUID(),
          role: "tool",
          content: JSON.stringify(result.result),
          tool_results: [result],
          created_at: new Date().toISOString(),
        })
      }

      const finalResponse = await this.callLLM()
      const finalContent = finalResponse.choices[0].message.content || ""

      this.messages.push({
        id: crypto.randomUUID(),
        role: "assistant",
        content: finalContent,
        created_at: new Date().toISOString(),
      })

      return finalContent
    }

    const content = assistantMessage.content || ""
    this.messages.push({
      id: crypto.randomUUID(),
      role: "assistant",
      content,
      created_at: new Date().toISOString(),
    })

    return content
  }

  private async callLLM() {
    const res = await fetch("https://api.openai.com/v1/chat/completions", {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${this.apiKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        model: this.model,
        messages: [
          { role: "system", content: this.systemPrompt },
          ...this.messages.map((m) => ({
            role: m.role === "tool" ? "tool" : m.role,
            content: m.role === "tool" ? m.content : m.content,
            tool_calls: m.tool_calls,
          })),
        ],
        tools: TOOL_DEFINITIONS.map((t) => ({
          type: "function",
          function: {
            name: t.name,
            description: t.description,
            parameters: t.parameters,
          },
        })),
        tool_choice: "auto",
      }),
    })

    return res.json()
  }

  getConversationHistory(): AIAgentMessage[] {
    return [...this.messages]
  }

  clear() {
    this.messages = []
  }
}
