"use client"

import { useState } from "react"
import { PageHeader } from "@/components/ui/page-header"
import { GlassCard, GlassCardHeader, GlassCardTitle } from "@/components/ui/glass-card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog"
import { Textarea } from "@/components/ui/textarea"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Switch } from "@/components/ui/switch"
import {
  ScrollText,
  Plus,
  Play,
  Sparkles,
  Code,
  BarChart3,
  Copy,
  Trash2,
  Edit3,
} from "lucide-react"

const strategies = [
  {
    id: "1",
    name: "RSI Mean Reversion",
    type: "technical",
    status: "active",
    lastRun: "2 hours ago",
    backtestReturn: "+12.4%",
    sharpe: 1.84,
    description: "Buy when RSI crosses below 30, sell when above 70",
  },
  {
    id: "2",
    name: "Golden Cross Momentum",
    type: "technical",
    status: "draft",
    lastRun: "1 day ago",
    backtestReturn: "+8.9%",
    sharpe: 1.32,
    description: "Buy on 50/200 SMA crossover, sell on death cross",
  },
  {
    id: "3",
    name: "Volatility Breakout",
    type: "technical",
    status: "active",
    lastRun: "3 hours ago",
    backtestReturn: "+15.2%",
    sharpe: 2.01,
    description: "Enter on Keltner channel breakout with volume confirmation",
  },
  {
    id: "4",
    name: "Earnings Momentum",
    type: "fundamental",
    status: "draft",
    lastRun: "5 days ago",
    backtestReturn: "+6.7%",
    sharpe: 0.95,
    description: "Trade earnings surprises with post-announcement drift",
  },
]

