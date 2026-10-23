import type { Env } from "./types";

/**
 * Execute one Composio action. Endpoint shape (v3 tools/execute) is isolated here:
 * verify with the first live call (COMPOSIO_BASE is overridable).
 * Returns the Graph response (`data` of the envelope); throws on {successful:false}.
 */
export async function composio(env: Env, slug: string, args: Record<string, unknown>): Promise<any> {
  if (!env.COMPOSIO_ACCOUNT_ID) throw new Error("COMPOSIO_ACCOUNT_ID not set: refusing to use a default account");
  const res = await fetch(`${env.COMPOSIO_BASE}/api/v3/tools/execute/${slug}`, {
    method: "POST",
    headers: { "x-api-key": env.COMPOSIO_API_KEY, "Content-Type": "application/json" },
    body: JSON.stringify({ connected_account_id: env.COMPOSIO_ACCOUNT_ID, arguments: args }),
  });
  const j: any = await res.json().catch(() => ({}));
  if (!res.ok || j.successful === false || j.data?.successful === false) {
    throw new Error(`composio ${slug} ${res.status}: ${String(j.error ?? j.data?.error ?? "").slice(0, 200)}`);
  }
  return j.data ?? {}; // Graph response, e.g. {data:[...], paging}
}
