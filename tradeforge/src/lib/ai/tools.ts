import type { ToolCall, ToolResult } from "@/types"

export type ToolDefinition = {
  name: string
  description: string
  parameters: Record<string, unknown>
  execute: (args: Record<string, unknown>) => Promise<unknown>
}

export const TOOL_DEFINITIONS: ToolDefinition[] = [
  {
    name: "get_market_data",
    description: "Get current market data for a symbol (price, volume, OHLCV)",
    parameters: {
      type: "object",
      properties: {
        symbol: { type: "string", description: "Stock symbol (e.g., AAPL)" },
        timeframe: { type: "string", enum: ["1D", "1W", "1M", "1Y"] },
      },
      required: ["symbol"],
    },
    execute: async (args) => {
      const { symbol, timeframe = "1M" } = args
      return { symbol, price: 198.45, change: 1.2, volume: 22400000, high: 199.5, low: 197.8, open: 198.1, close: 198.45 }
    },
  },
  {
    name: "analyze_technical",
    description: "Calculate technical indicators for a symbol",
    parameters: {
      type: "object",
      properties: {
        symbol: { type: "string" },
        indicators: { type: "array", items: { type: "string" } },
      },
      required: ["symbol"],
    },
    execute: async (args) => {
      const { symbol } = args
      return {
        symbol,
        rsi: 62,
        macd: { value: 2.4, signal: 1.8, histogram: 0.6 },
        sma20: 192.3,
        sma50: 182.15,
        bb: { upper: 205.2, middle: 192.3, lower: 179.4 },
      }
    },
  },
  {
    name: "analyze_fundamental",
    description: "Get fundamental data for a company",
    parameters: {
      type: "object",
      properties: { symbol: { type: "string" } },
      required: ["symbol"],
    },
    execute: async (args) => {
      const { symbol } = args
      return { symbol, pe: 28.4, eps: 6.98, revenue: "383.3B", profit: "97.0B", marketCap: "3.02T" }
    },
  },
  {
    name: "generate_strategy",
    description: "Generate a trading strategy from natural language description",
    parameters: {
      type: "object",
      properties: {
        description: { type: "string", description: "Strategy description in plain English" },
        symbol: { type: "string" },
      },
      required: ["description"],
    },
    execute: async (args) => {
      return {
        code: `def should_enter(data):\n    rsi = compute_rsi(data.close, 14)\n    return rsi < 30\n\ndef should_exit(data):\n    rsi = compute_rsi(data.close, 14)\n    return rsi > 70`,
      }
    },
  },
  {
    name: "run_backtest",
    description: "Run a backtest for a strategy",
    parameters: {
      type: "object",
      properties: {
        strategy_code: { type: "string" },
        symbol: { type: "string" },
        start_date: { type: "string" },
        end_date: { type: "string" },
        initial_capital: { type: "number" },
      },
      required: ["strategy_code", "symbol"],
    },
    execute: async () => {
      return {
        totalReturn: 12.4,
        sharpeRatio: 1.84,
        maxDrawdown: -8.4,
        winRate: 62,
        totalTrades: 47,
      }
    },
  },
  {
    name: "optimize_portfolio",
    description: "Run mean-variance portfolio optimization",
    parameters: {
      type: "object",
      properties: {
        symbols: { type: "array", items: { type: "string" } },
        risk_tolerance: { type: "string", enum: ["low", "medium", "high"] },
      },
      required: ["symbols"],
    },
    execute: async () => {
      return {
        allocations: { AAPL: 0.25, MSFT: 0.2, NVDA: 0.15, GOOGL: 0.15, AMZN: 0.1, cash: 0.15 },
        expectedReturn: 14.2,
        expectedVolatility: 18.5,
        sharpeRatio: 1.84,
      }
    },
  },
  {
    name: "get_news_sentiment",
    description: "Get aggregated news and sentiment for a symbol",
    parameters: {
      type: "object",
      properties: { symbol: { type: "string" }, limit: { type: "number" } },
      required: ["symbol"],
    },
    execute: async () => {
      return {
        overallSentiment: "positive",
        score: 0.72,
        articles: [
          { headline: "Apple Reports Record Quarterly Revenue", source: "Reuters", sentiment: "positive" },
          { headline: "Apple's Services Business Continues to Grow", source: "Bloomberg", sentiment: "positive" },
        ],
      }
    },
  },
  {
    name: "explain_market",
    description: "Get explanation of current market conditions",
    parameters: {
      type: "object",
      properties: { sector: { type: "string" } },
    },
    execute: async () => {
      return {
        overall: "Bullish",
        sp500: 5432,
        vix: 14.2,
        tenYearYield: 4.28,
        summary: "Markets are showing strength driven by AI sector momentum and expected rate cuts.",
        risks: ["Geopolitical tensions", "Inflation data"],
      }
    },
  },
  {
    name: "suggest_trades",
    description: "Get AI-generated trade suggestions with reasoning",
    parameters: {
      type: "object",
      properties: {
        symbols: { type: "array", items: { type: "string" } },
        strategy_type: { type: "string", enum: ["momentum", "mean_reversion", "breakout"] },
      },
      required: ["symbols"],
    },
    execute: async () => {
      return {
        suggestions: [
          { symbol: "NVDA", action: "buy", confidence: 85, reason: "Strong momentum with volume confirmation" },
          { symbol: "AAPL", action: "hold", confidence: 70, reason: "Waiting for earnings catalyst" },
          { symbol: "TSLA", action: "sell", confidence: 60, reason: "Resistance at $250, weakening momentum" },
        ],
      }
    },
  },
]

export async function executeToolCall(toolCall: ToolCall): Promise<ToolResult> {
  const tool = TOOL_DEFINITIONS.find((t) => t.name === toolCall.name)
  if (!tool) {
    return { tool_call_id: toolCall.id, result: { error: `Unknown tool: ${toolCall.name}` } }
  }
  try {
    const result = await tool.execute(toolCall.args)
    return { tool_call_id: toolCall.id, result }
  } catch (error) {
    return { tool_call_id: toolCall.id, result: { error: String(error) } }
  }
}
