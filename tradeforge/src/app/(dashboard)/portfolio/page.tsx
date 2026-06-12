"use client"

import { useState } from "react"
import { PageHeader } from "@/components/ui/page-header"
import { StatCard } from "@/components/ui/stat-card"
import { GlassCard, GlassCardHeader, GlassCardTitle } from "@/components/ui/glass-card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs"
import { DataTable, type Column } from "@/components/ui/data-table"
import { formatCurrency, formatPercent } from "@/lib/utils"
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Legend,
} from "recharts"
import { Download, RefreshCw, Plus } from "lucide-react"

const allocationData = [
  { name: "Technology", value: 42, color: "#00c853" },
  { name: "Healthcare", value: 15, color: "#2979ff" },
  { name: "Finance", value: 12, color: "#ffd600" },
  { name: "Energy", value: 10, color: "#ff6d00" },
  { name: "Consumer", value: 8, color: "#d500f9" },
  { name: "Cash", value: 13, color: "#546e7a" },
]

const holdingsData = [
  {
    symbol: "NVDA",
    name: "NVIDIA Corporation",
    quantity: 75,
    avgPrice: 824.5,
    currentPrice: 892.5,
    value: 66937.5,
    allocation: 24.8,
    pnl: 5100,
    pnlPct: 8.25,
  },
  {
    symbol: "AAPL",
    name: "Apple Inc.",
    quantity: 150,
    avgPrice: 192.3,
    currentPrice: 198.45,
    value: 29767.5,
    allocation: 11.0,
    pnl: 922.5,
    pnlPct: 3.2,
  },
  {
    symbol: "MSFT",
    name: "Microsoft Corporation",
    quantity: 100,
    avgPrice: 418.2,
    currentPrice: 425.3,
    value: 42530,
    allocation: 15.8,
    pnl: 710,
    pnlPct: 1.7,
  },
  {
    symbol: "TSLA",
    name: "Tesla Inc.",
    quantity: 50,
    avgPrice: 252.1,
    currentPrice: 245.8,
    value: 12290,
    allocation: 4.6,
    pnl: -315,
    pnlPct: -2.5,
  },
  {
    symbol: "AMZN",
    name: "Amazon.com Inc.",
    quantity: 60,
    avgPrice: 182.4,
    currentPrice: 188.75,
    value: 11325,
    allocation: 4.2,
    pnl: 381,
    pnlPct: 3.48,
  },
  {
    symbol: "GOOGL",
    name: "Alphabet Inc.",
    quantity: 80,
    avgPrice: 172.8,
    currentPrice: 175.2,
    value: 14016,
    allocation: 5.2,
    pnl: 192,
    pnlPct: 1.39,
  },
  {
    symbol: "META",
    name: "Meta Platforms",
    quantity: 40,
    avgPrice: 498.5,
    currentPrice: 512.6,
    value: 20504,
    allocation: 7.6,
    pnl: 564,
    pnlPct: 2.83,
  },
]

const sectorPerformance = [
  { sector: "Technology", return: 12.4, color: "#00c853" },
  { sector: "Healthcare", return: 5.2, color: "#2979ff" },
  { sector: "Finance", return: -2.1, color: "#ff6d00" },
  { sector: "Energy", return: 8.7, color: "#ffd600" },
  { sector: "Consumer", return: 3.5, color: "#d500f9" },
]

const columns: Column<(typeof holdingsData)[0]>[] = [
  { key: "symbol", header: "Symbol", render: (item) => <span className="font-medium">{item.symbol}</span> },
  { key: "name", header: "Name", render: (item) => <span className="text-muted-foreground">{item.name}</span> },
  { key: "quantity", header: "Qty", render: (item) => item.quantity.toLocaleString() },
  {
    key: "avgPrice",
    header: "Avg Price",
    render: (item) => formatCurrency(item.avgPrice),
  },
  {
    key: "currentPrice",
    header: "Current",
    render: (item) => formatCurrency(item.currentPrice),
  },
  {
    key: "value",
    header: "Value",
    render: (item) => formatCurrency(item.value),
  },
  {
    key: "allocation",
    header: "Allocation",
    render: (item) => (
      <div className="flex items-center gap-2">
        <div className="w-16 h-1.5 rounded-full bg-muted overflow-hidden">
          <div
            className="h-full rounded-full bg-primary"
            style={{ width: `${item.allocation * 4}%` }}
          />
        </div>
        <span className="text-xs">{item.allocation.toFixed(1)}%</span>
      </div>
    ),
  },
  {
    key: "pnlPct",
    header: "P&L",
    sortable: true,
    render: (item) => (
      <span className={item.pnlPct >= 0 ? "text-buy" : "text-sell"}>
        {formatPercent(item.pnlPct)}
      </span>
    ),
  },
]

