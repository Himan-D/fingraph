import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from "https://esm.sh/@supabase/supabase-js@2"

serve(async (req) => {
  const { bot_id, action } = await req.json()

  const supabase = createClient(
    Deno.env.get("SUPABASE_URL")!,
    Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!
  )

  const { data: bot } = await supabase
    .from("bots")
    .select("*, strategies(*)")
    .eq("id", bot_id)
    .single()

  if (!bot) {
    return new Response(JSON.stringify({ error: "Bot not found" }), { status: 404 })
  }

  switch (action) {
    case "start":
      await supabase.from("bots").update({ status: "running" }).eq("id", bot_id)
      return new Response(JSON.stringify({ status: "running" }), {
        headers: { "Content-Type": "application/json" },
      })

    case "stop":
      await supabase.from("bots").update({ status: "stopped" }).eq("id", bot_id)
      return new Response(JSON.stringify({ status: "stopped" }), {
        headers: { "Content-Type": "application/json" },
      })

    case "status":
      return new Response(JSON.stringify({ status: bot.status }), {
        headers: { "Content-Type": "application/json" },
      })

    case "execute": {
      const { data: quote } = await supabase
        .from("market_data_cache")
        .select("*")
        .eq("symbol", bot.symbol)
        .order("timestamp", { ascending: false })
        .limit(100)

      if (!quote?.length) {
        return new Response(JSON.stringify({ error: "No market data" }), { status: 400 })
      }

      const currentPrice = quote[0].close
      const prices = quote.map((q: Record<string, unknown>) => q.close as number)

      const rsi = computeRSI(prices)
      const sma20 = prices.slice(-20).reduce((a: number, b: number) => a + b, 0) / 20
      const signal = rsi < 30 ? "buy" : rsi > 70 ? "sell" : "hold"

      await supabase.from("bot_logs").insert({
        bot_id,
        action: "signal",
        details: { signal, price: currentPrice, rsi, sma20 },
      })

      return new Response(JSON.stringify({ signal, price: currentPrice, rsi }), {
        headers: { "Content-Type": "application/json" },
      })
    }

    default:
      return new Response(JSON.stringify({ error: "Unknown action" }), { status: 400 })
  }
})

function computeRSI(prices: number[], period = 14): number {
  if (prices.length < period + 1) return 50
  const changes = prices.slice(-period - 1).map((p, i, arr) => i === 0 ? 0 : p - arr[i - 1])
  const gains = changes.filter((c) => c > 0).reduce((a, b) => a + b, 0) / period
  const losses = changes.filter((c) => c < 0).reduce((a, b) => a + Math.abs(b), 0) / period
  if (losses === 0) return 100
  const rs = gains / losses
  return 100 - 100 / (1 + rs)
}
