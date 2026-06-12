import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from "https://esm.sh/@supabase/supabase-js@2"

serve(async (req) => {
  const { message, conversation_id, api_key } = await req.json()

  const supabase = createClient(
    Deno.env.get("SUPABASE_URL")!,
    Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!
  )

  const openAIKey = api_key || Deno.env.get("OPENAI_API_KEY")
  const claudeKey = Deno.env.get("CLAUDE_API_KEY")

  const { data: history } = await supabase
    .from("messages")
    .select("role, content")
    .eq("conversation_id", conversation_id)
    .order("created_at", { ascending: true })

  const systemPrompt = `You are TradeForge AI, a professional trading copilot. You help traders analyze markets, build strategies, and make informed decisions.

You have access to market data and can:
- Analyze stocks and market conditions
- Explain technical and fundamental analysis
- Generate trading strategies in Python
- Backtest strategies
- Provide risk management advice
- Suggest portfolio allocations

Be concise, data-driven, and always include risk warnings. Use markdown formatting.`

  const messages = [
    { role: "system", content: systemPrompt },
    ...(history || []).slice(-10),
    { role: "user", content: message },
  ]

  if (openAIKey) {
    const res = await fetch("https://api.openai.com/v1/chat/completions", {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${openAIKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        model: "gpt-4",
        messages,
        temperature: 0.7,
        stream: true,
      }),
    })

    const { readable, writable } = new TransformStream()
    res.body!.pipeTo(writable)

    // Store the message
    const encoder = new TextEncoder()
    const reader = readable.getReader()
    const chunks: string[] = []

    const stream = new ReadableStream({
      async start(controller) {
        while (true) {
          const { done, value } = await reader.read()
          if (done) break
          const text = new TextDecoder().decode(value)
          chunks.push(text)
          controller.enqueue(value)
        }

        const fullContent = chunks.join("")
        await supabase.from("messages").insert({
          conversation_id,
          role: "assistant",
          content: fullContent,
        })

        controller.close()
      },
    })

    return new Response(stream, {
      headers: { "Content-Type": "text/event-stream" },
    })
  }

  return new Response(JSON.stringify({ error: "No AI API key configured" }), { status: 400 })
})
