"use client"

import { PageHeader } from "@/components/ui/page-header"
import { GlassCard, GlassCardHeader, GlassCardTitle } from "@/components/ui/glass-card"
import { StatCard } from "@/components/ui/stat-card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs"
import { DataTable, type Column } from "@/components/ui/data-table"
import { Shield, Users, Activity, Server, AlertTriangle, CheckCircle } from "lucide-react"

const users = [
  { id: "1", name: "John Doe", email: "john@example.com", plan: "pro", status: "active", joined: "Jan 15, 2024" },
  { id: "2", name: "Jane Smith", email: "jane@example.com", plan: "enterprise", status: "active", joined: "Feb 3, 2024" },
  { id: "3", name: "Bob Wilson", email: "bob@example.com", plan: "free", status: "active", joined: "Mar 22, 2024" },
  { id: "4", name: "Alice Brown", email: "alice@example.com", plan: "pro", status: "suspended", joined: "Dec 10, 2023" },
  { id: "5", name: "Charlie Davis", email: "charlie@example.com", plan: "free", status: "inactive", joined: "Apr 5, 2024" },
]

const systemMetrics = [
  { metric: "API Latency", value: "142ms", status: "healthy" },
  { metric: "Error Rate", value: "0.02%", status: "healthy" },
  { metric: "Active Users", value: "847", status: "healthy" },
  { metric: "Bot Executions", value: "12,452", status: "healthy" },
  { metric: "Database Size", value: "24.5 GB", status: "healthy" },
]

export default function AdminPage() {
  return (
    <div className="space-y-6 animate-fade-in">
      <PageHeader
        title="Admin Panel"
        description="System administration and monitoring"
        actions={
          <Badge variant="success" className="gap-1">
            <CheckCircle className="h-3 w-3" />
            All systems operational
          </Badge>
        }
      />

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <StatCard title="Total Users" value="2,847" change={12} changeLabel="this month" icon={<Users className="h-4 w-4" />} />
        <StatCard title="Active Bots" value="1,234" change={8} changeLabel="this month" icon={<Activity className="h-4 w-4" />} />
        <StatCard title="API Requests" value="4.2M" change={22} changeLabel="this month" icon={<Server className="h-4 w-4" />} />
        <StatCard title="Alerts Triggered" value="847" change={-3} changeLabel="this month" icon={<AlertTriangle className="h-4 w-4" />} />
      </div>

      <Tabs defaultValue="overview">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="users">Users</TabsTrigger>
          <TabsTrigger value="system">System</TabsTrigger>
        </TabsList>

        <TabsContent value="overview">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <GlassCard>
              <GlassCardHeader>
                <GlassCardTitle>System Health</GlassCardTitle>
              </GlassCardHeader>
              <div className="space-y-3">
                {systemMetrics.map((m) => (
                  <div key={m.metric} className="flex items-center justify-between py-2 border-b border-border last:border-0">
                    <span className="text-sm">{m.metric}</span>
                    <div className="flex items-center gap-3">
                      <span className="text-sm font-medium">{m.value}</span>
                      <Badge variant="success" className="text-[10px]">
                        <CheckCircle className="h-3 w-3 mr-1" />
                        {m.status}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            </GlassCard>

            <GlassCard>
              <GlassCardHeader>
                <GlassCardTitle>Recent Activity</GlassCardTitle>
              </GlassCardHeader>
              <div className="space-y-3">
                {[
                  { action: "New user signup", detail: "user@example.com", time: "2 min ago" },
                  { action: "Bot deployed", detail: "Momentum Trader (NVDA)", time: "15 min ago" },
                  { action: "Alert triggered", detail: "AAPL price alert", time: "32 min ago" },
                  { action: "Backtest completed", detail: "RSI Strategy (MSFT)", time: "1 hour ago" },
                  { action: "Payment received", detail: "Pro plan - $29.00", time: "3 hours ago" },
                ].map((event, i) => (
                  <div key={i} className="flex items-center justify-between py-2">
                    <div>
                      <p className="text-sm">{event.action}</p>
                      <p className="text-xs text-muted-foreground">{event.detail}</p>
                    </div>
                    <span className="text-xs text-muted-foreground">{event.time}</span>
                  </div>
                ))}
              </div>
            </GlassCard>
          </div>
        </TabsContent>

        <TabsContent value="users">
          <GlassCard>
            <DataTable
              columns={[
                { key: "name", header: "Name" },
                { key: "email", header: "Email" },
                {
                  key: "plan",
                  header: "Plan",
                  render: (item) => (
                    <Badge variant={item.plan === "enterprise" ? "info" : item.plan === "pro" ? "default" : "secondary"} className="capitalize">
                      {item.plan}
                    </Badge>
                  ),
                },
                {
                  key: "status",
                  header: "Status",
                  render: (item) => (
                    <Badge variant={item.status === "active" ? "success" : "danger"} className="capitalize">
                      {item.status}
                    </Badge>
                  ),
                },
                { key: "joined", header: "Joined" },
                {
                  key: "actions",
                  header: "Actions",
                  render: () => (
                    <Button variant="ghost" size="sm">Manage</Button>
                  ),
                },
              ]}
              data={users}
              searchable
              searchKeys={["name", "email"]}
            />
          </GlassCard>
        </TabsContent>

        <TabsContent value="system">
          <GlassCard>
            <GlassCardHeader>
              <GlassCardTitle>Feature Flags</GlassCardTitle>
            </GlassCardHeader>
            <div className="space-y-3">
              {[
                { feature: "AI Trading Copilot", status: "enabled", rollout: "100%" },
                { feature: "Live Trading", status: "enabled", rollout: "100%" },
                { feature: "Advanced Backtesting", status: "enabled", rollout: "75%" },
                { feature: "White Label", status: "beta", rollout: "10%" },
                { feature: "Mobile App", status: "disabled", rollout: "0%" },
              ].map((flag) => (
                <div key={flag.feature} className="flex items-center justify-between py-3 border-b border-border last:border-0">
                  <div>
                    <p className="text-sm font-medium">{flag.feature}</p>
                    <p className="text-xs text-muted-foreground">Rollout: {flag.rollout}</p>
                  </div>
                  <Badge variant={
                    flag.status === "enabled" ? "success" :
                    flag.status === "beta" ? "warning" : "secondary"
                  } className="capitalize">
                    {flag.status}
                  </Badge>
                </div>
              ))}
            </div>
          </GlassCard>
        </TabsContent>
      </Tabs>
    </div>
  )
}
