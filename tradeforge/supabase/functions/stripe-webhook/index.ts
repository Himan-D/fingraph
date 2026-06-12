import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from "https://esm.sh/@supabase/supabase-js@2"

serve(async (req) => {
  const signature = req.headers.get("stripe-signature")
  const body = await req.text()

  const stripeSecret = Deno.env.get("STRIPE_WEBHOOK_SECRET")
  if (!stripeSecret) {
    return new Response(JSON.stringify({ error: "Webhook secret not configured" }), { status: 500 })
  }

  try {
    const event = JSON.parse(body)

    const supabase = createClient(
      Deno.env.get("SUPABASE_URL")!,
      Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!
    )

    switch (event.type) {
      case "checkout.session.completed": {
        const session = event.data.object
        const userId = session.client_reference_id
        const plan = session.metadata?.plan || "pro"

        await supabase.from("subscriptions").upsert({
          user_id: userId,
          plan,
          status: "active",
          stripe_subscription_id: session.subscription || session.id,
          current_period_end: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
        })

        await supabase.from("profiles").update({ plan }).eq("id", userId)
        break
      }

      case "customer.subscription.updated":
      case "customer.subscription.deleted": {
        const subscription = event.data.object
        await supabase.from("subscriptions").update({
          status: subscription.status === "active" ? "active" : "canceled",
          current_period_end: new Date(subscription.current_period_end * 1000).toISOString(),
        }).eq("stripe_subscription_id", subscription.id)
        break
      }
    }

    return new Response(JSON.stringify({ received: true }), {
      headers: { "Content-Type": "application/json" },
    })
  } catch (err) {
    return new Response(JSON.stringify({ error: err.message }), { status: 400 })
  }
})
