"use client"

import { useState } from "react"
import { PageHeader } from "@/components/ui/page-header"
import { GlassCard, GlassCardHeader, GlassCardTitle } from "@/components/ui/glass-card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { DataTable, type Column } from "@/components/ui/data-table"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { TrendingUp, TrendingDown, Filter, RefreshCw } from "lucide-react"
import { useScreener, useScreenerSectors, type ScreenerResult, type ScreenerFilters } from "@/hooks/useFingraph"
import { formatCurrency } from "@/lib/utils"
import { toast } from "@/hooks/useToast"

const presets: { name: string; filters: ScreenerFilters }[] = [
  { name: "Large Cap Value", filters: { market_cap_min: 50000, pe_max: 20, dividend_yield_min: 2 } },
  { name: "High Growth", filters: { revenue_growth_min: 15, roe_min: 15 } },
  { name: "Low Debt", filters: { debt_equity_max: 0.5, roe_min: 12 } },
  { name: "Dividend Kings", filters: { dividend_yield_min: 3, pe_max: 25 } },
]

const columns: Column<ScreenerResult>[] = [
  { key: "symbol", header: "Symbol", render: (item) => <span className="font-medium">{item.symbol}</span> },
  { key: "name", header: "Name", render: (item) => <span className="text-muted-foreground text-xs max-w-[200px] truncate block">{item.name}</span> },
  { key: "price", header: "Price", render: (item) => formatCurrency(item.price, "INR") },
  {
    key: "pct_change",
    header: "Change",
    sortable: true,
    render: (item) => (
      <span className={`flex items-center gap-1 text-sm font-medium ${item.pct_change >= 0 ? "text-buy" : "text-sell"}`}>
        {item.pct_change >= 0 ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
        {item.pct_change >= 0 ? "+" : ""}{item.pct_change.toFixed(2)}%
      </span>
    ),
  },
  { key: "sector", header: "Sector", render: (item) => <span className="text-xs">{item.sector}</span> },
  {
    key: "pe_ratio",
    header: "P/E",
    sortable: true,
    render: (item) => item.pe_ratio?.toFixed(1) ?? "—",
  },
  {
    key: "roe",
    header: "ROE",
    sortable: true,
    render: (item) => item.roe ? `${item.roe.toFixed(1)}%` : "—",
  },
  {
    key: "debt_equity",
    header: "D/E",
    render: (item) => item.debt_equity?.toFixed(2) ?? "—",
  },
  {
    key: "market_cap",
    header: "Market Cap",
    render: (item) => item.market_cap ? `₹${(item.market_cap / 100).toFixed(0)} Cr` : "—",
  },
]

export default function ScannerPage() {
  const [filters, setFilters] = useState<ScreenerFilters>({ limit: 50, sort_by: "market_cap", sort_order: "desc" })
  const [enabled, setEnabled] = useState(false)
  const [activePreset, setActivePreset] = useState<string | null>(null)

  const { data: screenerResult, isLoading, refetch } = useScreener(filters, enabled)
  const { data: sectorsData } = useScreenerSectors()

  const handleRun = () => setEnabled(true)

  const applyPreset = (preset: typeof presets[0]) => {
    setActivePreset(preset.name)
    setFilters({ ...preset.filters, limit: 50, sort_by: "market_cap", sort_order: "desc" })
    setEnabled(true)
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <PageHeader
        title="Market Scanner"
        description="Screen Indian stocks by fundamentals"
        actions={
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={() => refetch()}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
            <Button size="sm" onClick={handleRun}>
              <Filter className="h-4 w-4 mr-2" />
              Scan Now
            </Button>
          </div>
        }
      />

      {/* Filters */}
      <GlassCard>
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-4">
          <div className="space-y-2">
            <label className="text-xs font-medium text-muted-foreground">Min P/E</label>
            <Input type="number" placeholder="0" value={filters.pe_min ?? ""} onChange={(e) => setFilters(f => ({ ...f, pe_min: e.target.value ? Number(e.target.value) : undefined }))} />
          </div>
          <div className="space-y-2">
            <label className="text-xs font-medium text-muted-foreground">Max P/E</label>
            <Input type="number" placeholder="100" value={filters.pe_max ?? ""} onChange={(e) => setFilters(f => ({ ...f, pe_max: e.target.value ? Number(e.target.value) : undefined }))} />
          </div>
          <div className="space-y-2">
            <label className="text-xs font-medium text-muted-foreground">Min ROE (%)</label>
            <Input type="number" placeholder="0" value={filters.roe_min ?? ""} onChange={(e) => setFilters(f => ({ ...f, roe_min: e.target.value ? Number(e.target.value) : undefined }))} />
          </div>
          <div className="space-y-2">
            <label className="text-xs font-medium text-muted-foreground">Sector</label>
            <Select value={filters.sector ?? ""} onValueChange={(v) => setFilters(f => ({ ...f, sector: v || undefined }))}>
              <SelectTrigger><SelectValue placeholder="Any" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Any</SelectItem>
                {sectorsData?.map((s: string) => (
                  <SelectItem key={s} value={s}>{s}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <label className="text-xs font-medium text-muted-foreground">Max D/E</label>
            <Input type="number" placeholder="1.0" value={filters.debt_equity_max ?? ""} onChange={(e) => setFilters(f => ({ ...f, debt_equity_max: e.target.value ? Number(e.target.value) : undefined }))} />
          </div>
          <div className="space-y-2">
            <label className="text-xs font-medium text-muted-foreground">Sort By</label>
            <Select value={filters.sort_by ?? "market_cap"} onValueChange={(v) => setFilters(f => ({ ...f, sort_by: v }))}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="market_cap">Market Cap</SelectItem>
                <SelectItem value="pe_ratio">P/E</SelectItem>
                <SelectItem value="roe">ROE</SelectItem>
                <SelectItem value="pct_change">Change %</SelectItem>
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
            onClick={() => applyPreset(p)}
            className={`inline-flex items-center gap-1 text-xs px-3 py-1.5 rounded-full border transition-colors ${
              activePreset === p.name
                ? "border-primary bg-primary/10 text-primary"
                : "border-border bg-muted/30 text-muted-foreground hover:bg-muted/50 hover:text-foreground"
            }`}
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
          <Badge variant="secondary">{screenerResult?.length ?? 0} results</Badge>
        </GlassCardHeader>
        {isLoading ? (
          <div className="flex items-center justify-center py-12 text-muted-foreground">
            <RefreshCw className="h-4 w-4 animate-spin mr-2" />
            Scanning stocks...
          </div>
        ) : screenerResult ? (
          <DataTable columns={columns} data={screenerResult} searchable searchKeys={["symbol", "name", "sector"]} />
        ) : enabled ? (
          <div className="text-center py-12 text-muted-foreground">
            No results found. Try adjusting your filters.
          </div>
        ) : (
          <div className="text-center py-12 text-muted-foreground">
            Configure filters and click &quot;Scan Now&quot; to find stocks.
          </div>
        )}
      </GlassCard>
    </div>
  )
}
