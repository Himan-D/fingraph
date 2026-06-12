import { serve } from "https://deno.land/std@0.168.0/http/server.ts"

serve(async (req) => {
  const { prices, portfolio_value, positions } = await req.json()

  if (!prices?.length) {
    return new Response(JSON.stringify({ error: "Price data required" }), { status: 400 })
  }

  const returns = prices.slice(1).map((p: number, i: number) => (p - prices[i]) / prices[i])
  const avgReturn = returns.reduce((a: number, b: number) => a + b, 0) / returns.length
  const variance = returns.reduce((a: number, b: number) => a + (b - avgReturn) ** 2, 0) / returns.length
  const stdDev = Math.sqrt(variance)
  const annualizedVol = stdDev * Math.sqrt(252)
  const sharpe = stdDev === 0 ? 0 : (avgReturn / stdDev) * Math.sqrt(252)

  const sortedReturns = [...returns].sort((a, b) => a - b)
  const var95 = sortedReturns[Math.floor(sortedReturns.length * 0.05)]
  const var99 = sortedReturns[Math.floor(sortedReturns.length * 0.01)]

  let peak = prices[0]
  let maxDrawdown = 0
  for (const price of prices) {
    peak = Math.max(peak, price)
    const dd = (peak - price) / peak * 100
    maxDrawdown = Math.max(maxDrawdown, dd)
  }

  const upsideReturns = returns.filter((r: number) => r > 0)
  const downsideReturns = returns.filter((r: number) => r < 0)
  const downsideDev = downsideReturns.length > 0
    ? Math.sqrt(downsideReturns.reduce((a: number, b: number) => a + b ** 2, 0) / returns.length)
    : 0
  const sortino = downsideDev === 0 ? 0 : (avgReturn / downsideDev) * Math.sqrt(252)

  let correlation = 0
  let beta = 0
  let alpha = 0

  const metrics = {
    sharpe_ratio: parseFloat(sharpe.toFixed(4)),
    sortino_ratio: parseFloat(sortino.toFixed(4)),
    max_drawdown: parseFloat(maxDrawdown.toFixed(2)),
    volatility: parseFloat((annualizedVol * 100).toFixed(2)),
    var_95: parseFloat((var95 * 100).toFixed(2)),
    var_99: parseFloat((var99 * 100).toFixed(2)),
    beta: parseFloat(beta.toFixed(4)),
    alpha: parseFloat((alpha * 100).toFixed(2)),
    correlation: parseFloat(correlation.toFixed(4)),
    total_return: parseFloat(((prices[prices.length - 1] - prices[0]) / prices[0] * 100).toFixed(2)),
  }

  return new Response(JSON.stringify({ metrics, risk_level: metrics.max_drawdown > 20 ? "high" : metrics.max_drawdown > 10 ? "medium" : "low" }), {
    headers: { "Content-Type": "application/json" },
  })
})
