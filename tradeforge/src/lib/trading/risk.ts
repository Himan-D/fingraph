export function calculatePositionSize(
  capital: number,
  price: number,
  stopLossPct: number,
  riskPerTrade: number
): number {
  const riskAmount = capital * (riskPerTrade / 100)
  const stopDistance = price * (stopLossPct / 100)
  return Math.floor(riskAmount / stopDistance)
}

export function calculateKellyFraction(
  winRate: number,
  avgWin: number,
  avgLoss: number
): number {
  if (avgLoss === 0) return 0
  const b = avgWin / avgLoss
  const p = winRate / 100
  const q = 1 - p
  return Math.max(0, (p * b - q) / b)
}

export function calculateVaR(
  returns: number[],
  confidence = 0.95
): number {
  const sorted = [...returns].sort((a, b) => a - b)
  const index = Math.floor(sorted.length * (1 - confidence))
  return sorted[index] * 100
}

export function calculateBeta(
  assetReturns: number[],
  marketReturns: number[]
): number {
  if (assetReturns.length !== marketReturns.length || assetReturns.length === 0) return 1

  const assetMean = assetReturns.reduce((s, v) => s + v, 0) / assetReturns.length
  const marketMean = marketReturns.reduce((s, v) => s + v, 0) / marketReturns.length

  let covariance = 0
  let marketVariance = 0

  for (let i = 0; i < assetReturns.length; i++) {
    covariance += (assetReturns[i] - assetMean) * (marketReturns[i] - marketMean)
    marketVariance += (marketReturns[i] - marketMean) ** 2
  }

  covariance /= assetReturns.length
  marketVariance /= assetReturns.length

  return marketVariance === 0 ? 1 : covariance / marketVariance
}

export function calculateCorrelation(
  returns1: number[],
  returns2: number[]
): number {
  if (returns1.length !== returns2.length || returns1.length === 0) return 0

  const mean1 = returns1.reduce((s, v) => s + v, 0) / returns1.length
  const mean2 = returns2.reduce((s, v) => s + v, 0) / returns2.length

  let cov = 0
  let var1 = 0
  let var2 = 0

  for (let i = 0; i < returns1.length; i++) {
    const d1 = returns1[i] - mean1
    const d2 = returns2[i] - mean2
    cov += d1 * d2
    var1 += d1 * d1
    var2 += d2 * d2
  }

  const denom = Math.sqrt(var1 * var2)
  return denom === 0 ? 0 : cov / denom
}

export function calculatePortfolioRisk(positions: {
  value: number
  volatility: number
}[]): number {
  const totalValue = positions.reduce((s, p) => s + p.value, 0)
  if (totalValue === 0) return 0

  let portfolioVariance = 0
  for (let i = 0; i < positions.length; i++) {
    const wi = positions[i].value / totalValue
    for (let j = 0; j < positions.length; j++) {
      const wj = positions[j].value / totalValue
      portfolioVariance += wi * wj * positions[i].volatility * positions[j].volatility
    }
  }

  return Math.sqrt(portfolioVariance) * Math.sqrt(252) * 100
}
