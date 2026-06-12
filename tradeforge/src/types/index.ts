export type User = {
  id: string
  email: string
  name: string | null
  avatar_url: string | null
  plan: 'free' | 'pro' | 'enterprise'
  created_at: string
}

export type BrokerConnection = {
  id: string
  user_id: string
  broker: 'alpaca' | 'binance' | 'polygon'
  label: string
  is_active: boolean
  created_at: string
}

export type Strategy = {
  id: string
  user_id: string
  name: string
  description: string | null
  type: 'technical' | 'fundamental' | 'ml' | 'custom'
  code: string | null
  rules: StrategyRule[]
  config: Record<string, unknown>
  is_active: boolean
  created_at: string
  updated_at: string
}

export type StrategyRule = {
  id: string
  condition: string
  action: 'buy' | 'sell' | 'short' | 'cover'
  params: Record<string, unknown>
}

export type BacktestRun = {
  id: string
  strategy_id: string
  symbol: string
  start_date: string
  end_date: string
  initial_capital: number
  metrics: BacktestMetrics
  trades: BacktestTrade[]
  status: 'running' | 'completed' | 'failed'
  created_at: string
}

export type BacktestMetrics = {
  total_return: number
  annualized_return: number
  sharpe_ratio: number
  sortino_ratio: number
  max_drawdown: number
  win_rate: number
  profit_factor: number
  total_trades: number
  avg_holding_period: number
}

export type BacktestTrade = {
  entry_date: string
  exit_date: string
  direction: 'long' | 'short'
  entry_price: number
  exit_price: number
  quantity: number
  pnl: number
  return_pct: number
}

export type Bot = {
  id: string
  user_id: string
  name: string
  strategy_id: string
  symbol: string
  status: 'running' | 'stopped' | 'error' | 'paused'
  config: BotConfig
  stats: BotStats
  created_at: string
}

export type BotConfig = {
  position_size: number
  max_drawdown: number
  daily_loss_limit: number
  leverage: number
  trading_hours: { start: string; end: string }
}

export type BotStats = {
  total_pnl: number
  daily_pnl: number
  win_rate: number
  total_trades: number
  open_positions: number
}

export type Position = {
  id: string
  bot_id: string | null
  symbol: string
  direction: 'long' | 'short'
  quantity: number
  entry_price: number
  current_price: number
  pnl: number
  pnl_pct: number
  opened_at: string
  closed_at: string | null
}

export type Portfolio = {
  total_value: number
  cash: number
  invested: number
  day_pnl: number
  total_pnl: number
  day_pnl_pct: number
  total_pnl_pct: number
  holdings: PortfolioHolding[]
}

export type PortfolioHolding = {
  symbol: string
  name: string
  quantity: number
  avg_price: number
  current_price: number
  value: number
  allocation_pct: number
  pnl: number
  pnl_pct: number
}

export type Alert = {
  id: string
  user_id: string
  name: string
  type: 'price' | 'technical' | 'news' | 'portfolio'
  symbol: string | null
  condition: AlertCondition
  channel: ('email' | 'sms' | 'push')[]
  is_active: boolean
  last_triggered: string | null
  created_at: string
}

export type AlertCondition = {
  field: string
  operator: 'above' | 'below' | 'crosses_above' | 'crosses_below' | 'equals'
  value: number
}

export type JournalEntry = {
  id: string
  user_id: string
  symbol: string
  title: string
  notes: string
  emotions: string[]
  screenshots: string[]
  tags: string[]
  pnl: number | null
  lesson: string | null
  created_at: string
}

export type MarketData = {
  symbol: string
  name: string
  price: number
  change: number
  change_pct: number
  volume: number
  high: number
  low: number
  open: number
  close: number
  market_cap: number | null
}

export type TickerItem = {
  symbol: string
  price: number
  change_pct: number
}

export type AIAgentMessage = {
  id: string
  role: 'user' | 'assistant' | 'tool'
  content: string
  tool_calls?: ToolCall[]
  tool_results?: ToolResult[]
  created_at: string
}

export type ToolCall = {
  name: string
  args: Record<string, unknown>
  id: string
}

export type ToolResult = {
  tool_call_id: string
  result: unknown
}

export type Conversation = {
  id: string
  title: string
  created_at: string
}

export type Subscription = {
  id: string
  plan: 'free' | 'pro' | 'enterprise'
  status: 'active' | 'canceled' | 'past_due'
  current_period_end: string
  stripe_subscription_id: string | null
}
