import { afterEach, describe, expect, it } from "vitest";
import { pollOnce } from "../src/poller";
import { handleOne } from "../src/index";
import type { Env } from "../src/types";

class FakeKV {
  m = new Map<string, string>();
  async get(k: string, type?: string) { const v = this.m.get(k); return v == null ? null : type === "json" ? JSON.parse(v) : v; }
  async put(k: string, v: string) { this.m.set(k, v); }
}
const mkEnv = (over: Partial<Env> = {}): Env => ({ KV: new FakeKV() as any, ANTHROPIC_API_KEY: "k", IG_ACCESS_TOKEN: "", IG_APP_SECRET: "", WEBHOOK_VERIFY_TOKEN: "", ADMIN_TOKEN: "a", DRY_RUN: "0", IG_USER_ID: "own", IG_USERNAME: "meshkani.pro", MODEL: "m", GRAPH_VERSION: "v23.0", LLM_TIMEOUT_MS: "3500", COMPOSIO_API_KEY: "ck", COMPOSIO_ACCOUNT_ID: "ca_1", COMPOSIO_BASE: "https://c", POLLER: {} as any, POLL_MS: "10000", MEDIA_WINDOW: "5", IG_ALT_IDS: "alt", TRANSPORT: "composio", ...over });

const NOW = Date.parse("2026-10-23T20:00:00Z");
const iso = (ms: number) => new Date(ms).toISOString().replace("Z", "+0000");
let calls: { slug: string; args: any }[] = [];
const realFetch = globalThis.fetch;
function fakeComposio(handlers: Record<string, (a: any) => any>) {
  calls = [];
  globalThis.fetch = (async (url: any, init: any) => {
    const slug = String(url).split("/").pop()!;
    const args = JSON.parse(init.body).arguments;
    calls.push({ slug, args });
    return new Response(JSON.stringify({ successful: true, data: handlers[slug]?.(args) ?? { data: [] } }));
  }) as any;
}
afterEach(() => { globalThis.fetch = realFetch; });

describe("poller", () => {
  it("first start is a baseline: old comments are never answered", async () => {
    const env = mkEnv();
    fakeComposio({
      INSTAGRAM_GET_IG_USER_MEDIA: () => ({ data: [{ id: "m1", username: "meshkani.pro", comments_count: 3 }] }),
      INSTAGRAM_GET_IG_MEDIA_COMMENTS: () => ({ data: [{ id: "old", text: "سؤال؟", username: "ali", from: { id: "u1" }, timestamp: iso(NOW - 3600_000) }] }),
    });
    expect((await pollOnce(env, NOW)).items).toHaveLength(0);
  });
  it("quiet cycle costs 2 calls; a new comment is detected via count change and fetched once", async () => {
    const env = mkEnv();
    await env.KV.put("poller:since", String(NOW - 60_000));
    await env.KV.put("mc:m1", "3");
    let count = 3;
    fakeComposio({
      INSTAGRAM_GET_IG_USER_MEDIA: () => ({ data: [{ id: "m1", username: "meshkani.pro", comments_count: count }] }),
      INSTAGRAM_GET_IG_MEDIA_COMMENTS: () => ({ data: [
        { id: "new", text: "این چطور کار می‌کنه؟", username: "ali", from: { id: "u1" }, timestamp: iso(NOW - 4000) },
        { id: "mine", text: "ممنون", username: "meshkani.pro", from: { id: "own" }, timestamp: iso(NOW - 3000) },
      ] }),
    });
    const quiet = await pollOnce(env, NOW);
    expect(quiet).toMatchObject({ items: [], calls: 2 });
    count = 4;
    const busy = await pollOnce(env, NOW + 10_000);
    expect(busy.items.map((i) => i.id)).toEqual(["new"]);
    expect(busy.items[0]).toMatchObject({ mediaId: "m1", username: "ali" });
  });
  it("stops if the connected account is not meshkani.pro", async () => {
    const env = mkEnv();
    fakeComposio({ INSTAGRAM_GET_IG_USER_MEDIA: () => ({ data: [{ id: "m1", username: "mirror.dev", comments_count: 1 }] }) });
    await expect(pollOnce(env, NOW)).rejects.toThrow(/identity check failed/);
  });
  it("detects a new DM, skips our own message and stale ones", async () => {
    const env = mkEnv();
    await env.KV.put("poller:since", String(NOW - 600_000));
    fakeComposio({
      INSTAGRAM_LIST_ALL_CONVERSATIONS: () => ({ data: [{ id: "cv1", updated_time: iso(NOW - 2000) }] }),
      INSTAGRAM_LIST_ALL_MESSAGES: () => ({ data: [
        { id: "m2", from: { id: "u7", username: "sara" }, message: "سلام", created_time: iso(NOW - 2000) },
        { id: "m1", from: { id: "alt", username: "meshkani.pro" }, message: "جواب ما", created_time: iso(NOW - 90_000) },
        { id: "m0", from: { id: "u7" }, message: "قدیمی", created_time: iso(NOW - 700_000) },
      ] }),
    });
    const r = await pollOnce(env, NOW);
    expect(r.items.map((i) => i.id)).toEqual(["m2"]);
    expect(r.items[0].kind).toBe("dm");
  });
});

describe("composio transport", () => {
  it("replies through INSTAGRAM_POST_IG_COMMENT_REPLIES with the explicit account", async () => {
    const env = mkEnv();
    fakeComposio({ INSTAGRAM_POST_IG_COMMENT_REPLIES: () => ({ id: "r1" }) });
    await handleOne(env, { kind: "comment", id: "c1", userId: "u1", username: "ali", text: "سؤال؟", mediaId: "m1", timestampMs: NOW - 3000 }, Date.now(), { llm: async () => '{"action":"reply","reason":"q","text":"جواب"}' });
    const c = calls.find((x) => x.slug === "INSTAGRAM_POST_IG_COMMENT_REPLIES")!;
    expect(c.args).toEqual({ ig_comment_id: "c1", message: "جواب" });
  });
  it("refuses to run without an explicit connected account", async () => {
    const { composio } = await import("../src/composio");
    await expect(composio(mkEnv({ COMPOSIO_ACCOUNT_ID: "" }), "X", {})).rejects.toThrow(/default account/);
  });
});
