import { serve } from "https://deno.land/std@0.168.0/http/server.ts"

serve(async (req) => {
  const { description, symbol } = await req.json()

  const apiKey = Deno.env.get("OPENAI_API_KEY")

  const prompt = `Convert this trading strategy description into Python code:

"${description}"

Generate a complete strategy class with:
1. should_enter(data) — returns True/False for entry signal
2. should_exit(data) — returns True/False for exit signal  
3. position_size(capital, price) — returns position size
4. Required indicators (RSI, SMA, MACD, etc.) as helper functions

Use these helper functions:
- compute_rsi(prices, period=14)
- compute_sma(prices, period)
- compute_ema(prices, period)
- compute_macd(prices)
- compute_bollinger_bands(prices, period=20, std=2)

Return ONLY the Python code, no explanation. Include reasonable default parameters.`

  const res = await fetch("https://api.openai.com/v1/chat/completions", {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${apiKey}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      model: "gpt-4",
      messages: [
        { role: "system", content: "You are a professional quant developer. Generate production-quality trading strategy code." },
        { role: "user", content: prompt },
      ],
      temperature: 0.3,
    }),
  })

  const data = await res.json()
  const code = data.choices?.[0]?.message?.content || ""

  return new Response(JSON.stringify({ code, symbol }), {
    headers: { "Content-Type": "application/json" },
  })
})
