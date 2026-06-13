"use client"

import { useState } from "react"
import { PageHeader } from "@/components/ui/page-header"
import { GlassCard, GlassCardHeader, GlassCardTitle } from "@/components/ui/glass-card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Switch } from "@/components/ui/switch"
import { Bell, Plus, Trash2, Clock, TrendingUp, TrendingDown, Activity } from "lucide-react"
import { useAIAlerts } from "@/hooks/useFingraph"
import { api } from "@/lib/api"
import { toast } from "@/hooks/useToast"

export default function AlertsPage() {
  const [showCreate, setShowCreate] = useState(false)
  const { data: alerts, isLoading, refetch } = useAIAlerts(50)

  const getTypeIcon = (type: string) => {
    switch (type) {
      case "price": return <TrendingUp className="h-4 w-4" />
      case "technical": return <Activity className="h-4 w-4" />
      case "portfolio": return <TrendingDown className="h-4 w-4" />
      default: return <Bell className="h-4 w-4" />
    }
  }

  const markRead = async (id: number) => {
    try {
      await api.post(`/api/v1/ai/alerts/${id}/read`, {})
      refetch()
    } catch {}
  }

  const scanForNew = async () => {
    try {
      await api.post("/api/v1/ai/alerts/scan", {})
      toast({ title: "Alert scan triggered", variant: "success" })
      refetch()
    } catch (err) {
      toast({ title: "Scan failed", description: err instanceof Error ? err.message : "Error", variant: "destructive" })
    }
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <PageHeader
        title="AI Alerts"
        description="AI-generated alerts from market analysis"
        actions={
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={scanForNew}>
              <Bell className="h-4 w-4 mr-2" />
              Scan for Alerts
            </Button>
          </div>
        }
      />

      {/* Alerts List */}
      <div className="grid grid-cols-1 gap-3">
        {isLoading ? (
          Array.from({ length: 5 }).map((_, i) => (
            <GlassCard key={i}>
              <div className="flex items-center gap-4 p-2">
                <div className="h-10 w-10 rounded-lg bg-muted animate-pulse" />
                <div className="flex-1 space-y-2">
                  <div className="h-4 w-48 bg-muted animate-pulse rounded" />
                  <div className="h-3 w-64 bg-muted animate-pulse rounded" />
                </div>
              </div>
            </GlassCard>
          ))
        ) : alerts && alerts.length > 0 ? (
          alerts.map((alert) => (
            <GlassCard key={alert.id}>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className={`h-10 w-10 rounded-lg flex items-center justify-center ${
                    alert.severity === "high" ? "bg-sell/10 text-sell" :
                    alert.severity === "medium" ? "bg-yellow-500/10 text-yellow-500" :
                    "bg-primary/10 text-primary"
                  }`}>
                    {getTypeIcon(alert.alert_type)}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="font-medium">{alert.title}</h3>
                      <Badge variant={
                        alert.severity === "high" ? "danger" :
                        alert.severity === "medium" ? "warning" : "info"
                      } className="capitalize text-[10px]">
                        {alert.severity}
                      </Badge>
                      <Badge variant="secondary" className="text-[10px]">{alert.symbol}</Badge>
                      {!alert.is_read && (
                        <span className="h-2 w-2 rounded-full bg-primary" />
                      )}
                    </div>
                    <p className="text-sm text-muted-foreground">
                      {alert.summary}
                    </p>
                    <p className="text-xs text-muted-foreground mt-0.5">
                      {alert.alert_type} &middot; {new Date(alert.created_at).toLocaleString()}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {!alert.is_read && (
                    <Button variant="ghost" size="sm" onClick={() => markRead(alert.id)}>
                      Mark Read
                    </Button>
                  )}
                </div>
              </div>
            </GlassCard>
          ))
        ) : (
          <GlassCard>
            <div className="text-center py-8 text-muted-foreground">
              <Bell className="h-8 w-8 mx-auto mb-2 opacity-50" />
              <p>No AI alerts yet. Click &quot;Scan for Alerts&quot; to generate alerts.</p>
            </div>
          </GlassCard>
        )}
      </div>
    </div>
  )
}
