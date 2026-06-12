import * as React from "react"
import { cn } from "@/lib/utils"

interface GlassCardProps extends React.HTMLAttributes<HTMLDivElement> {
  hover?: boolean
  glow?: "green" | "blue" | "none"
}

export function GlassCard({
  className,
  children,
  hover = false,
  glow = "none",
  ...props
}: GlassCardProps) {
  return (
    <div
      className={cn(
        "glass rounded-xl p-6 transition-all duration-300",
        hover && "glass-hover cursor-pointer",
        glow === "green" && "glow-green",
        glow === "blue" && "glow-blue",
        className
      )}
      {...props}
    >
      {children}
    </div>
  )
}

export function GlassCardHeader({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("flex items-center justify-between mb-4", className)}
      {...props}
    />
  )
}

export function GlassCardTitle({
  className,
  ...props
}: React.HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h3
      className={cn("text-sm font-medium text-muted-foreground", className)}
      {...props}
    />
  )
}

export function GlassCardValue({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "text-2xl font-bold tracking-tight animate-slide-up",
        className
      )}
      {...props}
    />
  )
}
