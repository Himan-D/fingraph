import { serve } from "https://deno.land/std@0.168.0/http/server.ts"

const ALPACA_BASE = "https://data.alpaca.markets/v2"
const POLYGON_BASE = "https://api.polygon.io/v2"
const BINANCE_BASE = "https://api.binance.com/api/v3"

serve(async (req) => {
  const { provider, endpoint, params } = await req.json()

  try {
    let data: unknown

    switch (provider) {
      case "alpaca": {
        const apiKey = Deno.env.get("ALPACA_API_KEY")
        const secretKey = Deno.env.get("ALPACA_SECRET_KEY")
        const res = await fetch(`${ALPACA_BASE}${endpoint}?${new URLSearchParams(params)}`, {
          headers: { "APCA-API-KEY-ID": apiKey!, "APCA-API-SECRET-KEY": secretKey! },
        })
        data = await res.json()
        break
      }
      case "polygon": {
        const apiKey = Deno.env.get("POLYGON_API_KEY")
        const res = await fetch(`${POLYGON_BASE}${endpoint}?${new URLSearchParams({ ...params, apiKey: apiKey! })}`)
        data = await res.json()
        break
      }
      case "binance": {
        const res = await fetch(`${BINANCE_BASE}${endpoint}?${new URLSearchParams(params)}`)
        data = await res.json()
        break
      }
      default:
        return new Response(JSON.stringify({ error: "Unknown provider" }), { status: 400 })
    }

    return new Response(JSON.stringify({ data }), {
      headers: { "Content-Type": "application/json" },
    })
  } catch (error) {
    return new Response(JSON.stringify({ error: error.message }), { status: 500 })
  }
})
