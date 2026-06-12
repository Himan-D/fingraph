"use client"

import { useState } from "react"
import { PageHeader } from "@/components/ui/page-header"
import { GlassCard, GlassCardHeader, GlassCardTitle } from "@/components/ui/glass-card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Switch } from "@/components/ui/switch"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Bell, Plus, BellRing, BellOff, Trash2, Clock, TrendingUp, TrendingDown } from "lucide-react"
import { formatTimeAgo } from "@/lib/utils"

const alerts = [
  {
    id: "1",
    name: "AAPL Resistance Break",
    type: "price",
    symbol: "AAPL",
    condition: "Price above $205",
    status: "active",
    lastTriggered: "2 days ago",
  },
  {
    id: "2",
    name: "NVDA RSI Overbought",
    type: "technical",
    symbol: "NVDA",
    condition: "RSI above 70",
    status: "active",
    lastTriggered: "5 hours ago",
  },
  {
    id: "3",
    name: "BTC Daily Move",
    type: "price",
    symbol: "BTC",
    condition: "Price change > 5%",
    status: "active",
    lastTriggered: "1 day ago",
  },
  {
    id: "4",
    name: "Portfolio Drawdown",
    type: "portfolio",
    symbol: null,
    condition: "Portfolio drawdown > 10%",
    status: "paused",
    lastTriggered: "1 week ago",
  },
  {
    id: "5",
    name: "TSLA News Alert",
    type: "news",
    symbol: "TSLA",
    condition: "Breaking news detected",
    status: "active",
    lastTriggered: "3 days ago",
  },
]

const alertHistory = [
  { alert: "NVDA RSI Overbought", symbol: "NVDA", triggeredAt: "5 hours ago", value: "RSI at 72" },
  { alert: "AAPL Resistance Break", symbol: "AAPL", triggeredAt: "2 days ago", value: "Price at $206.50" },
  { alert: "BTC Daily Move", symbol: "BTC", triggeredAt: "1 day ago", value: "Price moved 5.2%" },
]

export default function AlertsPage() {
  const [showCreate, setShowCreate] = useState(false)

  const getTypeIcon = (type: string) => {
    switch (type) {
      case "price": return <TrendingUp className="h-4 w-4" />
      case "technical": return <Activity className="h-4 w-4" />
      case "portfolio": return <TrendingDown className="h-4 w-4" />
      case "news": return <Bell className="h-4 w-4" />
      default: return <Bell className="h-4 w-4" />
    }
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <PageHeader
        title="Alerts"
        description="Monitor market conditions and get notified"
        actions={
          <Button onClick={() => setShowCreate(true)}>
            <Plus className="h-4 w-4 mr-2" />
            Create Alert
          </Button>
        }
      />

      {/* Active Alerts */}
      <div className="grid grid-cols-1 gap-3">
        {alerts.map((alert) => (
          <GlassCard key={alert.id}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className={`h-10 w-10 rounded-lg flex items-center justify-center ${
                  alert.status === "active" ? "bg-primary/10" : "bg-muted"
                }`}>
                  {getTypeIcon(alert.type)}
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="font-medium">{alert.name}</h3>
                    <Badge variant={
                      alert.type === "price" ? "info" :
                      alert.type === "technical" ? "warning" :
                      alert.type === "portfolio" ? "danger" : "secondary"
                    } className="capitalize text-[10px]">
                      {alert.type}
                    </Badge>
                    <Badge variant={alert.status === "active" ? "success" : "secondary"} className="capitalize text-[10px]">
                      {alert.status}
                    </Badge>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    {alert.symbol && `${alert.symbol} — `}{alert.condition}
                  </p>
                  {alert.lastTriggered && (
                    <p className="text-xs text-muted-foreground mt-0.5">
                      Last triggered: {alert.lastTriggered}
                    </p>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Switch defaultChecked={alert.status === "active"} />
                <Button variant="ghost" size="icon" className="h-8 w-8 text-destructive">
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </GlassCard>
        ))}
      </div>

      {/* History */}
      <GlassCard>
        <GlassCardHeader>
          <GlassCardTitle>Alert History</GlassCardTitle>
        </GlassCardHeader>
        <div className="space-y-3">
          {alertHistory.map((item, i) => (
            <div key={i} className="flex items-center justify-between py-2.5 border-b border-border last:border-0">
              <div className="flex items-center gap-3">
                <Clock className="h-4 w-4 text-muted-foreground" />
                <div>
                  <p className="text-sm font-medium">{item.alert}</p>
                  <p className="text-xs text-muted-foreground">{item.symbol}</p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-sm">{item.value}</p>
                <p className="text-xs text-muted-foreground">{item.triggeredAt}</p>
              </div>
            </div>
          ))}
        </div>
      </GlassCard>

      {/* Create Alert Dialog */}
      <Dialog open={showCreate} onOpenChange={setShowCreate}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create Alert</DialogTitle>
            <DialogDescription>
              Set up conditions to monitor the markets.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Alert Name</label>
              <Input placeholder="e.g., AAPL Support Break" />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Type</label>
                <Select>
                  <SelectTrigger>
                    <SelectValue placeholder="Select type" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="price">Price Alert</SelectItem>
                    <SelectItem value="technical">Technical Alert</SelectItem>
                    <SelectItem value="news">News Alert</SelectItem>
                    <SelectItem value="portfolio">Portfolio Alert</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Symbol</label>
                <Input placeholder="e.g., AAPL" />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Condition</label>
                <Select>
                  <SelectTrigger>
                    <SelectValue placeholder="Select condition" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="above">Price above</SelectItem>
                    <SelectItem value="below">Price below</SelectItem>
                    <SelectItem value="cross_above">Crosses above</SelectItem>
                    <SelectItem value="cross_below">Crosses below</SelectItem>
                    <SelectItem value="change">Price change &gt; %</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Value</label>
                <Input type="number" placeholder="0" />
              </div>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Notifications</label>
              <div className="flex gap-4">
                <label className="flex items-center gap-2 text-sm">
                  <input type="checkbox" className="rounded border-border" /> Email
                </label>
                <label className="flex items-center gap-2 text-sm">
                  <input type="checkbox" className="rounded border-border" /> SMS
                </label>
                <label className="flex items-center gap-2 text-sm">
                  <input type="checkbox" className="rounded border-border" defaultChecked /> Push
                </label>
              </div>
            </div>
            <Button className="w-full">Create Alert</Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}

function Activity({ className }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
    </svg>
  )
}
