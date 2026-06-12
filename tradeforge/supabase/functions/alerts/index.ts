import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from "https://esm.sh/@supabase/supabase-js@2"

serve(async (req) => {
  const supabase = createClient(
    Deno.env.get("SUPABASE_URL")!,
    Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!
  )

  const { data: activeAlerts } = await supabase
    .from("alerts")
    .select("*")
    .eq("is_active", true)

  if (!activeAlerts?.length) {
    return new Response(JSON.stringify({ checked: 0, triggered: 0 }), {
      headers: { "Content-Type": "application/json" },
    })
  }

  let triggered = 0

  for (const alert of activeAlerts) {
    try {
      const { data: quote } = await supabase
        .from("market_data_cache")
        .select("*")
        .eq("symbol", alert.symbol)
        .order("timestamp", { ascending: false })
        .limit(1)
        .single()

      if (!quote) continue

      const price = quote.close
      const condition = alert.condition
      let isTriggered = false

      switch (condition.operator) {
        case "above":
          isTriggered = price > condition.value
          break
        case "below":
          isTriggered = price < condition.value
          break
        case "crosses_above":
          // Would need two data points
          break
      }

      if (isTriggered) {
        await supabase.from("alert_history").insert({
          alert_id: alert.id,
          symbol: alert.symbol,
          triggered_at: new Date().toISOString(),
          value: price,
          condition: condition,
        })

        await supabase.from("alerts").update({
          last_triggered: new Date().toISOString(),
        }).eq("id", alert.id)

        triggered++
      }
    } catch {
      continue
    }
  }

  return new Response(JSON.stringify({ checked: activeAlerts.length, triggered }), {
    headers: { "Content-Type": "application/json" },
  })
})
