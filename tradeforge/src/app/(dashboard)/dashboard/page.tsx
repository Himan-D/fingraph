"use client"

import { useState } from "react"
import { PageHeader } from "@/components/ui/page-header"
import { StatCard } from "@/components/ui/stat-card"
import { GlassCard, GlassCardHeader, GlassCardTitle, GlassCardValue } from "@/components/ui/glass-card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs"
import { motion } from "framer-motion"
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  Activity,
  Bot,
  ArrowRight,
  Sparkles,
  BarChart3,
  LineChart,
  PieChart,
  Wallet,
} from "lucide-react"
import {
  LineChart as RechartsLineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Area,
  AreaChart,
} from "recharts"

const performanceData = Array.from({ length: 30 }, (_, i) => ({
  day: `Day ${i + 1}`,
  portfolio: 100000 + Math.random() * 30000 - 5000 + i * 800,
  benchmark: 100000 + Math.random() * 20000 - 4000 + i * 400,
}))

const tickerData = [
  { symbol: "AAPL", price: 198.45, change: 1.2 },
  { symbol: "TSLA", price: 245.80, change: -0.8 },
  { symbol: "NVDA", price: 892.50, change: 3.4 },
  { symbol: "MSFT", price: 425.30, change: 0.5 },
  { symbol: "GOOGL", price: 175.20, change: -0.3 },
  { symbol: "AMZN", price: 188.75, change: 1.8 },
  { symbol: "META", price: 512.60, change: 2.1 },
  { symbol: "BTC", price: 67890, change: -1.5 },
  { symbol: "ETH", price: 3456, change: 0.7 },
  { symbol: "SOL", price: 178.90, change: 5.2 },
]

const aiInsights = [
  {
    title: "Momentum detected in NVDA",
    description: "Strong bullish momentum with RSI at 62. Volume 2.5x average. Consider adding to position.",
    type: "opportunity",
  },
  {
    title: "Portfolio rebalance suggested",
    description: "Tech allocation at 68% exceeds target. Consider rebalancing to reduce risk.",
    type: "alert",
  },
  {
    title: "AAPL earnings incoming",
    description: "Earnings in 3 days. Options market pricing 4.2% move. Consider hedging.",
    type: "info",
  },
]

