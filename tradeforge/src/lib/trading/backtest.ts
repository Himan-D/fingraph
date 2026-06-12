import {
  computeRSI,
  computeSMA,
  computeSharpe,
  computeMaxDrawdown,
  computeWinRate,
  computeProfitFactor,
} from "./indicators"
import type { BacktestMetrics, BacktestTrade } from "@/types"

interface BacktestConfig {
  prices: number[]
  initialCapital: number
  strategy: {
    entryCondition: (prices: number[], index: number) => boolean
    exitCondition: (prices: number[], index: number, entryPrice: number) => boolean
    positionSize: (capital: number, price: number) => number
  }
}

export function runBacktest(config: BacktestConfig): {
  metrics: BacktestMetrics
  trades: BacktestTrade[]
  equity: number[]
} {
  const { prices, initialCapital, strategy } = config
  let capital = initialCapital
  let position = 0
  let entryPrice = 0
  const trades: BacktestTrade[] = []
  const equity: number[] = [initialCapital]

  for (let i = 20; i < prices.length; i++) {
    const price = prices[i]

    if (position === 0 && strategy.entryCondition(prices, i)) {
      const qty = strategy.positionSize(capital, price)
      position = qty
      entryPrice = price
      capital -= qty * price
    } else if (position > 0 && strategy.exitCondition(prices, i, entryPrice)) {
      const proceeds = position * price
      const pnl = proceeds - position * entryPrice
      trades.push({
        entry_date: new Date().toISOString(),
        exit_date: new Date().toISOString(),
        direction: "long",
        entry_price: entryPrice,
        exit_price: price,
        quantity: position,
        pnl: parseFloat(pnl.toFixed(2)),
        return_pct: parseFloat(((price - entryPrice) / entryPrice * 100).toFixed(2)),
      })
      capital += proceeds
      position = 0
    }

    equity.push(capital + position * price)
  }

  // Close any remaining position
  if (position > 0) {
    const finalPrice = prices[prices.length - 1]
    const proceeds = position * finalPrice
    const pnl = proceeds - position * entryPrice
    trades.push({
      entry_date: new Date().toISOString(),
      exit_date: new Date().toISOString(),
      direction: "long",
      entry_price: entryPrice,
      exit_price: finalPrice,
      quantity: position,
      pnl: parseFloat(pnl.toFixed(2)),
      return_pct: parseFloat(((finalPrice - entryPrice) / entryPrice * 100).toFixed(2)),
    })
    capital += proceeds
  }

  const finalValue = capital
  const totalReturn = ((finalValue - initialCapital) / initialCapital) * 100
  const returns = equity.slice(1).map((v, i) => (v - equity[i]) / equity[i])

  const metrics: BacktestMetrics = {
    total_return: parseFloat(totalReturn.toFixed(2)),
    annualized_return: parseFloat((totalReturn * (252 / prices.length)).toFixed(2)),
    sharpe_ratio: parseFloat(computeSharpe(returns).toFixed(4)),
    sortino_ratio: 0,
    max_drawdown: parseFloat(computeMaxDrawdown(equity).toFixed(2)),
    win_rate: parseFloat(computeWinRate(trades).toFixed(1)),
    profit_factor: parseFloat(computeProfitFactor(trades).toFixed(4)),
    total_trades: trades.length,
    avg_holding_period: 0,
  }

  return { metrics, trades, equity }
}
