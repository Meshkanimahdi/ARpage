import { describe, expect, it } from "vitest";
import examples from "../examples.json";
import { decide, parseDecision, prefilter } from "../src/decide";
import { buildUserPrompt, SYSTEM_PROMPT } from "../src/prompt";
import type { Incoming, Llm } from "../src/types";

const post = examples.fixture_post;
const ctx = { ownUserId: "own", priorReplies: 0, now: Date.now() };
const mk = (text: string, over: Partial<Incoming> = {}): Incoming => ({ kind: "comment", id: "c1", userId: "u1", text, mediaId: "FIXTURE_1", ...over });

/** Fake model that answers with the expected example for each text: tests the pipeline around the model. */
const oracle: Llm = async (_s, user) => {
  const c = examples.cases.find((x) => user.includes(`<message>\n${x.text}\n</message>`));
  if (!c) return "garbage";
  return JSON.stringify({ action: c.action, reason: c.label, text: c.reply ?? undefined, flag: "flag" in c ? c.flag : false });
};

describe("classifier pipeline, one case per category", () => {
  const byLabel = (l: string) => examples.cases.find((c) => c.label.startsWith(l))!;
  const run = (label: string) => {
    const c = byLabel(label);
    return decide(mk(c.text, { kind: c.kind as any, timestampMs: Date.now() }), post, oracle, ctx);
  };
  it("on-topic serious -> reply", async () => expect((await run("on-topic serious")).action).toBe("reply"));
  it("on-topic joke -> reply", async () => expect((await run("on-topic joke")).action).toBe("reply"));
  it("insult -> ignore", async () => expect((await run("insult")).action).toBe("ignore"));
  it("spam -> ignore", async () => expect((await run("spam")).action).toBe("ignore"));
  it("unrelated -> ignore", async () => expect((await run("unrelated")).action).toBe("ignore"));
  it("emoji only -> ignore without calling the model", async () => {
    let called = false;
    const d = await decide(mk("🔥🔥🔥"), post, async () => ((called = true), "{}"), ctx);
    expect(d).toMatchObject({ action: "ignore", reason: "emoji only" });
    expect(called).toBe(false);
  });
  it("business DM -> reply + flag", async () => {
    const d = await run("business DM: pricing");
    expect(d).toMatchObject({ action: "reply", flag: true });
    expect(d.text).not.toMatch(/\d{3,}/); // no price promised
  });
  it("flag is never set on comments", () => {
    expect(parseDecision('{"action":"reply","text":"سلام","flag":true}', "comment").flag).toBe(false);
  });
});

describe("prefilter", () => {
  it("ignores our own comments", () => expect(prefilter(mk("ممنون"), { ...ctx, ownUserId: "u1" })?.reason).toBe("own comment"));
  it("ignores links and phone numbers in comments", () => {
    expect(prefilter(mk("see https://x.com/a"), ctx)).not.toBeNull();
    expect(prefilter(mk("زنگ بزن 09121234567"), ctx)).not.toBeNull();
  });
  it("caps replies at 2 per user", () => expect(prefilter(mk("سؤال دارم؟"), { ...ctx, priorReplies: 2 })?.reason).toMatch(/turn limit/));
  it("respects the 24h DM window", () => {
    const old = mk("سلام", { kind: "dm", timestampMs: Date.now() - 25 * 3600_000 });
    expect(prefilter(old, ctx)?.reason).toMatch(/24h/);
  });
  it("lets a normal question through", () => expect(prefilter(mk("این چطور کار می‌کنه؟"), ctx)).toBeNull());
});

describe("failure handling", () => {
  it("garbage model output -> ignore", async () => expect((await decide(mk("سؤال؟"), post, async () => "no json", ctx)).action).toBe("ignore"));
  it("model error -> ignore (no late reply)", async () => {
    const d = await decide(mk("سؤال؟"), post, async () => { throw new Error("boom"); }, ctx);
    expect(d.action).toBe("ignore");
  });
  it("timeout -> ignore", async () => {
    const slow: Llm = (_s, _u, signal) => new Promise((_, rej) => signal.addEventListener("abort", () => rej(Object.assign(new Error("x"), { name: "AbortError" }))));
    expect((await decide(mk("سؤال؟"), post, slow, ctx, 30)).reason).toMatch(/AbortError/);
  });
  it("reply action without text -> ignore", () => expect(parseDecision('{"action":"reply"}', "comment").action).toBe("ignore"));
});

describe("prompt", () => {
  it("is byte-stable so it can be cached", () => expect(SYSTEM_PROMPT).toBe(SYSTEM_PROMPT));
  it("carries Mahdi's rules", () => {
    for (const s of ["محاوره‌ای", "1-2 sentences", "At most one emoji", "Never invent", "medical, financial or legal", "Never promise", "untrusted"]) {
      expect(SYSTEM_PROMPT.toLowerCase()).toContain(s.toLowerCase());
    }
  });
  it("has the 15 examples", () => expect(examples.cases).toHaveLength(15));
  it("puts the message inside tags and truncates it", () => {
    const u = buildUserPrompt(mk("x".repeat(5000)), post);
    expect(u).toContain("<message>");
    expect(u.length).toBeLessThan(2000);
  });
  it("tells the model when post context is missing", () => expect(buildUserPrompt(mk("hi"), null)).toContain("not available"));
});