export default function DashboardPage() {
  const [activeTab, setActiveTab] = useState("overview")

  return (
    <div className="space-y-6 animate-fade-in">
      <PageHeader
        title="Dashboard"
        description="Your trading overview at a glance"
        actions={
          <Button variant="default" className="gap-2">
            <Sparkles className="h-4 w-4" />
            AI Insights
          </Button>
        }
      />

      {/* Market Ticker */}
      <div className="relative overflow-hidden rounded-xl border border-border bg-muted/30 py-3">
        <div className="flex animate-ticker gap-8 whitespace-nowrap">
          {[...tickerData, ...tickerData].map((item, i) => (
            <div key={i} className="flex items-center gap-2 text-sm">
              <span className="font-semibold">{item.symbol}</span>
              <span>${item.price.toLocaleString()}</span>
              <span
                className={`flex items-center gap-0.5 text-xs font-medium ${
                  item.change >= 0 ? "text-buy" : "text-sell"
                }`}
              >
                {item.change >= 0 ? (
                  <TrendingUp className="h-3 w-3" />
                ) : (
                  <TrendingDown className="h-3 w-3" />
                )}
                {item.change >= 0 ? "+" : ""}
                {item.change}%
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Stats Grid */}
      <motion.div
        className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4"
        initial="initial"
        animate="animate"
        variants={{
          animate: { transition: { staggerChildren: 0.05 } },
        }}
      >
        <motion.div
          variants={{ initial: { opacity: 0, y: 10 }, animate: { opacity: 1, y: 0 } }}
        >
          <StatCard
            title="Portfolio Value"
            value="$147,892"
            change={2.4}
            changeLabel="today"
            icon={<DollarSign className="h-4 w-4" />}
          />
        </motion.div>
        <motion.div
          variants={{ initial: { opacity: 0, y: 10 }, animate: { opacity: 1, y: 0 } }}
        >
          <StatCard
            title="Day P&L"
            value="+$3,472"
            change={2.4}
            changeLabel="today"
            icon={<Activity className="h-4 w-4" />}
          />
        </motion.div>
        <motion.div
          variants={{ initial: { opacity: 0, y: 10 }, animate: { opacity: 1, y: 0 } }}
        >
          <StatCard
            title="Open Positions"
            value="12"
            change={1}
            changeLabel="vs yesterday"
            icon={<BarChart3 className="h-4 w-4" />}
          />
        </motion.div>
        <motion.div
          variants={{ initial: { opacity: 0, y: 10 }, animate: { opacity: 1, y: 0 } }}
        >
          <StatCard
            title="Active Bots"
            value="3"
            change={0}
            changeLabel="no change"
            icon={<Bot className="h-4 w-4" />}
          />
        </motion.div>
      </motion.div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Performance Chart */}
        <div className="lg:col-span-2">
          <GlassCard>
            <GlassCardHeader>
              <GlassCardTitle>Portfolio Performance</GlassCardTitle>
              <Tabs value={activeTab} onValueChange={setActiveTab}>
                <TabsList>
                  <TabsTrigger value="overview">1M</TabsTrigger>
                  <TabsTrigger value="3m">3M</TabsTrigger>
                  <TabsTrigger value="1y">1Y</TabsTrigger>
                  <TabsTrigger value="all">All</TabsTrigger>
                </TabsList>
              </Tabs>
            </GlassCardHeader>
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={performanceData}>
                  <defs>
                    <linearGradient id="portfolioGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#00c853" stopOpacity={0.15} />
                      <stop offset="95%" stopColor="#00c853" stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="benchmarkGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#2979ff" stopOpacity={0.1} />
                      <stop offset="95%" stopColor="#2979ff" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis
                    dataKey="day"
                    stroke="rgba(255,255,255,0.1)"
                    tick={{ fill: "rgba(255,255,255,0.4)", fontSize: 12 }}
                    tickLine={false}
                  />
                  <YAxis
                    stroke="rgba(255,255,255,0.1)"
                    tick={{ fill: "rgba(255,255,255,0.4)", fontSize: 12 }}
                    tickLine={false}
                    axisLine={false}
                    tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`}
                  />
                  <Tooltip
                    contentStyle={{
                      background: "rgba(13,17,23,0.95)",
                      border: "1px solid rgba(30,45,69,0.5)",
                      borderRadius: "8px",
                      boxShadow: "0 8px 32px rgba(0,0,0,0.3)",
                    }}
                    labelStyle={{ color: "#e8edf5" }}
                  />
                  <Area
                    type="monotone"
                    dataKey="portfolio"
                    stroke="#00c853"
                    strokeWidth={2}
                    fill="url(#portfolioGrad)"
                    name="Portfolio"
                  />
                  <Area
                    type="monotone"
                    dataKey="benchmark"
                    stroke="#2979ff"
                    strokeWidth={2}
                    fill="url(#benchmarkGrad)"
                    strokeDasharray="4 4"
                    name="Benchmark"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </GlassCard>
        </div>

        {/* AI Insights */}
        <div className="space-y-4">
          <GlassCard>
            <GlassCardHeader>
              <GlassCardTitle>AI Insights</GlassCardTitle>
              <Sparkles className="h-4 w-4 text-primary" />
            </GlassCardHeader>
            <div className="space-y-4">
              {aiInsights.map((insight, i) => (
                <div
                  key={i}
                  className="rounded-lg border border-border bg-muted/20 p-4 transition-colors hover:bg-muted/40 cursor-pointer"
                >
                  <div className="flex items-start gap-3">
                    <div
                      className={`mt-0.5 h-2 w-2 rounded-full shrink-0 ${
                        insight.type === "opportunity"
                          ? "bg-buy"
                          : insight.type === "alert"
                            ? "bg-yellow-500"
                            : "bg-blue-500"
                      }`}
                    />
                    <div>
                      <p className="text-sm font-medium mb-1">{insight.title}</p>
                      <p className="text-xs text-muted-foreground">
                        {insight.description}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
            <Button variant="ghost" className="w-full mt-4 text-sm gap-2">
              View all insights <ArrowRight className="h-3 w-3" />
            </Button>
          </GlassCard>
        </div>
      </div>

      {/* Bottom Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Open Positions */}
        <GlassCard>
          <GlassCardHeader>
            <GlassCardTitle>Open Positions</GlassCardTitle>
            <Button variant="ghost" size="sm" className="gap-2">
              View all <ArrowRight className="h-3 w-3" />
            </Button>
          </GlassCardHeader>
          <div className="space-y-3">
            {[
              { symbol: "AAPL", dir: "Long", qty: 150, price: 195.20, pnl: "+$1,230" },
              { symbol: "TSLA", dir: "Long", qty: 50, price: 248.30, pnl: "-$675" },
              { symbol: "NVDA", dir: "Short", qty: 25, price: 890.40, pnl: "+$890" },
              { symbol: "MSFT", dir: "Long", qty: 100, price: 423.10, pnl: "+$340" },
            ].map((pos) => (
              <div
                key={pos.symbol}
                className="flex items-center justify-between py-3 border-b border-border last:border-0"
              >
                <div className="flex items-center gap-3">
                  <div className="h-8 w-8 rounded-lg bg-muted flex items-center justify-center text-xs font-bold">
                    {pos.symbol.slice(0, 2)}
                  </div>
                  <div>
                    <p className="text-sm font-medium">{pos.symbol}</p>
                    <p className="text-xs text-muted-foreground">
                      {pos.dir} &middot; {pos.qty} shares @ ${pos.price}
                    </p>
                  </div>
                </div>
                <span
                  className={`text-sm font-medium ${
                    pos.pnl.startsWith("+") ? "text-buy" : "text-sell"
                  }`}
                >
                  {pos.pnl}
                </span>
              </div>
            ))}
          </div>
        </GlassCard>

        {/* Active Bots */}
        <GlassCard>
          <GlassCardHeader>
            <GlassCardTitle>Active Bots</GlassCardTitle>
            <Badge variant="success">3 running</Badge>
          </GlassCardHeader>
          <div className="space-y-3">
            {[
              { name: "Momentum Trader", symbol: "NVDA", status: "running", pnl: "+$2,340", trades: 24 },
              { name: "Mean Reversion", symbol: "AAPL", status: "running", pnl: "+$890", trades: 18 },
              { name: "Grid Bot", symbol: "BTC", status: "running", pnl: "+$4,567", trades: 156 },
            ].map((bot) => (
              <div
                key={bot.name}
                className="flex items-center justify-between py-3 border-b border-border last:border-0"
              >
                <div className="flex items-center gap-3">
                  <div className="h-8 w-8 rounded-lg bg-primary/10 flex items-center justify-center">
                    <Bot className="h-4 w-4 text-primary" />
                  </div>
                  <div>
                    <p className="text-sm font-medium">{bot.name}</p>
                    <p className="text-xs text-muted-foreground">
                      {bot.symbol} &middot; {bot.trades} trades
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <span className="text-sm font-medium text-buy">{bot.pnl}</span>
                  <div className="flex items-center gap-1.5 mt-0.5 justify-end">
                    <span className="h-1.5 w-1.5 rounded-full bg-buy animate-pulse-glow" />
                    <span className="text-xs text-muted-foreground">Active</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </GlassCard>
      </div>
    </div>
  )
}
