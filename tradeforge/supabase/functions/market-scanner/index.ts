import { serve } from "https://deno.land/std@0.168.0/http/server.ts"

const ALPACA_BASE = "https://data.alpaca.markets/v2"

const MARKET_INDICES = ["SPY", "QQQ", "DIA", "IWM"]
const SECTOR_ETFS = ["XLF", "XLK", "XLE", "XLV", "XLI", "XLP", "XLY", "XLU", "XLB", "XLRE"]

serve(async (req) => {
  const { min_price = 5, max_price = 10000, min_volume = 100000, min_market_cap = 1e9 } = await req.json()

  const apiKey = Deno.env.get("ALPACA_API_KEY")
  const secretKey = Deno.env.get("ALPACA_SECRET_KEY")

  const symbols = [...MARKET_INDICES, ...SECTOR_ETFS]

  const results = []

  for (const symbol of symbols) {
    try {
      const res = await fetch(
        `${ALPACA_BASE}/stocks/${symbol}/quotes/latest?feed=iex`,
        { headers: { "APCA-API-KEY-ID": apiKey!, "APCA-API-SECRET-KEY": secretKey! } }
      )
      const quote = await res.json()

      const barsRes = await fetch(
        `${ALPACA_BASE}/stocks/${symbol}/bars?timeframe=1Day&limit=30`,
        { headers: { "APCA-API-KEY-ID": apiKey!, "APCA-API-SECRET-KEY": secretKey! } }
      )
      const bars = await barsRes.json()

      if (!quote.quote || !bars.bars?.length) continue

      const price = quote.quote.ap || quote.quote.bp || 0
      const lastBar = bars.bars[bars.bars.length - 1]
      const prevBar = bars.bars[bars.bars.length - 2]
      const change = lastBar && prevBar ? ((lastBar.c - prevBar.c) / prevBar.c) * 100 : 0
      const volume = lastBar?.v || 0
      const avgVolume = bars.bars.slice(-20).reduce((a: number, b: Record<string, unknown>) => a + (b.v as number), 0) / 20
      const volumeRatio = avgVolume > 0 ? volume / avgVolume : 0

      const prices = bars.bars.map((b: Record<string, unknown>) => b.c as number)
      const rsi = computeRSI(prices)
      const sma20 = prices.slice(-20).reduce((a: number, b: number) => a + b, 0) / 20
      const sma50 = prices.length >= 50
        ? prices.slice(-50).reduce((a: number, b: number) => a + b, 0) / 50
        : sma20

      let signal = "neutral"
      if (rsi > 70) signal = "overbought"
      else if (rsi < 30) signal = "oversold"
      else if (change > 2 && volumeRatio > 1.5) signal = "bullish"
      else if (change < -2) signal = "bearish"

      results.push({
        symbol,
        price,
        change: parseFloat(change.toFixed(2)),
        volume: parseFloat((volume / 1e6).toFixed(1)),
        avg_volume: parseFloat((avgVolume / 1e6).toFixed(1)),
        volume_ratio: parseFloat(volumeRatio.toFixed(2)),
        rsi: parseFloat(rsi.toFixed(0)),
        sma20: parseFloat(sma20.toFixed(2)),
        sma50: parseFloat(sma50.toFixed(2)),
        signal,
      })
    } catch {
      continue
    }
  }

  return new Response(JSON.stringify({ results, total: results.length }), {
    headers: { "Content-Type": "application/json" },
  })
})

function computeRSI(prices: number[], period = 14): number {
  if (prices.length < period + 1) return 50
  const changes = prices.slice(-period - 1).map((p, i, arr) => i === 0 ? 0 : p - arr[i - 1])
  const gains = changes.filter((c) => c > 0).reduce((a, b) => a + b, 0) / period
  const losses = changes.filter((c) => c < 0).reduce((a, b) => a + Math.abs(b), 0) / period
  if (losses === 0) return 100
  const rs = gains / losses
  return 100 - 100 / (1 + rs)
}
