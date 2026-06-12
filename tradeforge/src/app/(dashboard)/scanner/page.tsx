"use client"

import { useState } from "react"
import { PageHeader } from "@/components/ui/page-header"
import { GlassCard, GlassCardHeader, GlassCardTitle } from "@/components/ui/glass-card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { DataTable, type Column } from "@/components/ui/data-table"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { ScanSearch, Search, TrendingUp, TrendingDown, Filter, Save, RefreshCw } from "lucide-react"

const scanResults = [
  { symbol: "NVDA", name: "NVIDIA Corporation", price: 892.5, change: 3.42, volume: 45.2, rsi: 62, signal: "bullish", marketCap: "2.2T" },
  { symbol: "META", name: "Meta Platforms", price: 512.6, change: 2.15, volume: 18.7, rsi: 58, signal: "bullish", marketCap: "1.3T" },
  { symbol: "AMD", name: "Advanced Micro Devices", price: 178.3, change: 4.81, volume: 32.1, rsi: 71, signal: "overbought", marketCap: "288B" },
  { symbol: "SNOW", name: "Snowflake Inc.", price: 168.2, change: -1.25, volume: 8.4, rsi: 42, signal: "bearish", marketCap: "56B" },
  { symbol: "PLTR", name: "Palantir Technologies", price: 24.8, change: 6.72, volume: 78.5, rsi: 75, signal: "overbought", marketCap: "52B" },
  { symbol: "COIN", name: "Coinbase Global", price: 245.6, change: 3.88, volume: 12.3, rsi: 65, signal: "bullish", marketCap: "62B" },
  { symbol: "TSLA", name: "Tesla Inc.", price: 245.8, change: -0.82, volume: 28.9, rsi: 48, signal: "neutral", marketCap: "782B" },
  { symbol: "AAPL", name: "Apple Inc.", price: 198.45, change: 1.23, volume: 22.4, rsi: 55, signal: "neutral", marketCap: "3.02T" },
  { symbol: "MSFT", name: "Microsoft Corporation", price: 425.3, change: 0.54, volume: 15.6, rsi: 52, signal: "neutral", marketCap: "3.16T" },
  { symbol: "AMZN", name: "Amazon.com Inc.", price: 188.75, change: 1.85, volume: 19.8, rsi: 60, signal: "bullish", marketCap: "1.96T" },
]

const presets = [
  { name: "Momentum", filters: "Change > 3%, Volume > 10M" },
  { name: "Oversold", filters: "RSI < 30, Volume > 5M" },
  { name: "Breakout", filters: "Volume > 2x Avg, RSI > 60" },
  { name: "High Volume", filters: "Volume > 50M, Market Cap > 10B" },
]

const columns: Column<(typeof scanResults)[0]>[] = [
  { key: "symbol", header: "Symbol", render: (item) => <span className="font-medium">{item.symbol}</span> },
  { key: "name", header: "Name", render: (item) => <span className="text-muted-foreground text-xs">{item.name}</span> },
  { key: "price", header: "Price", render: (item) => `$${item.price.toFixed(2)}` },
  {
    key: "change",
    header: "Change",
    sortable: true,
    render: (item) => (
      <span className={`flex items-center gap-1 text-sm font-medium ${item.change >= 0 ? "text-buy" : "text-sell"}`}>
        {item.change >= 0 ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
        {item.change >= 0 ? "+" : ""}{item.change}%
      </span>
    ),
  },
  { key: "volume", header: "Volume (M)", render: (item) => item.volume.toFixed(1) },
  {
    key: "rsi",
    header: "RSI",
    sortable: true,
    render: (item) => (
      <span className={
        item.rsi >= 70 ? "text-sell" : item.rsi <= 30 ? "text-buy" : ""
      }>{item.rsi}</span>
    ),
  },
  {
    key: "signal",
    header: "Signal",
    render: (item) => (
      <Badge variant={
        item.signal === "bullish" ? "success" :
        item.signal === "bearish" ? "danger" :
        item.signal === "overbought" ? "warning" : "secondary"
      } className="capitalize">
        {item.signal}
      </Badge>
    ),
  },
  { key: "marketCap", header: "Market Cap" },
]

export default function ScannerPage() {
  return (
    <div className="space-y-6 animate-fade-in">
      <PageHeader
        title="Market Scanner"
        description="Scan thousands of assets for trading opportunities"
        actions={
          <div className="flex gap-2">
            <Button variant="outline" size="sm">
              <Save className="h-4 w-4 mr-2" />
              Save Scan
            </Button>
            <Button size="sm" className="gap-2">
              <RefreshCw className="h-4 w-4" />
              Scan Now
            </Button>
          </div>
        }
      />

      {/* Filters */}
      <GlassCard>
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-4">
          <div className="space-y-2">
            <label className="text-xs font-medium text-muted-foreground">Min Price</label>
            <Input type="number" placeholder="0" />
          </div>
          <div className="space-y-2">
            <label className="text-xs font-medium text-muted-foreground">Max Price</label>
            <Input type="number" placeholder="10000" />
          </div>
          <div className="space-y-2">
            <label className="text-xs font-medium text-muted-foreground">Min Volume</label>
            <Input type="number" placeholder="1M" />
          </div>
          <div className="space-y-2">
            <label className="text-xs font-medium text-muted-foreground">Market Cap</label>
            <Select>
              <SelectTrigger>
                <SelectValue placeholder="Any" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="any">Any</SelectItem>
                <SelectItem value="large">Large Cap (&gt;10B)</SelectItem>
                <SelectItem value="mid">Mid Cap (2B-10B)</SelectItem>
                <SelectItem value="small">Small Cap (&lt;2B)</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <label className="text-xs font-medium text-muted-foreground">RSI Range</label>
            <Select>
              <SelectTrigger>
                <SelectValue placeholder="Any" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="any">Any</SelectItem>
                <SelectItem value="oversold">Oversold (&lt;30)</SelectItem>
                <SelectItem value="neutral">Neutral (30-70)</SelectItem>
                <SelectItem value="overbought">Overbought (&gt;70)</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <label className="text-xs font-medium text-muted-foreground">Signal</label>
            <Select>
              <SelectTrigger>
                <SelectValue placeholder="Any" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="any">Any</SelectItem>
                <SelectItem value="bullish">Bullish</SelectItem>
                <SelectItem value="bearish">Bearish</SelectItem>
                <SelectItem value="neutral">Neutral</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </GlassCard>

      {/* Presets */}
      <div className="flex flex-wrap gap-2">
        <span className="text-xs text-muted-foreground self-center">Presets:</span>
        {presets.map((p) => (
          <button
            key={p.name}
            className="inline-flex items-center gap-1 text-xs px-3 py-1.5 rounded-full border border-border bg-muted/30 text-muted-foreground hover:bg-muted/50 hover:text-foreground transition-colors"
          >
            <Filter className="h-3 w-3" />
            {p.name}
          </button>
        ))}
      </div>

      {/* Results */}
      <GlassCard>
        <GlassCardHeader>
          <GlassCardTitle>Scan Results</GlassCardTitle>
          <Badge variant="secondary">{scanResults.length} results</Badge>
        </GlassCardHeader>
        <DataTable columns={columns} data={scanResults} searchable searchKeys={["symbol", "name"]} />
      </GlassCard>
    </div>
  )
}
