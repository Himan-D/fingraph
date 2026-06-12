"use client"

import { useState } from "react"
import { PageHeader } from "@/components/ui/page-header"
import { GlassCard, GlassCardHeader, GlassCardTitle } from "@/components/ui/glass-card"
import { StatCard } from "@/components/ui/stat-card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Switch } from "@/components/ui/switch"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs"
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts"
import {
  Bot,
  Plus,
  Play,
  Pause,
  StopCircle,
  Settings,
  TrendingUp,
  TrendingDown,
  Activity,
  BarChart3,
} from "lucide-react"

const bots = [
  {
    id: "1",
    name: "Momentum Trader",
    strategy: "RSI Mean Reversion",
    symbol: "NVDA",
    status: "running",
    totalPnl: "+$2,340",
    dailyPnl: "+$184",
    winRate: 68,
    totalTrades: 24,
    openPositions: 2,
  },
  {
    id: "2",
    name: "Mean Reversion",
    strategy: "Volatility Breakout",
    symbol: "AAPL",
    status: "running",
    totalPnl: "+$890",
    dailyPnl: "+$45",
    winRate: 62,
    totalTrades: 18,
    openPositions: 1,
  },
  {
    id: "3",
    name: "Grid Bot BTC",
    strategy: "Grid Trading",
    symbol: "BTC",
    status: "running",
    totalPnl: "+$4,567",
    dailyPnl: "+$234",
    winRate: 72,
    totalTrades: 156,
    openPositions: 5,
  },
  {
    id: "4",
    name: "Earnings Momentum",
    strategy: "Earnings Momentum",
    symbol: "AMZN",
    status: "stopped",
    totalPnl: "+$345",
    dailyPnl: "$0",
    winRate: 55,
    totalTrades: 8,
    openPositions: 0,
  },
]

const botPerformance = Array.from({ length: 30 }, (_, i) => ({
  day: i + 1,
  pnl: (Math.random() - 0.45) * 500 + 50,
}))

export default function BotsPage() {
  const [showCreate, setShowCreate] = useState(false)
  const [selectedBot, setSelectedBot] = useState<string | null>(null)

  return (
    <div className="space-y-6 animate-fade-in">
      <PageHeader
        title="Trading Bots"
        description="Deploy and monitor automated trading bots"
        actions={
          <Button onClick={() => setShowCreate(true)}>
            <Plus className="h-4 w-4 mr-2" />
            Create Bot
          </Button>
        }
      />

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <StatCard title="Active Bots" value="3" change={0} icon={<Bot className="h-4 w-4" />} />
        <StatCard title="Total P&L" value="+$7,797" change={15.2} icon={<TrendingUp className="h-4 w-4" />} />
        <StatCard title="Win Rate" value="67.3%" change={2.1} icon={<Activity className="h-4 w-4" />} />
        <StatCard title="Open Positions" value="8" change={-1} icon={<BarChart3 className="h-4 w-4" />} />
      </div>

      {/* Bot Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {bots.map((bot) => (
          <GlassCard key={bot.id} hover>
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className={`h-10 w-10 rounded-lg flex items-center justify-center ${
                  bot.status === "running" ? "bg-primary/10" : "bg-muted"
                }`}>
                  <Bot className={`h-5 w-5 ${bot.status === "running" ? "text-primary" : "text-muted-foreground"}`} />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="font-semibold">{bot.name}</h3>
                    <Badge variant={bot.status === "running" ? "success" : "secondary"} className="capitalize">
                      {bot.status}
                    </Badge>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {bot.symbol} &middot; {bot.strategy}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-1">
                {bot.status === "running" ? (
                  <>
                    <Button variant="ghost" size="icon" className="h-8 w-8">
                      <Pause className="h-4 w-4" />
                    </Button>
                    <Button variant="ghost" size="icon" className="h-8 w-8 text-destructive">
                      <StopCircle className="h-4 w-4" />
                    </Button>
                  </>
                ) : (
                  <Button variant="ghost" size="icon" className="h-8 w-8">
                    <Play className="h-4 w-4" />
                  </Button>
                )}
                <Button variant="ghost" size="icon" className="h-8 w-8">
                  <Settings className="h-4 w-4" />
                </Button>
              </div>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
              <div>
                <p className="text-xs text-muted-foreground">Total P&L</p>
                <p className="text-sm font-medium text-buy">{bot.totalPnl}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Daily P&L</p>
                <p className="text-sm font-medium text-buy">{bot.dailyPnl}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Win Rate</p>
                <p className="text-sm font-medium">{bot.winRate}%</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Open Positions</p>
                <p className="text-sm font-medium">{bot.openPositions}</p>
              </div>
            </div>

            <div className="h-[80px]">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={botPerformance}>
                  <defs>
                    <linearGradient id="botPnl" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#00c853" stopOpacity={0.1} />
                      <stop offset="95%" stopColor="#00c853" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <Area type="monotone" dataKey="pnl" stroke="#00c853" strokeWidth={1.5} fill="url(#botPnl)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </GlassCard>
        ))}
      </div>

      {/* Create Bot Dialog */}
      <Dialog open={showCreate} onOpenChange={setShowCreate}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Create Trading Bot</DialogTitle>
            <DialogDescription>
              Configure your automated trading bot.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Bot Name</label>
              <Input placeholder="My Trading Bot" />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Strategy</label>
                <Select>
                  <SelectTrigger>
                    <SelectValue placeholder="Select strategy" />
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
                <Select>
                  <SelectTrigger>
                    <SelectValue placeholder="Select symbol" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="AAPL">AAPL</SelectItem>
                    <SelectItem value="MSFT">MSFT</SelectItem>
                    <SelectItem value="NVDA">NVDA</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Position Size ($)</label>
              <Input type="number" placeholder="1000" />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Max Drawdown (%)</label>
                <Input type="number" placeholder="15" />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Daily Loss Limit ($)</label>
                <Input type="number" placeholder="500" />
              </div>
            </div>
            <Button className="w-full gap-2">
              <Bot className="h-4 w-4" />
              Deploy Bot
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}
