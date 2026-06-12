import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from "https://esm.sh/@supabase/supabase-js@2"

serve(async (req) => {
  const { strategy_id, symbol, start_date, end_date, initial_capital } = await req.json()

  const supabase = createClient(
    Deno.env.get("SUPABASE_URL")!,
    Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!
  )

  const { data: strategy } = await supabase
    .from("strategies")
    .select("*")
    .eq("id", strategy_id)
    .single()

  if (!strategy) {
    return new Response(JSON.stringify({ error: "Strategy not found" }), { status: 404 })
  }

  const { data: priceData } = await supabase
    .from("market_data_cache")
    .select("*")
    .eq("symbol", symbol)
    .gte("timestamp", start_date)
    .lte("timestamp", end_date)
    .order("timestamp", { ascending: true })

  if (!priceData?.length) {
    return new Response(JSON.stringify({ error: "No price data found" }), { status: 404 })
  }

  const trades: Array<Record<string, unknown>> = []
  let capital = initial_capital
  let position = 0
  let entryPrice = 0
  let peak = capital
  const equity: Array<{ date: string; equity: number }> = []

  for (let i = 20; i < priceData.length; i++) {
    const slice = priceData.slice(i - 20, i + 1)
    const current = priceData[i]
    const price = current.close

    const rsi = computeRSI(slice.map((d: Record<string, unknown>) => d.close as number))
    const sma20 = computeSMA(slice.map((d: Record<string, unknown>) => d.close as number))
    const sma50 = i > 50
      ? computeSMA(priceData.slice(i - 50, i + 1).map((d: Record<string, unknown>) => d.close as number))
      : sma20

    const shouldBuy = rsi < 30 && price < sma20 * 0.98
    const shouldSell = rsi > 70 || (position > 0 && price > entryPrice * 1.05)

    if (shouldBuy && position === 0) {
      position = Math.floor(capital * 0.95 / price)
      entryPrice = price
      capital -= position * price
      trades.push({
        date: current.timestamp,
        type: "buy",
        price,
        quantity: position,
      })
    } else if (shouldSell && position > 0) {
      const proceeds = position * price
      const pnl = proceeds - (position * entryPrice)
      capital += proceeds
      trades.push({
        date: current.timestamp,
        type: "sell",
        price,
        quantity: position,
        pnl,
      })
      position = 0
    }

    const totalEquity = capital + position * price
    equity.push({ date: current.timestamp, equity: totalEquity })
    peak = Math.max(peak, totalEquity)
  }

  const finalValue = capital + position * priceData[priceData.length - 1].close
  const totalReturn = ((finalValue - initial_capital) / initial_capital) * 100
  const maxDrawdown = computeMaxDrawdown(equity.map((e) => e.equity))
  const sharpe = computeSharpe(equity.map((e) => e.equity))
  const winningTrades = trades.filter((t) => (t.pnl as number) > 0).length
  const winRate = trades.length > 0 ? (winningTrades / trades.length) * 100 : 0

  const result = {
    total_return: totalReturn,
    annualized_return: totalReturn * (252 / priceData.length),
    sharpe_ratio: sharpe,
    max_drawdown: maxDrawdown,
    win_rate: winRate,
    total_trades: trades.length,
    equity_curve: equity,
    trades,
  }

  await supabase.from("backtest_runs").insert({
    strategy_id,
    symbol,
    start_date,
    end_date,
    initial_capital,
    metrics: result,
    status: "completed",
  })

  return new Response(JSON.stringify(result), {
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

function computeSMA(prices: number[]): number {
  return prices.reduce((a, b) => a + b, 0) / prices.length
}

function computeMaxDrawdown(equity: number[]): number {
  let peak = equity[0]
  let maxDD = 0
  for (const val of equity) {
    peak = Math.max(peak, val)
    const dd = (peak - val) / peak * 100
    maxDD = Math.max(maxDD, dd)
  }
  return maxDD
}

function computeSharpe(equity: number[]): number {
  const returns = equity.slice(1).map((val, i) => (val - equity[i]) / equity[i])
  const avgReturn = returns.reduce((a, b) => a + b, 0) / returns.length
  const variance = returns.reduce((a, b) => a + (b - avgReturn) ** 2, 0) / returns.length
  const stdDev = Math.sqrt(variance)
  return stdDev === 0 ? 0 : (avgReturn / stdDev) * Math.sqrt(252)
}