export default function StrategiesPage() {
  const [showBuilder, setShowBuilder] = useState(false)
  const [nlInput, setNlInput] = useState("")
  const [generating, setGenerating] = useState(false)
  const [generatedCode, setGeneratedCode] = useState("")

  const handleGenerate = async () => {
    if (!nlInput.trim()) return
    setGenerating(true)
    setTimeout(() => {
      setGeneratedCode(`def should_enter(data):
    """Generate entry signal for: ${nlInput}"""
    rsi = compute_rsi(data.close, 14)
    bb_lower = compute_bollinger_band(data.close, 20, 2).lower
    
    return (
        rsi < 30 and
        data.close[-1] < bb_lower[-1] and
        data.volume[-1] > average_volume(data.volume, 20) * 1.5
    )

def should_exit(data):
    """Generate exit signal"""
    rsi = compute_rsi(data.close, 14)
    bb_upper = compute_bollinger_band(data.close, 20, 2).upper
    
    return (
        rsi > 70 or
        data.close[-1] > bb_upper[-1]
    )

def position_size(capital, price, risk_pct=1.0):
    """Calculate position size based on risk"""
    risk_amount = capital * (risk_pct / 100)
    return int(risk_amount / (price * 0.02))  # 2% stop loss`)
      setGenerating(false)
    }, 2000)
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <PageHeader
        title="Strategies"
        description="Build and manage your trading strategies"
        actions={
          <Button onClick={() => setShowBuilder(true)}>
            <Plus className="h-4 w-4 mr-2" />
            New Strategy
          </Button>
        }
      />

      {/* Strategy Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {strategies.map((s) => (
          <GlassCard key={s.id} hover>
            <div className="flex items-start justify-between mb-3">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <h3 className="font-semibold">{s.name}</h3>
                  <Badge
                    variant={s.status === "active" ? "success" : "secondary"}
                    className="capitalize"
                  >
                    {s.status}
                  </Badge>
                </div>
                <p className="text-sm text-muted-foreground">{s.description}</p>
              </div>
            </div>
            <div className="grid grid-cols-3 gap-4 mb-4">
              <div>
                <p className="text-xs text-muted-foreground">Return</p>
                <p className="text-sm font-medium text-buy">{s.backtestReturn}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Sharpe</p>
                <p className="text-sm font-medium">{s.sharpe}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Last Run</p>
                <p className="text-sm font-medium">{s.lastRun}</p>
              </div>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" className="flex-1 gap-2">
                <BarChart3 className="h-3 w-3" />
                Backtest
              </Button>
              <Button variant="outline" size="sm" className="flex-1 gap-2">
                <Play className="h-3 w-3" />
                Run
              </Button>
              <Button variant="ghost" size="icon">
                <Copy className="h-4 w-4" />
              </Button>
              <Button variant="ghost" size="icon">
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>
          </GlassCard>
        ))}
      </div>

      {/* Strategy Builder Dialog */}
      <Dialog open={showBuilder} onOpenChange={setShowBuilder}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Create Strategy</DialogTitle>
            <DialogDescription>
              Describe your strategy in natural language, and AI will generate the code.
            </DialogDescription>
          </DialogHeader>

          <Tabs defaultValue="natural">
            <TabsList className="mb-4">
              <TabsTrigger value="natural">
                <Sparkles className="h-3 w-3 mr-2" />
                Natural Language
              </TabsTrigger>
              <TabsTrigger value="code">
                <Code className="h-3 w-3 mr-2" />
                Code Editor
              </TabsTrigger>
              <TabsTrigger value="visual">Visual Builder</TabsTrigger>
            </TabsList>

            <TabsContent value="natural" className="space-y-4">
              <Textarea
                placeholder="Describe your strategy... e.g., 'Buy when RSI crosses below 30 and the price is near the lower Bollinger Band, with volume at least 1.5x average. Sell when RSI exceeds 70.'"
                value={nlInput}
                onChange={(e) => setNlInput(e.target.value)}
                className="min-h-[120px]"
              />
              <div className="flex gap-2">
                <Button
                  onClick={handleGenerate}
                  disabled={generating || !nlInput.trim()}
                  className="flex-1 gap-2"
                >
                  <Sparkles className="h-4 w-4" />
                  {generating ? "Generating..." : "Generate Strategy"}
                </Button>
              </div>

              {generatedCode && (
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <label className="text-sm font-medium">Generated Code</label>
                    <div className="flex gap-2">
                      <Badge variant="success">Ready</Badge>
                      <Button variant="ghost" size="sm">
                        <Copy className="h-3 w-3 mr-1" />
                        Copy
                      </Button>
                    </div>
                  </div>
                  <ScrollArea className="h-[200px] rounded-lg border border-border bg-muted/50 p-4">
                    <pre className="text-xs font-mono leading-relaxed">
                      {generatedCode}
                    </pre>
                  </ScrollArea>
                  <div className="flex gap-2 pt-2">
                    <Button className="flex-1 gap-2">
                      <BarChart3 className="h-4 w-4" />
                      Backtest Strategy
                    </Button>
                    <Button variant="outline" className="gap-2">
                      <Edit3 className="h-4 w-4" />
                      Edit Code
                    </Button>
                  </div>
                </div>
              )}
            </TabsContent>

            <TabsContent value="code">
              <div className="space-y-4">
                <div className="flex gap-2">
                  <Input placeholder="Strategy name" className="flex-1" />
                  <Input placeholder="Symbol (e.g., AAPL)" className="w-32" />
                </div>
                <ScrollArea className="h-[300px] rounded-lg border border-border bg-muted/50 p-4 font-mono text-sm">
                  <pre className="leading-relaxed">{`# Write your strategy logic here
def should_enter(data):
    # TODO: implement entry logic
    return False

def should_exit(data):
    # TODO: implement exit logic  
    return False

def position_size(capital, price):
    # Position sizing logic
    return int(capital * 0.02 / price)
`}</pre>
                </ScrollArea>
                <div className="flex gap-2">
                  <Button className="gap-2">
                    <Code className="h-4 w-4" />
                    Validate
                  </Button>
                  <Button variant="outline" className="gap-2">
                    <BarChart3 className="h-4 w-4" />
                    Backtest
                  </Button>
                </div>
              </div>
            </TabsContent>

            <TabsContent value="visual">
              <div className="text-center py-12 text-muted-foreground">
                <p>Visual strategy builder coming soon.</p>
                <p className="text-sm mt-1">
                  Use Natural Language or Code Editor for now.
                </p>
              </div>
            </TabsContent>
          </Tabs>
        </DialogContent>
      </Dialog>
    </div>
  )
}
