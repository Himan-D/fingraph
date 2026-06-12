"use client"

import { useState } from "react"
import { PageHeader } from "@/components/ui/page-header"
import { GlassCard, GlassCardHeader, GlassCardTitle } from "@/components/ui/glass-card"
import { StatCard } from "@/components/ui/stat-card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  LineChart,
  Line,
} from "recharts"
import {
  Play,
  History,
  Download,
  BarChart3,
  TrendingUp,
  TrendingDown,
  RefreshCw,
} from "lucide-react"

const equityCurve = Array.from({ length: 252 }, (_, i) => ({
  day: i + 1,
  equity: 100000 + (Math.random() - 0.48) * 30000 + i * 200,
  drawdown: Math.random() * -5,
}))

const monthlyReturns = [
  { month: "Jan", return: 3.2 },
  { month: "Feb", return: -1.8 },
  { month: "Mar", return: 4.5 },
  { month: "Apr", return: 2.1 },
  { month: "May", return: -0.5 },
  { month: "Jun", return: 5.2 },
  { month: "Jul", return: 3.8 },
  { month: "Aug", return: -2.1 },
  { month: "Sep", return: 1.5 },
  { month: "Oct", return: 4.2 },
  { month: "Nov", return: 2.8 },
  { month: "Dec", return: 3.5 },
]

const trades = [
  { date: "2024-06-01", symbol: "AAPL", dir: "Long", entry: 192.3, exit: 198.45, pnl: "+$922" },
  { date: "2024-06-02", symbol: "NVDA", dir: "Long", entry: 845.0, exit: 892.5, pnl: "+$3,562" },
  { date: "2024-06-03", symbol: "TSLA", dir: "Short", entry: 252.1, exit: 245.8, pnl: "+$315" },
  { date: "2024-06-04", symbol: "MSFT", dir: "Long", entry: 418.2, exit: 425.3, pnl: "+$710" },
  { date: "2024-06-05", symbol: "GOOGL", dir: "Long", entry: 172.8, exit: 175.2, pnl: "+$192" },
]

const previousRuns = [
  { id: "1", strategy: "RSI Mean Reversion", symbol: "AAPL", period: "Jan-Jun 2024", return: "+12.4%", sharpe: 1.84, status: "completed" },
  { id: "2", strategy: "Golden Cross", symbol: "MSFT", period: "Jan-Jun 2024", return: "+8.9%", sharpe: 1.32, status: "completed" },
  { id: "3", strategy: "Volatility Breakout", symbol: "NVDA", period: "Mar-Jun 2024", return: "+15.2%", sharpe: 2.01, status: "completed" },
]

