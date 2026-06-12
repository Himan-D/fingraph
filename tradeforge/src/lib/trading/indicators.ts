export function computeRSI(prices: number[], period = 14): number {
  if (prices.length < period + 1) return 50
  const changes = prices.slice(-period - 1).map((p, i, arr) => (i === 0 ? 0 : p - arr[i - 1]))
  const avgGain = changes.filter((c) => c > 0).reduce((s, v) => s + v, 0) / period
  const avgLoss = changes.filter((c) => c < 0).reduce((s, v) => s + Math.abs(v), 0) / period
  if (avgLoss === 0) return 100
  const rs = avgGain / avgLoss
  return 100 - 100 / (1 + rs)
}

export function computeSMA(prices: number[], period: number): number[] {
  const result: number[] = []
  for (let i = period - 1; i < prices.length; i++) {
    result.push(prices.slice(i - period + 1, i + 1).reduce((s, v) => s + v, 0) / period)
  }
  return result
}

export function computeEMA(prices: number[], period: number): number[] {
  const multiplier = 2 / (period + 1)
  const result: number[] = [prices.slice(0, period).reduce((s, v) => s + v, 0) / period]
  for (let i = period; i < prices.length; i++) {
    result.push((prices[i] - result[result.length - 1]) * multiplier + result[result.length - 1])
  }
  return result
}

export function computeMACD(prices: number[]): {
  macd: number[]
  signal: number[]
  histogram: number[]
} {
  const ema12 = computeEMA(prices, 12)
  const ema26 = computeEMA(prices, 26)
  const offset = ema12.length - ema26.length
  const macdLine = ema12.slice(offset).map((v, i) => v - ema26[i])
  const signal = computeEMA(macdLine, 9)
  const histogram = macdLine.slice(-signal.length).map((v, i) => v - signal[i])
  return { macd: macdLine, signal, histogram }
}

export function computeBollingerBands(
  prices: number[],
  period = 20,
  std = 2
): { upper: number[]; middle: number[]; lower: number[] } {
  const middle = computeSMA(prices, period)
  const upper: number[] = []
  const lower: number[] = []
  for (let i = 0; i < middle.length; i++) {
    const slice = prices.slice(i, i + period)
    const mean = middle[i]
    const variance = slice.reduce((s, v) => s + (v - mean) ** 2, 0) / period
    const sd = Math.sqrt(variance)
    upper.push(mean + sd * std)
    lower.push(mean - sd * std)
  }
  return { upper, middle, lower }
}

export function computeSharpe(returns: number[], riskFreeRate = 0.05): number {
  const avgReturn = returns.reduce((s, v) => s + v, 0) / returns.length
  const excess = avgReturn - riskFreeRate / 252
  const variance = returns.reduce((s, v) => s + (v - avgReturn) ** 2, 0) / returns.length
  const stdDev = Math.sqrt(variance)
  return stdDev === 0 ? 0 : (excess / stdDev) * Math.sqrt(252)
}

export function computeMaxDrawdown(prices: number[]): number {
  let peak = prices[0]
  let maxDD = 0
  for (const price of prices) {
    peak = Math.max(peak, price)
    const dd = (peak - price) / peak
    maxDD = Math.max(maxDD, dd)
  }
  return maxDD * 100
}

export function computeWinRate(trades: { pnl: number }[]): number {
  if (trades.length === 0) return 0
  const wins = trades.filter((t) => t.pnl > 0).length
  return (wins / trades.length) * 100
}

export function computeProfitFactor(trades: { pnl: number }[]): number {
  const grossProfit = trades.filter((t) => t.pnl > 0).reduce((s, t) => s + t.pnl, 0)
  const grossLoss = Math.abs(trades.filter((t) => t.pnl < 0).reduce((s, t) => s + t.pnl, 0))
  return grossLoss === 0 ? Infinity : grossProfit / grossLoss
}
