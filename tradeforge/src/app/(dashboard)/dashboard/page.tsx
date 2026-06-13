"use client"

import { useState } from "react"
import { PageHeader } from "@/components/ui/page-header"
import { StatCard } from "@/components/ui/stat-card"
import { GlassCard, GlassCardHeader, GlassCardTitle } from "@/components/ui/glass-card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
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
} from "lucide-react"
import {
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Area,
  AreaChart,
} from "recharts"
import { useIndices, useMovers, useAIAlerts } from "@/hooks/useFingraph"
import { formatCurrency, formatCompactNumber } from "@/lib/utils"
import { useAuth } from "@/hooks/useAuth"
import Link from "next/link"

export default function DashboardPage() {
  const [activeTab, setActiveTab] = useState("overview")
  const { user } = useAuth()

  const { data: indices } = useIndices()
  const { data: movers } = useMovers()
  const { data: alerts } = useAIAlerts(5)

  const allTickers = [
    ...(indices?.slice(0, 5) ?? []).map((i) => ({
      symbol: i.symbol,
      price: i.price,
      change_pct: i.pct_change,
    })),
    ...(movers?.gainers.slice(0, 5) ?? []).map((m) => ({
      symbol: m.symbol,
      price: m.price,
      change_pct: m.pct_change,
    })),
  ]

  const performanceData = Array.from({ length: 30 }, (_, i) => ({
    day: `Day ${i + 1}`,
    portfolio: 100000 + Math.random() * 30000 - 5000 + i * 800,
    benchmark: 100000 + Math.random() * 20000 - 4000 + i * 400,
  }))

  return (
    <div className="space-y-6 animate-fade-in">
      <PageHeader
        title="Dashboard"
        description={`Welcome back${user?.name ? `, ${user.name}` : ""}`}
        actions={
          <Link href="/copilot">
            <Button variant="default" className="gap-2">
              <Sparkles className="h-4 w-4" />
              AI Insights
            </Button>
          </Link>
        }
      />

      {/* Market Ticker */}
      <div className="relative overflow-hidden rounded-xl border border-border bg-muted/30 py-3">
        <div className="flex animate-ticker gap-8 whitespace-nowrap">
          {allTickers.length > 0
            ? [...allTickers, ...allTickers].map((item, i) => (
                <div key={i} className="flex items-center gap-2 text-sm">
                  <span className="font-semibold">{item.symbol}</span>
                  <span>{formatCurrency(item.price, "INR")}</span>
                  <span
                    className={`flex items-center gap-0.5 text-xs font-medium ${
                      item.change_pct >= 0 ? "text-buy" : "text-sell"
                    }`}
                  >
                    {item.change_pct >= 0 ? (
                      <TrendingUp className="h-3 w-3" />
                    ) : (
                      <TrendingDown className="h-3 w-3" />
                    )}
                    {item.change_pct >= 0 ? "+" : ""}
                    {item.change_pct.toFixed(2)}%
                  </span>
                </div>
              ))
            : Array.from({ length: 10 }).map((_, i) => (
                <div key={i} className="flex items-center gap-2 text-sm">
                  <span className="font-semibold text-muted-foreground">—</span>
                  <span className="text-muted-foreground">Loading...</span>
                </div>
              ))}
        </div>
      </div>

      {/* Stats Grid */}
      <motion.div
        className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4"
        initial="initial"
        animate="animate"
        variants={{ animate: { transition: { staggerChildren: 0.05 } } }}
      >
        <motion.div variants={{ initial: { opacity: 0, y: 10 }, animate: { opacity: 1, y: 0 } }}>
          <StatCard
            title="Market Status"
            value={indices?.[0]?.pct_change !== undefined ? (indices[0].pct_change >= 0 ? "Bullish" : "Bearish") : "Loading..."}
            change={indices?.[0]?.pct_change ?? 0}
            changeLabel="NIFTY 50"
            icon={<DollarSign className="h-4 w-4" />}
          />
        </motion.div>
        <motion.div variants={{ initial: { opacity: 0, y: 10 }, animate: { opacity: 1, y: 0 } }}>
          <StatCard
            title="Top Gainer"
            value={movers?.gainers?.[0]?.symbol ?? "—"}
            change={movers?.gainers?.[0]?.pct_change ?? 0}
            changeLabel="today"
            icon={<TrendingUp className="h-4 w-4" />}
          />
        </motion.div>
        <motion.div variants={{ initial: { opacity: 0, y: 10 }, animate: { opacity: 1, y: 0 } }}>
          <StatCard
            title="AI Alerts"
            value={String(alerts?.length ?? 0)}
            change={0}
            changeLabel="unread"
            icon={<Activity className="h-4 w-4" />}
          />
        </motion.div>
        <motion.div variants={{ initial: { opacity: 0, y: 10 }, animate: { opacity: 1, y: 0 } }}>
          <StatCard
            title="Your Plan"
            value={user?.plan?.toUpperCase() ?? "FREE"}
            change={0}
            changeLabel="current tier"
            icon={<BarChart3 className="h-4 w-4" />}
          />
        </motion.div>
      </motion.div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <GlassCard>
            <GlassCardHeader>
              <GlassCardTitle>Market Indices</GlassCardTitle>
              <Tabs value={activeTab} onValueChange={setActiveTab}>
                <TabsList>
                  <TabsTrigger value="overview">Overview</TabsTrigger>
                </TabsList>
              </Tabs>
            </GlassCardHeader>
            <div className="space-y-3">
              {indices && indices.length > 0
                ? indices.map((idx) => (
                    <div
                      key={idx.symbol}
                      className="flex items-center justify-between py-2.5 border-b border-border last:border-0"
                    >
                      <div className="flex items-center gap-3">
                        <div className="h-8 w-8 rounded-lg bg-muted flex items-center justify-center text-xs font-bold">
                          {idx.symbol.slice(0, 4)}
                        </div>
                        <div>
                          <p className="text-sm font-medium">{idx.name}</p>
                          <p className="text-xs text-muted-foreground">{idx.symbol}</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-sm font-medium">{formatCurrency(idx.price, "INR")}</p>
                        <p
                          className={`text-xs font-medium ${
                            idx.pct_change >= 0 ? "text-buy" : "text-sell"
                          }`}
                        >
                          {idx.pct_change >= 0 ? "+" : ""}
                          {idx.pct_change.toFixed(2)}% ({idx.change >= 0 ? "+" : ""}
                          {idx.change.toFixed(2)})
                        </p>
                      </div>
                    </div>
                  ))
                : [1, 2, 3, 4, 5].map((i) => (
                    <div key={i} className="flex items-center justify-between py-2.5">
                      <div className="flex items-center gap-3">
                        <div className="h-8 w-8 rounded-lg bg-muted animate-pulse" />
                        <div>
                          <div className="h-4 w-24 bg-muted animate-pulse rounded" />
                          <div className="h-3 w-16 bg-muted animate-pulse rounded mt-1" />
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="h-4 w-20 bg-muted animate-pulse rounded ml-auto" />
                      </div>
                    </div>
                  ))}
            </div>
          </GlassCard>
        </div>

        {/* Top Gainers / Losers + AI Alerts */}
        <div className="space-y-4">
          <GlassCard>
            <GlassCardHeader>
              <GlassCardTitle>Top Movers</GlassCardTitle>
              <Badge variant="success">{movers?.gainers?.length ?? 0} gainers</Badge>
            </GlassCardHeader>
            <div className="space-y-2">
              {movers?.gainers?.slice(0, 5).map((g) => (
                <div
                  key={g.symbol}
                  className="flex items-center justify-between py-2 border-b border-border last:border-0"
                >
                  <div>
                    <p className="text-sm font-medium">{g.symbol}</p>
                    <p className="text-xs text-muted-foreground">{g.name}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm">{formatCurrency(g.price, "INR")}</p>
                    <p className="text-xs text-buy">+{g.pct_change.toFixed(2)}%</p>
                  </div>
                </div>
              ))}
            </div>
          </GlassCard>

          <GlassCard>
            <GlassCardHeader>
              <GlassCardTitle>AI Alerts</GlassCardTitle>
              <Link href="/alerts">
                <Button variant="ghost" size="sm" className="gap-1">
                  View all <ArrowRight className="h-3 w-3" />
                </Button>
              </Link>
            </GlassCardHeader>
            <div className="space-y-3">
              {alerts && alerts.length > 0 ? (
                alerts.map((alert) => (
                  <div
                    key={alert.id}
                    className="rounded-lg border border-border bg-muted/20 p-3 transition-colors hover:bg-muted/40 cursor-pointer"
                  >
                    <div className="flex items-start gap-3">
                      <div
                        className={`mt-0.5 h-2 w-2 rounded-full shrink-0 ${
                          alert.severity === "high"
                            ? "bg-sell"
                            : alert.severity === "medium"
                              ? "bg-yellow-500"
                              : "bg-blue-500"
                        }`}
                      />
                      <div>
                        <p className="text-sm font-medium">{alert.title}</p>
                        <p className="text-xs text-muted-foreground mt-0.5">{alert.summary?.slice(0, 100)}</p>
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center py-4 text-muted-foreground text-sm">
                  <Sparkles className="h-5 w-5 mx-auto mb-2 opacity-50" />
                  No alerts yet. Alerts are generated automatically.
                </div>
              )}
            </div>
          </GlassCard>
        </div>
      </div>

      {/* Bottom - Performance Chart */}
      <GlassCard>
        <GlassCardHeader>
          <GlassCardTitle>Portfolio Performance</GlassCardTitle>
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
                tickFormatter={(v) => `₹${(v / 1000).toFixed(0)}k`}
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
  )
}
