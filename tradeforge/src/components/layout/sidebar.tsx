"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import { useAuth } from "@/hooks/useAuth"
import {
  LayoutDashboard,
  BotMessageSquare,
  Briefcase,
  ScrollText,
  TestTube,
  Bot,
  ScanSearch,
  Bell,
  BookOpenText,
  Settings,
  Shield,
  TrendingUp,
} from "lucide-react"

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/copilot", label: "AI Copilot", icon: BotMessageSquare },
  { href: "/portfolio", label: "Portfolio", icon: Briefcase },
  { href: "/strategies", label: "Strategies", icon: ScrollText },
  { href: "/backtesting", label: "Backtesting", icon: TestTube },
  { href: "/bots", label: "Trading Bots", icon: Bot },
  { href: "/scanner", label: "Market Scanner", icon: ScanSearch },
  { href: "/alerts", label: "Alerts", icon: Bell },
  { href: "/journal", label: "Journal", icon: BookOpenText },
  { href: "/settings", label: "Settings", icon: Settings },
  { href: "/admin", label: "Admin", icon: Shield },
]

export function Sidebar() {
  const pathname = usePathname()
  const { user } = useAuth()
  const plan = user?.plan?.toUpperCase() || "FREE"

  return (
    <aside className="fixed left-0 top-0 z-40 h-screen w-64 border-r border-border bg-sidebar">
      <div className="flex h-full flex-col">
        <div className="flex h-16 items-center gap-2 border-b border-border px-6">
          <TrendingUp className="h-6 w-6 text-primary" />
          <span className="text-lg font-bold">
            Trade<span className="text-primary">Forge</span>
          </span>
        </div>

        <nav className="flex-1 overflow-y-auto p-4 space-y-1">
          {navItems.map((item) => {
            const isActive = pathname === item.href
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-200",
                  isActive
                    ? "bg-primary/10 text-primary shadow-sm"
                    : "text-muted-foreground hover:bg-muted/50 hover:text-foreground"
                )}
              >
                <item.icon className="h-4 w-4" />
                {item.label}
              </Link>
            )
          })}
        </nav>

        <div className="border-t border-border p-4">
          <div className="flex items-center gap-3 rounded-lg bg-muted/30 px-3 py-2">
            <div className="flex-1">
              <p className="text-xs font-medium text-muted-foreground">{plan} Plan</p>
              {plan === "FREE" && (
                <Link
                  href="/pricing"
                  className="text-xs text-primary hover:underline"
                >
                  Upgrade to Pro
                </Link>
              )}
            </div>
          </div>
        </div>
      </div>
    </aside>
  )
}
