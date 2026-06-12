"use client"

import { useState } from "react"
import { PageHeader } from "@/components/ui/page-header"
import { GlassCard, GlassCardHeader, GlassCardTitle, GlassCardValue } from "@/components/ui/glass-card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog"
import { Textarea } from "@/components/ui/textarea"
import { StatCard } from "@/components/ui/stat-card"
import { BookOpenText, Plus, Sparkles, TrendingUp, TrendingDown, Tag, Smile, Frown, Meh } from "lucide-react"
import { formatDate } from "@/lib/utils"

const entries = [
  {
    id: "1",
    symbol: "NVDA",
    title: "Great momentum trade",
    notes: "Entered on breakout above $880 with strong volume. RSI was 58, not overbought. Exited at $892 for a clean 1.4% gain. Need to remember: patience paid off here — waited for the right setup instead of chasing.",
    emotions: ["confident", "patient"],
    tags: ["momentum", "breakout", "earnings"],
    pnl: 1275,
    date: "2024-06-05",
  },
  {
    id: "2",
    symbol: "TSLA",
    title: "FOMO entry - need to be more disciplined",
    notes: "Jumped into TSLA after seeing it spike 3% in 5 minutes. Didn't wait for confirmation. Got stopped out for -0.8%. Lesson: don't chase moves. Wait for pullback to support.",
    emotions: ["regretful", "impatient"],
    tags: ["mistake", "fomo", "discipline"],
    pnl: -340,
    date: "2024-06-04",
  },
  {
    id: "3",
    symbol: "AAPL",
    title: "Steady accumulation working",
    notes: "Been adding to AAPL over the past week on dips to the 50 SMA. Position is now 150 shares at $192 avg. Stock showing good relative strength vs sector. Holding for earnings.",
    emotions: ["confident", "patient"],
    tags: ["accumulation", "swing", "earnings"],
    pnl: 922,
    date: "2024-06-03",
  },
  {
    id: "4",
    symbol: "MSFT",
    title: "AI sentiment driving price",
    notes: "MSFT grinding higher on AI news flow. Solid fundamentals support the move. Keeping existing position but not adding at these levels. RSI at 65 — room to run but not cheap.",
    emotions: ["cautious", "optimistic"],
    tags: ["ai", "long-term", "hold"],
    pnl: 710,
    date: "2024-06-02",
  },
]

const emotionIcons: Record<string, React.ReactNode> = {
  confident: <Smile className="h-4 w-4 text-buy" />,
  patient: <Smile className="h-4 w-4 text-buy" />,
  regretful: <Frown className="h-4 w-4 text-sell" />,
  impatient: <Frown className="h-4 w-4 text-sell" />,
  cautious: <Meh className="h-4 w-4 text-yellow-500" />,
  optimistic: <Smile className="h-4 w-4 text-buy" />,
}

export default function JournalPage() {
  const [showCreate, setShowCreate] = useState(false)

  const totalPnl = entries.reduce((sum, e) => sum + (e.pnl ?? 0), 0)
  const winTrades = entries.filter((e) => (e.pnl ?? 0) >= 0).length
  const winRate = Math.round((winTrades / entries.length) * 100)

  return (
    <div className="space-y-6 animate-fade-in">
      <PageHeader
        title="Trading Journal"
        description="Review your trades and improve your strategy"
        actions={
          <div className="flex gap-2">
            <Button variant="outline" size="sm" className="gap-2">
              <Sparkles className="h-4 w-4" />
              AI Review
            </Button>
            <Button onClick={() => setShowCreate(true)}>
              <Plus className="h-4 w-4 mr-2" />
              New Entry
            </Button>
          </div>
        }
      />

      <div className="grid grid-cols-3 gap-4">
        <StatCard title="Total P&L" value={totalPnl >= 0 ? `+$${totalPnl}` : `-$${Math.abs(totalPnl)}`} change={0} />
        <StatCard title="Win Rate" value={`${winRate}%`} change={0} />
        <StatCard title="Entries" value={String(entries.length)} change={0} />
      </div>

      {/* AI Insight */}
      <GlassCard glow="green">
        <div className="flex items-start gap-3">
          <Sparkles className="h-5 w-5 text-primary shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-medium mb-1">AI Insight</p>
            <p className="text-sm text-muted-foreground">
              Your momentum trades are outperforming mean reversion by 3.2%. Consider focusing more on breakout setups. 
              Your main area for improvement is entry timing — waiting for confirmation could reduce drawdowns by 40%.
            </p>
          </div>
        </div>
      </GlassCard>

      {/* Journal Entries */}
      <div className="space-y-4">
        {entries.map((entry) => (
          <GlassCard key={entry.id} hover>
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-start gap-3">
                <div className="h-10 w-10 rounded-lg bg-muted flex items-center justify-center text-sm font-bold">
                  {entry.symbol}
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="font-semibold">{entry.title}</h3>
                    <span className={`text-sm font-medium ${(entry.pnl ?? 0) >= 0 ? "text-buy" : "text-sell"}`}>
                      {(entry.pnl ?? 0) >= 0 ? "+" : ""}${Math.abs(entry.pnl ?? 0)}
                    </span>
                  </div>
                  <p className="text-xs text-muted-foreground">{formatDate(entry.date)}</p>
                </div>
              </div>
            </div>
            <p className="text-sm text-muted-foreground mb-3 leading-relaxed">
              {entry.notes}
            </p>
            <div className="flex items-center gap-3 flex-wrap">
              <div className="flex items-center gap-1.5">
                {entry.emotions.map((emotion) => (
                  <span key={emotion} className="flex items-center gap-1 text-xs text-muted-foreground">
                    {emotionIcons[emotion] ?? <Meh className="h-3 w-3" />}
                    {emotion}
                  </span>
                ))}
              </div>
              <div className="flex items-center gap-1.5">
                <Tag className="h-3 w-3 text-muted-foreground" />
                {entry.tags.map((tag) => (
                  <Badge key={tag} variant="secondary" className="text-[10px] px-1.5 py-0">
                    {tag}
                  </Badge>
                ))}
              </div>
            </div>
          </GlassCard>
        ))}
      </div>

      {/* Create Entry Dialog */}
      <Dialog open={showCreate} onOpenChange={setShowCreate}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>New Journal Entry</DialogTitle>
            <DialogDescription>
              Document your trade and reflect on your decision-making.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Symbol</label>
                <Input placeholder="e.g., AAPL" />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">P&L ($)</label>
                <Input type="number" placeholder="0" />
              </div>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Title</label>
              <Input placeholder="What happened?" />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Notes</label>
              <Textarea
                placeholder="What did you learn? What would you do differently?"
                className="min-h-[120px]"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Tags</label>
              <div className="flex flex-wrap gap-2">
                {["momentum", "breakout", "mistake", "earnings", "swing", "scalp", "fomo"].map((tag) => (
                  <label key={tag} className="flex items-center gap-1.5 text-sm px-2 py-1 rounded-md border border-border hover:bg-muted/50 cursor-pointer">
                    <input type="checkbox" className="rounded border-border" />
                    {tag}
                  </label>
                ))}
              </div>
            </div>
            <Button className="w-full">Save Entry</Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}