export default function PortfolioPage() {
  const [tab, setTab] = useState("holdings")

  return (
    <div className="space-y-6 animate-fade-in">
      <PageHeader
        title="Portfolio"
        description="Track your investments and performance"
        actions={
          <div className="flex gap-2">
            <Button variant="outline" size="sm">
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
            <Button variant="outline" size="sm">
              <Download className="h-4 w-4 mr-2" />
              Export
            </Button>
            <Button size="sm">
              <Plus className="h-4 w-4 mr-2" />
              Add Funds
            </Button>
          </div>
        }
      />

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Total Value" value="$269,487" change={1.8} changeLabel="today" />
        <StatCard title="Total P&L" value="+$34,892" change={14.9} changeLabel="all time" />
        <StatCard title="Day Change" value="+$4,782" change={1.8} changeLabel="today" />
        <StatCard
          title="Cash Balance"
          value="$35,000"
          change={0}
          changeLabel="available"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Allocation */}
        <GlassCard>
          <GlassCardHeader>
            <GlassCardTitle>Asset Allocation</GlassCardTitle>
          </GlassCardHeader>
          <div className="h-[250px]">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={allocationData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={90}
                  paddingAngle={4}
                  dataKey="value"
                >
                  {allocationData.map((entry, i) => (
                    <Cell key={i} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    background: "rgba(13,17,23,0.95)",
                    border: "1px solid rgba(30,45,69,0.5)",
                    borderRadius: "8px",
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="grid grid-cols-2 gap-2 mt-2">
            {allocationData.map((item) => (
              <div key={item.name} className="flex items-center gap-2 text-xs">
                <div
                  className="h-2 w-2 rounded-full shrink-0"
                  style={{ background: item.color }}
                />
                <span className="text-muted-foreground">{item.name}</span>
                <span className="ml-auto font-medium">{item.value}%</span>
              </div>
            ))}
          </div>
        </GlassCard>

        {/* Sector Performance */}
        <GlassCard>
          <GlassCardHeader>
            <GlassCardTitle>Sector Performance</GlassCardTitle>
          </GlassCardHeader>
          <div className="h-[250px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={sectorPerformance}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis
                  dataKey="sector"
                  stroke="rgba(255,255,255,0.2)"
                  tick={{ fill: "rgba(255,255,255,0.4)", fontSize: 11 }}
                />
                <YAxis
                  stroke="rgba(255,255,255,0.2)"
                  tick={{ fill: "rgba(255,255,255,0.4)", fontSize: 11 }}
                  tickFormatter={(v) => `${v}%`}
                />
                <Tooltip
                  contentStyle={{
                    background: "rgba(13,17,23,0.95)",
                    border: "1px solid rgba(30,45,69,0.5)",
                    borderRadius: "8px",
                  }}
                />
                <Bar dataKey="return" radius={[4, 4, 0, 0]}>
                  {sectorPerformance.map((entry, i) => (
                    <Cell key={i} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </GlassCard>

        {/* Risk Metrics */}
        <GlassCard>
          <GlassCardHeader>
            <GlassCardTitle>Risk Metrics</GlassCardTitle>
          </GlassCardHeader>
          <div className="space-y-4">
            {[
              { label: "Sharpe Ratio", value: "1.84", status: "good" },
              { label: "Sortino Ratio", value: "2.12", status: "good" },
              { label: "Max Drawdown", value: "-8.4%", status: "warning" },
              { label: "Beta", value: "1.12", status: "neutral" },
              { label: "Alpha", value: "3.2%", status: "good" },
              { label: "Volatility", value: "18.5%", status: "neutral" },
            ].map((metric) => (
              <div
                key={metric.label}
                className="flex items-center justify-between py-2 border-b border-border last:border-0"
              >
                <span className="text-sm text-muted-foreground">{metric.label}</span>
                <span
                  className={`text-sm font-medium ${
                    metric.status === "good"
                      ? "text-buy"
                      : metric.status === "warning"
                        ? "text-yellow-500"
                        : ""
                  }`}
                >
                  {metric.value}
                </span>
              </div>
            ))}
          </div>
        </GlassCard>
      </div>

      {/* Holdings Table */}
      <GlassCard>
        <Tabs value={tab} onValueChange={setTab}>
          <GlassCardHeader>
            <GlassCardTitle>Holdings</GlassCardTitle>
            <TabsList>
              <TabsTrigger value="holdings">Holdings</TabsTrigger>
              <TabsTrigger value="transactions">Transactions</TabsTrigger>
            </TabsList>
          </GlassCardHeader>

          <div className="px-6 pb-6">
            <TabsContent value="holdings">
              <DataTable columns={columns} data={holdingsData} searchable searchKeys={["symbol", "name"]} />
            </TabsContent>

            <TabsContent value="transactions">
              <DataTable
                columns={[
                  { key: "date", header: "Date" },
                  { key: "symbol", header: "Symbol" },
                  { key: "type", header: "Type" },
                  { key: "quantity", header: "Quantity" },
                  { key: "price", header: "Price" },
                  { key: "total", header: "Total" },
                ]}
                data={[]}
              />
            </TabsContent>
          </div>
        </Tabs>
      </GlassCard>
    </div>
  )
}