export default function BacktestingPage() {
  const [selectedStrategy, setSelectedStrategy] = useState("rsi")
  const [selectedSymbol, setSelectedSymbol] = useState("AAPL")

  return (
    <div className="space-y-6 animate-fade-in">
      <PageHeader
        title="Backtesting"
        description="Test your strategies against historical data"
        actions={
          <div className="flex gap-2">
            <Button variant="outline" size="sm">
              <History className="h-4 w-4 mr-2" />
              History
            </Button>
            <Button size="sm" className="gap-2">
              <Play className="h-4 w-4" />
              Run Backtest
            </Button>
          </div>
        }
      />

      {/* Config */}
      <GlassCard>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">Strategy</label>
            <Select value={selectedStrategy} onValueChange={setSelectedStrategy}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="rsi">RSI Mean Reversion</SelectItem>
                <SelectItem value="golden">Golden Cross</SelectItem>
                <SelectItem value="volatility">Volatility Breakout</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">Symbol</label>
            <Select value={selectedSymbol} onValueChange={setSelectedSymbol}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="AAPL">AAPL</SelectItem>
                <SelectItem value="MSFT">MSFT</SelectItem>
                <SelectItem value="NVDA">NVDA</SelectItem>
                <SelectItem value="TSLA">TSLA</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">Start Date</label>
            <Input type="date" defaultValue="2024-01-01" />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">End Date</label>
            <Input type="date" defaultValue="2024-06-30" />
          </div>
        </div>
        <div className="flex gap-4 mt-4">
          <div className="flex items-center gap-2">
            <label className="text-sm text-muted-foreground">Initial Capital</label>
            <Input type="number" defaultValue={100000} className="w-32" />
          </div>
          <Button className="ml-auto gap-2">
            <BarChart3 className="h-4 w-4" />
            Run Backtest
          </Button>
        </div>
      </GlassCard>

      {/* Results Metrics */}
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3">
        <StatCard title="Total Return" value="+12.4%" change={12.4} />
        <StatCard title="Sharpe Ratio" value="1.84" change={0} />
        <StatCard title="Sortino Ratio" value="2.12" change={0} />
        <StatCard title="Max Drawdown" value="-8.4%" change={-8.4} />
        <StatCard title="Win Rate" value="62%" change={0} />
        <StatCard title="Profit Factor" value="1.92" change={0} />
        <StatCard title="Total Trades" value="47" change={0} />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <GlassCard>
          <GlassCardHeader>
            <GlassCardTitle>Equity Curve</GlassCardTitle>
          </GlassCardHeader>
          <div className="h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={equityCurve}>
                <defs>
                  <linearGradient id="eqGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#00c853" stopOpacity={0.15} />
                    <stop offset="95%" stopColor="#00c853" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="day" stroke="rgba(255,255,255,0.1)" tick={{ fill: "rgba(255,255,255,0.4)", fontSize: 11 }} tickLine={false} />
                <YAxis stroke="rgba(255,255,255,0.1)" tick={{ fill: "rgba(255,255,255,0.4)", fontSize: 11 }} tickLine={false} tickFormatter={(v) => `$${(v/1000).toFixed(0)}k`} />
                <Tooltip
                  contentStyle={{ background: "rgba(13,17,23,0.95)", border: "1px solid rgba(30,45,69,0.5)", borderRadius: "8px" }}
                />
                <Area type="monotone" dataKey="equity" stroke="#00c853" strokeWidth={2} fill="url(#eqGrad)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </GlassCard>

        <GlassCard>
          <GlassCardHeader>
            <GlassCardTitle>Drawdown</GlassCardTitle>
          </GlassCardHeader>
          <div className="h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={equityCurve}>
                <defs>
                  <linearGradient id="ddGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ff1744" stopOpacity={0.15} />
                    <stop offset="95%" stopColor="#ff1744" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="day" stroke="rgba(255,255,255,0.1)" tick={{ fill: "rgba(255,255,255,0.4)", fontSize: 11 }} tickLine={false} />
                <YAxis stroke="rgba(255,255,255,0.1)" tick={{ fill: "rgba(255,255,255,0.4)", fontSize: 11 }} tickLine={false} tickFormatter={(v) => `${v.toFixed(1)}%`} />
                <Tooltip
                  contentStyle={{ background: "rgba(13,17,23,0.95)", border: "1px solid rgba(30,45,69,0.5)", borderRadius: "8px" }}
                />
                <Area type="monotone" dataKey="drawdown" stroke="#ff1744" strokeWidth={2} fill="url(#ddGrad)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </GlassCard>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Monthly Returns */}
        <GlassCard>
          <GlassCardHeader>
            <GlassCardTitle>Monthly Returns</GlassCardTitle>
          </GlassCardHeader>
          <div className="h-[250px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={monthlyReturns}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="month" stroke="rgba(255,255,255,0.1)" tick={{ fill: "rgba(255,255,255,0.4)", fontSize: 11 }} />
                <YAxis stroke="rgba(255,255,255,0.1)" tick={{ fill: "rgba(255,255,255,0.4)", fontSize: 11 }} tickFormatter={(v) => `${v}%`} />
                <Tooltip
                  contentStyle={{ background: "rgba(13,17,23,0.95)", border: "1px solid rgba(30,45,69,0.5)", borderRadius: "8px" }}
                />
                <Bar dataKey="return" radius={[4, 4, 0, 0]}>
                  {monthlyReturns.map((entry, i) => (
                    <rect key={i} fill={entry.return >= 0 ? "#00c853" : "#ff1744"} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </GlassCard>

        {/* Trade List */}
        <GlassCard>
          <GlassCardHeader>
            <GlassCardTitle>Recent Trades</GlassCardTitle>
          </GlassCardHeader>
          <div className="space-y-2">
            {trades.map((trade, i) => (
              <div
                key={i}
                className="flex items-center justify-between py-2.5 px-3 rounded-lg hover:bg-muted/30 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <Badge variant={trade.dir === "Long" ? "success" : "danger"}>
                    {trade.dir}
                  </Badge>
                  <div>
                    <p className="text-sm font-medium">{trade.symbol}</p>
                    <p className="text-xs text-muted-foreground">{trade.date}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-xs text-muted-foreground">
                    ${trade.entry} → ${trade.exit}
                  </p>
                  <p className="text-sm font-medium text-buy">{trade.pnl}</p>
                </div>
              </div>
            ))}
          </div>
        </GlassCard>
      </div>

      {/* Previous Runs */}
      <GlassCard>
        <GlassCardHeader>
          <GlassCardTitle>Backtest History</GlassCardTitle>
          <Button variant="ghost" size="sm">
            <RefreshCw className="h-3 w-3 mr-2" />
            Refresh
          </Button>
        </GlassCardHeader>
        <div className="space-y-3">
          {previousRuns.map((run) => (
            <div
              key={run.id}
              className="flex items-center justify-between py-3 border-b border-border last:border-0"
            >
              <div>
                <div className="flex items-center gap-2">
                  <p className="text-sm font-medium">{run.strategy}</p>
                  <Badge variant="success">{run.status}</Badge>
                </div>
                <p className="text-xs text-muted-foreground mt-0.5">
                  {run.symbol} &middot; {run.period}
                </p>
              </div>
              <div className="flex items-center gap-6">
                <div className="text-right">
                  <p className="text-sm font-medium text-buy">{run.return}</p>
                  <p className="text-xs text-muted-foreground">Return</p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium">{run.sharpe}</p>
                  <p className="text-xs text-muted-foreground">Sharpe</p>
                </div>
                <Button variant="outline" size="sm">
                  <Download className="h-3 w-3 mr-2" />
                  Report
                </Button>
              </div>
            </div>
          ))}
        </div>
      </GlassCard>
    </div>
  )
}
