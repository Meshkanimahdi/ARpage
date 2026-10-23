import { decide } from "./decide";
import { parseWebhook, verifySignature } from "./instagram";
import { fetchCaption, replyToComment, sendDm } from "./transport";
import { anthropicLlm } from "./llm";
export { Poller } from "./poller";
import type { Decision, Env, Incoming, Llm, PostContext } from "./types";

const DAY = 86400;

export interface Deps {
  llm: Llm;
}

async function loadPost(env: Env, mediaId: string | undefined): Promise<PostContext | null> {
  if (!mediaId) return null;
  const hit = await env.KV.get<PostContext>(`post:${mediaId}`, "json");
  if (hit) return hit;
  // Cache miss (post not registered by the publisher): one Graph lookup, then cached.
  const caption = await fetchCaption(env, mediaId).catch(() => null);
  if (!caption) return null;
  const ctx: PostContext = { media_id: mediaId, topic: "(derived from caption)", caption };
  await env.KV.put(`post:${mediaId}`, JSON.stringify(ctx), { expirationTtl: 30 * DAY });
  return ctx;
}

export async function handleOne(env: Env, msg: Incoming, t0: number, deps: Deps): Promise<void> {
  if (await env.KV.get(`seen:${msg.id}`)) return; // Meta retries deliveries
  await env.KV.put(`seen:${msg.id}`, "1", { expirationTtl: DAY });

  const turnKey = `turns:${msg.kind === "dm" ? "dm" : msg.mediaId}:${msg.userId}`;
  const priorReplies = Number((await env.KV.get(turnKey)) ?? 0);
  const post = msg.kind === "comment" ? await loadPost(env, msg.mediaId) : null;

  const tLlm = Date.now();
  const d: Decision = await decide(msg, post, deps.llm, { ownUserId: env.IG_USER_ID, ownUsername: env.IG_USERNAME, priorReplies, now: Date.now() }, Number(env.LLM_TIMEOUT_MS) || 3500);
  const llmMs = Date.now() - tLlm;

  let sent = false;
  let error: string | undefined;
  const dry = env.DRY_RUN !== "0";
  if (d.action === "reply" && d.text) {
    try {
      if (!dry) await (msg.kind === "comment" ? replyToComment(env, msg.id, d.text) : sendDm(env, msg.userId, d.text));
      sent = !dry;
      await env.KV.put(turnKey, String(priorReplies + 1), { expirationTtl: msg.kind === "dm" ? DAY : 30 * DAY });
    } catch (e) {
      error = (e as Error).message;
    }
  }
  const latencyMs = Date.now() - (msg.timestampMs ? Math.min(t0, msg.timestampMs) : t0);
  const day = new Date().toISOString().slice(0, 10);
  await env.KV.put(
    `log:${day}:${String(t0).padStart(13, "0")}:${msg.id}`,
    JSON.stringify({ at: new Date(t0).toISOString(), kind: msg.kind, user: msg.username ?? msg.userId, media: msg.mediaId, text: msg.text.slice(0, 300), action: d.action, reason: d.reason, reply: d.text, flag: d.flag === true, sent, dry, error, latency_ms: latencyMs, llm_ms: llmMs, detect_ms: t0 - (msg.timestampMs ?? t0), over_budget: latencyMs > 5000 }),
    { expirationTtl: 45 * DAY },
  );
}

async function admin(req: Request, env: Env, url: URL): Promise<Response> {
  if (!env.ADMIN_TOKEN || req.headers.get("Authorization") !== `Bearer ${env.ADMIN_TOKEN}`) return new Response("forbidden", { status: 403 });
  if (url.pathname === "/admin/events") {
    const date = url.searchParams.get("date") ?? new Date().toISOString().slice(0, 10);
    const events: unknown[] = [];
    let cursor: string | undefined;
    do {
      const page: KVNamespaceListResult<unknown, string> = await env.KV.list({ prefix: `log:${date}:`, cursor });
      for (const k of page.keys) events.push(await env.KV.get(k.name, "json"));
      cursor = page.list_complete ? undefined : page.cursor;
    } while (cursor);
    return Response.json(events);
  }
  const m = url.pathname.match(/^\/admin\/post\/(\d+)$/);
  if (m && req.method === "PUT") {
    const body = (await req.json()) as Partial<PostContext>;
    if (!body.caption || !body.topic) return new Response("caption and topic required", { status: 400 });
    const ctx: PostContext = { media_id: m[1], topic: body.topic, caption: body.caption, allowed_claims: body.allowed_claims };
    await env.KV.put(`post:${m[1]}`, JSON.stringify(ctx), { expirationTtl: 90 * DAY });
    return Response.json({ ok: true });
  }
  return new Response("not found", { status: 404 });
}

export default {
  /** Cron safety net: make sure the poller loop is alive (idempotent). */
  async scheduled(_e: ScheduledEvent, env: Env, ctx: ExecutionContext) {
    if (env.TRANSPORT === "composio") ctx.waitUntil(env.POLLER.get(env.POLLER.idFromName("main")).fetch("https://poller/admin/poller/start", { method: "POST" }));
  },
  async fetch(req: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const t0 = Date.now();
    const url = new URL(req.url);
    if (url.pathname === "/health") return new Response("ok");
    if (url.pathname.startsWith("/admin/poller/")) {
      if (!env.ADMIN_TOKEN || req.headers.get("Authorization") !== `Bearer ${env.ADMIN_TOKEN}`) return new Response("forbidden", { status: 403 });
      return env.POLLER.get(env.POLLER.idFromName("main")).fetch(req);
    }
    if (url.pathname.startsWith("/admin/")) return admin(req, env, url);
    if (url.pathname !== "/webhook") return new Response("not found", { status: 404 });

    if (req.method === "GET") {
      const ok = url.searchParams.get("hub.mode") === "subscribe" && url.searchParams.get("hub.verify_token") === env.WEBHOOK_VERIFY_TOKEN;
      return ok ? new Response(url.searchParams.get("hub.challenge") ?? "") : new Response("forbidden", { status: 403 });
    }
    if (req.method !== "POST") return new Response("method not allowed", { status: 405 });

    const body = await req.text();
    if (!(await verifySignature(env.IG_APP_SECRET, body, req.headers.get("X-Hub-Signature-256")))) return new Response("bad signature", { status: 403 });

    let items: Incoming[] = [];
    try {
      items = parseWebhook(JSON.parse(body));
    } catch {
      /* ignore malformed payloads, still 200 */
    }
    const deps: Deps = { llm: anthropicLlm(env.ANTHROPIC_API_KEY, env.MODEL) };
    // Return 200 immediately; do the work after the response.
    ctx.waitUntil(Promise.allSettled(items.map((m) => handleOne(env, m, t0, deps))));
    return new Response("EVENT_RECEIVED");
  },
};
