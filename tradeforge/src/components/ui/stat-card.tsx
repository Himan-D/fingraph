"use client"

import { cn } from "@/lib/utils"
import { GlassCard, GlassCardHeader, GlassCardTitle, GlassCardValue } from "./glass-card"
import { TrendingUp, TrendingDown, Minus } from "lucide-react"

interface StatCardProps {
  title: string
  value: string
  change?: number
  changeLabel?: string
  icon?: React.ReactNode
  className?: string
}

export function StatCard({
  title,
  value,
  change,
  changeLabel,
  icon,
  className,
}: StatCardProps) {
  const TrendIcon =
    change && change > 0
      ? TrendingUp
      : change && change < 0
        ? TrendingDown
        : Minus

  const changeColor =
    change && change > 0
      ? "text-buy"
      : change && change < 0
        ? "text-sell"
        : "text-muted-foreground"

  return (
    <GlassCard className={cn("", className)} hover>
      <GlassCardHeader>
        <GlassCardTitle>{title}</GlassCardTitle>
        {icon && <span className="text-muted-foreground">{icon}</span>}
      </GlassCardHeader>
      <GlassCardValue>{value}</GlassCardValue>
      {change !== undefined && (
        <div className="flex items-center gap-1.5 mt-2">
          <TrendIcon className={cn("h-4 w-4", changeColor)} />
          <span className={cn("text-sm font-medium", changeColor)}>
            {change >= 0 ? "+" : ""}
            {change.toFixed(2)}%
          </span>
          {changeLabel && (
            <span className="text-xs text-muted-foreground">{changeLabel}</span>
          )}
        </div>
      )}
    </GlassCard>
  )
}
