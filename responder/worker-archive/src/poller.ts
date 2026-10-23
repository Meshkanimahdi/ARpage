import { composio } from "./composio";
import { handleOne } from "./index";
import { anthropicLlm } from "./llm";
import type { Env, Incoming } from "./types";

const MAX_AGE_MS = 15 * 60_000; // never answer anything older than this
const ts = (s?: string) => (s ? Date.parse(s.replace(/\+0000$/, "Z")) || undefined : undefined);

/**
 * Polling transport (Composio has no push trigger for Instagram that we could verify).
 * Per cycle: 1 call lists the newest posts with comments_count; comments are fetched only for posts whose count changed.
 * 1 call lists DM conversations; messages are fetched only for conversations whose updated_time changed.
 * Quiet account => 2 Composio calls per cycle.
 */
export async function pollOnce(env: Env, now = Date.now()): Promise<{ items: Incoming[]; calls: number }> {
  const items: Incoming[] = [];
  let calls = 0;
  const since = Number(await env.KV.get("poller:since")) || now; // baseline: nothing before first start is answered
  if (!(await env.KV.get("poller:since"))) await env.KV.put("poller:since", String(now));
  const mine = new Set([env.IG_USER_ID, ...(env.IG_ALT_IDS || "").split(",").filter(Boolean)]);
  const isMine = (id?: string, username?: string) => (id && mine.has(id)) || username === env.IG_USERNAME;

  // --- comments ---
  calls++;
  const media = await composio(env, "INSTAGRAM_GET_IG_USER_MEDIA", { ig_user_id: "me", limit: Number(env.MEDIA_WINDOW) || 5, fields: "id,caption,username,timestamp,comments_count,media_product_type" });
  for (const m of media.data ?? []) {
    if (m.username && m.username !== env.IG_USERNAME) throw new Error(`identity check failed: connected account is ${m.username}, expected ${env.IG_USERNAME}`);
    const prev = await env.KV.get(`mc:${m.id}`);
    const count = String(m.comments_count ?? 0);
    if (prev === count) continue;
    await env.KV.put(`mc:${m.id}`, count, { expirationTtl: 30 * 86400 });
    if (prev === null && !m.comments_count) continue;
    calls++;
    const list = await composio(env, "INSTAGRAM_GET_IG_MEDIA_COMMENTS", { ig_media_id: m.id, limit: 25, fields: "id,text,username,timestamp,from,parent_id" });
    for (const c of list.data ?? []) {
      const t = ts(c.timestamp);
      if (!t || t < since || now - t > MAX_AGE_MS) continue;
      if (isMine(c.from?.id, c.username)) continue;
      items.push({ kind: "comment", id: String(c.id), userId: String(c.from?.id ?? c.username), username: c.username, text: c.text ?? "", mediaId: String(m.id), parentId: c.parent_id, timestampMs: t });
    }
  }

  // --- DMs ---
  calls++;
  const convs = await composio(env, "INSTAGRAM_LIST_ALL_CONVERSATIONS", { limit: 10, platform: "instagram", fields: "id,updated_time,participants" });
  for (const cv of convs.data ?? []) {
    const prev = await env.KV.get(`cv:${cv.id}`);
    if (prev === cv.updated_time) continue;
    await env.KV.put(`cv:${cv.id}`, String(cv.updated_time), { expirationTtl: 30 * 86400 });
    if (prev === null && (ts(cv.updated_time) ?? 0) < since) continue; // old conversation, first sight
    calls++;
    const msgs = await composio(env, "INSTAGRAM_LIST_ALL_MESSAGES", { conversation_id: cv.id, limit: 5 });
    for (const dm of msgs.data ?? []) {
      const t = ts(dm.created_time);
      if (!t || t < since || now - t > 23 * 3600_000 || !dm.message) continue;
      if (isMine(dm.from?.id, dm.from?.username)) continue;
      items.push({ kind: "dm", id: String(dm.id), userId: String(dm.from.id), username: dm.from?.username, text: dm.message, timestampMs: t });
    }
  }
  return { items, calls };
}

/** Durable Object: alarm loop. /admin/poller/start|stop|status */
export class Poller {
  constructor(private state: DurableObjectState, private env: Env) {}

  async fetch(req: Request): Promise<Response> {
    const path = new URL(req.url).pathname;
    if (path.endsWith("/start")) {
      if (!(await this.state.storage.getAlarm())) await this.state.storage.setAlarm(Date.now() + 500);
      await this.state.storage.put("on", true);
      return Response.json({ running: true });
    }
    if (path.endsWith("/stop")) {
      await this.state.storage.put("on", false);
      await this.state.storage.deleteAlarm();
      return Response.json({ running: false });
    }
    return Response.json({ on: await this.state.storage.get("on"), last: await this.state.storage.get("last") });
  }

  async alarm(): Promise<void> {
    if (!(await this.state.storage.get("on"))) return;
    const started = Date.now();
    let status: unknown = "ok";
    try {
      const { items, calls } = await pollOnce(this.env, started);
      const llm = anthropicLlm(this.env.ANTHROPIC_API_KEY, this.env.MODEL);
      await Promise.allSettled(items.map((m) => handleOne(this.env, m, Date.now(), { llm })));
      status = { items: items.length, calls };
    } catch (e) {
      status = `error: ${(e as Error).message}`;
      if (String(status).includes("identity check failed")) {
        await this.state.storage.put("on", false); // wrong account: stop, do not retry
      }
    }
    await this.state.storage.put("last", { at: new Date().toISOString(), ms: Date.now() - started, status });
    if (await this.state.storage.get("on")) await this.state.storage.setAlarm(Date.now() + Math.max(1000, Number(this.env.POLL_MS) || 10000));
  }
}
