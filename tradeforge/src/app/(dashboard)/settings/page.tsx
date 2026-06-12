"use client"

import { useState } from "react"
import { PageHeader } from "@/components/ui/page-header"
import { GlassCard, GlassCardHeader, GlassCardTitle } from "@/components/ui/glass-card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Switch } from "@/components/ui/switch"
import { Separator } from "@/components/ui/separator"
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import { User, Shield, Bell, CreditCard, Key, Link, Palette } from "lucide-react"

export default function SettingsPage() {
  return (
    <div className="space-y-6 animate-fade-in">
      <PageHeader title="Settings" description="Manage your account and preferences" />

      <Tabs defaultValue="profile">
        <TabsList className="mb-6">
          <TabsTrigger value="profile" className="gap-2">
            <User className="h-4 w-4" />
            Profile
          </TabsTrigger>
          <TabsTrigger value="security" className="gap-2">
            <Shield className="h-4 w-4" />
            Security
          </TabsTrigger>
          <TabsTrigger value="notifications" className="gap-2">
            <Bell className="h-4 w-4" />
            Notifications
          </TabsTrigger>
          <TabsTrigger value="billing" className="gap-2">
            <CreditCard className="h-4 w-4" />
            Billing
          </TabsTrigger>
          <TabsTrigger value="brokers" className="gap-2">
            <Link className="h-4 w-4" />
            Brokers
          </TabsTrigger>
          <TabsTrigger value="api" className="gap-2">
            <Key className="h-4 w-4" />
            API Keys
          </TabsTrigger>
        </TabsList>

        <TabsContent value="profile">
          <GlassCard>
            <GlassCardHeader>
              <GlassCardTitle>Profile Information</GlassCardTitle>
            </GlassCardHeader>
            <div className="space-y-4 max-w-lg">
              <div className="space-y-2">
                <label className="text-sm font-medium">Full Name</label>
                <Input defaultValue="John Doe" />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Email</label>
                <Input defaultValue="john@example.com" type="email" />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Timezone</label>
                <Input defaultValue="America/New_York" />
              </div>
              <Button>Save Changes</Button>
            </div>
          </GlassCard>
        </TabsContent>

        <TabsContent value="security">
          <div className="space-y-6 max-w-lg">
            <GlassCard>
              <GlassCardHeader>
                <GlassCardTitle>Change Password</GlassCardTitle>
              </GlassCardHeader>
              <div className="space-y-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Current Password</label>
                  <Input type="password" />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">New Password</label>
                  <Input type="password" />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Confirm Password</label>
                  <Input type="password" />
                </div>
                <Button>Update Password</Button>
              </div>
            </GlassCard>

            <GlassCard>
              <GlassCardHeader>
                <GlassCardTitle>Two-Factor Authentication</GlassCardTitle>
              </GlassCardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium">Enable 2FA</p>
                  <p className="text-sm text-muted-foreground">
                    Add an extra layer of security to your account
                  </p>
                </div>
                <Switch />
              </div>
            </GlassCard>

            <GlassCard>
              <GlassCardHeader>
                <GlassCardTitle>Sessions</GlassCardTitle>
              </GlassCardHeader>
              <div className="space-y-3">
                {[
                  { device: "Chrome on macOS", ip: "192.168.1.1", lastActive: "Now", current: true },
                  { device: "Safari on iPhone", ip: "10.0.0.1", lastActive: "2 days ago", current: false },
                ].map((session, i) => (
                  <div key={i} className="flex items-center justify-between py-2">
                    <div>
                      <div className="flex items-center gap-2">
                        <p className="text-sm font-medium">{session.device}</p>
                        {session.current && <Badge variant="success" className="text-[10px]">Current</Badge>}
                      </div>
                      <p className="text-xs text-muted-foreground">{session.ip} · {session.lastActive}</p>
                    </div>
                    {!session.current && <Button variant="ghost" size="sm" className="text-destructive">Revoke</Button>}
                  </div>
                ))}
              </div>
            </GlassCard>
          </div>
        </TabsContent>

        <TabsContent value="notifications">
          <GlassCard>
            <GlassCardHeader>
              <GlassCardTitle>Notification Preferences</GlassCardTitle>
            </GlassCardHeader>
            <div className="space-y-4 max-w-lg">
              {[
                { label: "Trade executions", desc: "When a bot opens or closes a position" },
                { label: "Price alerts", desc: "When price targets are hit" },
                { label: "Weekly summary", desc: "Weekly performance report" },
                { label: "System updates", desc: "Platform maintenance and updates" },
                { label: "AI insights", desc: "Daily AI-generated trading insights" },
              ].map((item) => (
                <div key={item.label} className="flex items-center justify-between py-2">
                  <div>
                    <p className="text-sm font-medium">{item.label}</p>
                    <p className="text-xs text-muted-foreground">{item.desc}</p>
                  </div>
                  <Switch defaultChecked />
                </div>
              ))}
            </div>
          </GlassCard>
        </TabsContent>

        <TabsContent value="billing">
          <div className="space-y-6 max-w-lg">
            <GlassCard>
              <GlassCardHeader>
                <GlassCardTitle>Current Plan</GlassCardTitle>
              </GlassCardHeader>
              <div className="flex items-center justify-between mb-4">
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-xl font-bold">Pro</h3>
                    <Badge variant="success">Active</Badge>
                  </div>
                  <p className="text-sm text-muted-foreground">$29/month · Next billing: July 15, 2024</p>
                </div>
                <Button variant="outline">Change Plan</Button>
              </div>
              <Separator className="my-4" />
              <div className="space-y-2">
                <p className="text-sm font-medium">Payment Method</p>
                <div className="flex items-center gap-3 p-3 rounded-lg border border-border">
                  <CreditCard className="h-5 w-5 text-muted-foreground" />
                  <span className="text-sm">Visa ending in 4242</span>
                  <span className="text-xs text-muted-foreground">Expires 12/26</span>
                  <Button variant="ghost" size="sm" className="ml-auto">Update</Button>
                </div>
              </div>
            </GlassCard>

            <GlassCard>
              <GlassCardHeader>
                <GlassCardTitle>Billing History</GlassCardTitle>
              </GlassCardHeader>
              <div className="space-y-2">
                {[
                  { date: "Jun 15, 2024", amount: "$29.00", status: "paid" },
                  { date: "May 15, 2024", amount: "$29.00", status: "paid" },
                  { date: "Apr 15, 2024", amount: "$29.00", status: "paid" },
                ].map((invoice) => (
                  <div key={invoice.date} className="flex items-center justify-between py-2">
                    <span className="text-sm">{invoice.date}</span>
                    <span className="text-sm font-medium">{invoice.amount}</span>
                    <Badge variant="success" className="text-[10px]">{invoice.status}</Badge>
                  </div>
                ))}
              </div>
            </GlassCard>
          </div>
        </TabsContent>

        <TabsContent value="brokers">
          <GlassCard>
            <GlassCardHeader>
              <GlassCardTitle>Connected Brokers</GlassCardTitle>
            </GlassCardHeader>
            <div className="space-y-4 max-w-lg">
              {[
                { name: "Alpaca", status: "connected", desc: "Paper trading" },
                { name: "Binance", status: "disconnected", desc: "API key required" },
                { name: "Polygon.io", status: "connected", desc: "Market data" },
              ].map((broker) => (
                <div key={broker.name} className="flex items-center justify-between py-3 border-b border-border last:border-0">
                  <div>
                    <div className="flex items-center gap-2">
                      <p className="text-sm font-medium">{broker.name}</p>
                      <Badge variant={broker.status === "connected" ? "success" : "secondary"}>
                        {broker.status}
                      </Badge>
                    </div>
                    <p className="text-xs text-muted-foreground">{broker.desc}</p>
                  </div>
                  <Button variant={broker.status === "connected" ? "outline" : "default"} size="sm">
                    {broker.status === "connected" ? "Configure" : "Connect"}
                  </Button>
                </div>
              ))}
            </div>
          </GlassCard>
        </TabsContent>

        <TabsContent value="api">
          <GlassCard>
            <GlassCardHeader>
              <GlassCardTitle>API Keys</GlassCardTitle>
            </GlassCardHeader>
            <div className="space-y-4 max-w-lg">
              <div className="flex items-center justify-between p-3 rounded-lg border border-border">
                <div>
                  <p className="text-sm font-medium">Production Key</p>
                  <p className="text-xs text-muted-foreground font-mono">tf_prod_••••••••••••a1b2</p>
                </div>
                <div className="flex gap-2">
                  <Button variant="ghost" size="sm">Copy</Button>
                  <Button variant="ghost" size="sm">Rotate</Button>
                </div>
              </div>
              <div className="flex items-center justify-between p-3 rounded-lg border border-border">
                <div>
                  <p className="text-sm font-medium">Test Key</p>
                  <p className="text-xs text-muted-foreground font-mono">tf_test_••••••••••••c3d4</p>
                </div>
                <div className="flex gap-2">
                  <Button variant="ghost" size="sm">Copy</Button>
                  <Button variant="ghost" size="sm">Revoke</Button>
                </div>
              </div>
              <Button variant="outline">Generate New Key</Button>
            </div>
          </GlassCard>
        </TabsContent>
      </Tabs>
    </div>
  )
}
