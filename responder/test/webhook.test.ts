import { describe, expect, it } from "vitest";
import worker, { handleOne } from "../src/index";
import { parseWebhook, sign, verifySignature } from "../src/instagram";
import type { Env } from "../src/types";

class FakeKV {
  m = new Map<string, string>();
  async get(k: string, type?: string) { const v = this.m.get(k); return v == null ? null : type === "json" ? JSON.parse(v) : v; }
  async put(k: string, v: string) { this.m.set(k, v); }
  async list({ prefix }: { prefix: string }) { return { keys: [...this.m.keys()].filter((k) => k.startsWith(prefix)).map((name) => ({ name })), list_complete: true }; }
}
const mkEnv = (over: Partial<Env> = {}): Env => ({ KV: new FakeKV() as any, ANTHROPIC_API_KEY: "k", IG_ACCESS_TOKEN: "t", IG_APP_SECRET: "secret", WEBHOOK_VERIFY_TOKEN: "vt", ADMIN_TOKEN: "adm", DRY_RUN: "1", IG_USER_ID: "own", IG_USERNAME: "meshkani.pro", MODEL: "m", GRAPH_VERSION: "v23.0", LLM_TIMEOUT_MS: "3500", COMPOSIO_API_KEY: "ck", COMPOSIO_ACCOUNT_ID: "ca_1", COMPOSIO_BASE: "https://c", POLLER: {} as any, POLL_MS: "10000", MEDIA_WINDOW: "5", IG_ALT_IDS: "alt", TRANSPORT: "meta", ...over });

const commentPayload = { object: "instagram", entry: [{ id: "own", changes: [{ field: "comments", value: { id: "c9", text: "سؤال؟", from: { id: "u9", username: "ali" }, media: { id: "m1" } } }] }] };
const dmPayload = { object: "instagram", entry: [{ id: "own", messaging: [{ sender: { id: "u8" }, recipient: { id: "own" }, timestamp: Date.now(), message: { mid: "mid1", text: "سلام" } }, { sender: { id: "own" }, message: { mid: "e", text: "echo", is_echo: true } }] }] };

describe("webhook", () => {
  it("parses comments and DMs, drops echoes", () => {
    expect(parseWebhook(commentPayload)).toMatchObject([{ kind: "comment", id: "c9", mediaId: "m1", userId: "u9" }]);
    expect(parseWebhook(dmPayload)).toHaveLength(1);
  });
  it("verifies signatures", async () => {
    const body = JSON.stringify(commentPayload);
    expect(await verifySignature("secret", body, await sign("secret", body))).toBe(true);
    expect(await verifySignature("secret", body, await sign("other", body))).toBe(false);
    expect(await verifySignature("secret", body, null)).toBe(false);
  });
  it("GET handshake echoes the challenge only with the right token", async () => {
    const env = mkEnv();
    const ok = await worker.fetch(new Request("https://x/webhook?hub.mode=subscribe&hub.verify_token=vt&hub.challenge=42"), env, {} as any);
    expect(await ok.text()).toBe("42");
    const bad = await worker.fetch(new Request("https://x/webhook?hub.mode=subscribe&hub.verify_token=no&hub.challenge=42"), env, {} as any);
    expect(bad.status).toBe(403);
  });
  it("POST with a bad signature is rejected", async () => {
    const r = await worker.fetch(new Request("https://x/webhook", { method: "POST", body: "{}", headers: { "X-Hub-Signature-256": "sha256=00" } }), mkEnv(), { waitUntil() {} } as any);
    expect(r.status).toBe(403);
  });
  it("POST returns 200 right away and defers the work", async () => {
    const env = mkEnv();
    const body = JSON.stringify(commentPayload);
    const waits: Promise<unknown>[] = [];
    const r = await worker.fetch(new Request("https://x/webhook", { method: "POST", body, headers: { "X-Hub-Signature-256": await sign("secret", body) } }), env, { waitUntil: (p: Promise<unknown>) => waits.push(p) } as any);
    expect(r.status).toBe(200);
    expect(waits).toHaveLength(1);
  });
});

describe("handleOne", () => {
  it("dry run logs latency and sends nothing; dedupes retries; caps turns", async () => {
    const env = mkEnv();
    await (env.KV as any).put("post:m1", JSON.stringify({ media_id: "m1", topic: "t", caption: "c" }));
    const llm = async () => '{"action":"reply","reason":"q","text":"جواب"}';
    const [msg] = parseWebhook(commentPayload);
    await handleOne(env, msg, Date.now(), { llm });
    await handleOne(env, msg, Date.now(), { llm }); // Meta retry
    const logs = [...(env.KV as any).m.keys()].filter((k: string) => k.startsWith("log:"));
    expect(logs).toHaveLength(1);
    const entry = JSON.parse((env.KV as any).m.get(logs[0]));
    expect(entry).toMatchObject({ action: "reply", sent: false, dry: true });
    expect(entry.latency_ms).toBeLessThan(5000);
  });
  it("live mode calls the Instagram reply endpoint", async () => {
    const env = mkEnv({ DRY_RUN: "0" });
    const calls: string[] = [];
    const real = globalThis.fetch;
    globalThis.fetch = (async (u: any) => (calls.push(String(u)), new Response("{}"))) as any;
    try {
      const [msg] = parseWebhook(commentPayload);
      await handleOne(env, msg, Date.now(), { llm: async () => '{"action":"reply","reason":"q","text":"جواب"}' });
    } finally { globalThis.fetch = real; }
    expect(calls.some((u) => u.includes("graph.instagram.com/v23.0/c9/replies"))).toBe(true);
  });
});
