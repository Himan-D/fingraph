"use client"

import Link from "next/link"
import { Button } from "@/components/ui/button"
import { GlassCard } from "@/components/ui/glass-card"
import { Badge } from "@/components/ui/badge"
import { Check, TrendingUp, ArrowRight, Star } from "lucide-react"

const plans = [
  {
    name: "Free",
    price: "$0",
    description: "Get started with paper trading",
    features: [
      "Paper trading simulator",
      "Basic AI insights (10 queries/day)",
      "Delayed market data (15 min)",
      "1 strategy",
      "Basic backtesting (3 months)",
      "Trading journal",
    ],
    cta: "Get started",
    popular: false,
    href: "/signup",
  },
  {
    name: "Pro",
    price: "$29",
    period: "/month",
    description: "For serious traders",
    features: [
      "Everything in Free",
      "Unlimited AI queries",
      "Real-time market data",
      "10 strategies",
      "Full backtesting (10 years)",
      "Live trading (1 broker)",
      "Trading bot deployment",
      "Advanced risk controls",
      "Email + push alerts",
    ],
    cta: "Start free trial",
    popular: true,
    href: "/signup?plan=pro",
  },
  {
    name: "Enterprise",
    price: "$99",
    period: "/month",
    description: "For teams and institutions",
    features: [
      "Everything in Pro",
      "5 team seats",
      "API access (rate: 1000/min)",
      "White label option",
      "Unlimited strategies",
      "Multiple broker connections",
      "Priority support (24/7)",
      "Custom integrations",
      "SLA guarantee",
    ],
    cta: "Contact sales",
    popular: false,
    href: "/contact",
  },
]

export default function PricingPage() {
  return (
    <div className="min-h-screen bg-background">
      <nav className="fixed top-0 left-0 right-0 z-50 border-b border-border bg-background/80 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <Link href="/" className="flex items-center gap-2">
              <TrendingUp className="h-6 w-6 text-primary" />
              <span className="text-lg font-bold">
                Trade<span className="text-primary">Forge</span>
              </span>
            </Link>
            <div className="flex items-center gap-4">
              <Link href="/login">
                <Button variant="ghost">Sign in</Button>
              </Link>
              <Link href="/signup">
                <Button>Get started</Button>
              </Link>
            </div>
          </div>
        </div>
      </nav>

      <section className="pt-32 pb-20 px-4">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h1 className="text-4xl sm:text-5xl font-bold mb-4">
              Simple, transparent pricing
            </h1>
            <p className="text-lg text-muted-foreground max-w-xl mx-auto">
              Choose the plan that fits your trading style. Upgrade anytime.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-6 max-w-5xl mx-auto">
            {plans.map((plan) => (
              <GlassCard
                key={plan.name}
                className={`relative p-8 ${
                  plan.popular
                    ? "border-primary/50 shadow-[0_0_40px_rgba(0,200,83,0.15)]"
                    : ""
                }`}
              >
                {plan.popular && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                    <Badge className="gap-1 px-3 py-1">
                      <Star className="h-3 w-3" />
                      Most popular
                    </Badge>
                  </div>
                )}
                <div className="mb-8">
                  <h3 className="text-2xl font-bold mb-2">{plan.name}</h3>
                  <p className="text-sm text-muted-foreground mb-6">
                    {plan.description}
                  </p>
                  <div className="flex items-baseline gap-1">
                    <span className="text-5xl font-bold">{plan.price}</span>
                    {plan.period && (
                      <span className="text-muted-foreground">{plan.period}</span>
                    )}
                  </div>
                </div>
                <ul className="space-y-4 mb-8">
                  {plan.features.map((feature) => (
                    <li key={feature} className="flex items-start gap-3 text-sm">
                      <Check className="h-4 w-4 text-primary mt-0.5 shrink-0" />
                      {feature}
                    </li>
                  ))}
                </ul>
                <Link href={plan.href}>
                  <Button
                    className="w-full h-12 text-base"
                    variant={plan.popular ? "default" : "outline"}
                  >
                    {plan.cta}
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </Button>
                </Link>
              </GlassCard>
            ))}
          </div>
        </div>
      </section>
    </div>
  )
}
