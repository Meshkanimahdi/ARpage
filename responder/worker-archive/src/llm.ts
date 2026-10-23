import Anthropic from "@anthropic-ai/sdk";
import type { Llm } from "./types";

/** One fast Claude call: cached system prompt, low effort, no extended thinking, ~200 output tokens. */
export function anthropicLlm(apiKey: string, model: string): Llm {
  const client = new Anthropic({ apiKey, maxRetries: 0 });
  return async (system, user, signal) => {
    const params: any = {
      model,
      max_tokens: 220,
      system: [{ type: "text", text: system, cache_control: { type: "ephemeral" } }],
      messages: [{ role: "user", content: user }],
      output_config: { effort: "low" },
      thinking: { type: "between_tools" }, // Sonnet 5.5: thinking off (disabled is a 400)
    };
    const res: any = await client.messages.create(params, { signal });
    return (res.content as any[]).filter((b) => b.type === "text").map((b) => b.text).join("");
  };
}
