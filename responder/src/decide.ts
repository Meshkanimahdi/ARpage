import { buildUserPrompt, SYSTEM_PROMPT } from "./prompt";
import type { Decision, Incoming, Llm, PostContext } from "./types";

const URL_RE = /(https?:\/\/|www\.|\.(com|ir|me|net|org)\b|t\.me\/|wa\.me\/)/i;
const PHONE_RE = /(\+?98|0)9\d{9}/;
const EMOJI_ONLY = /^[\s\p{Extended_Pictographic}\p{Emoji_Component}‍️.!؟?❤♥,،-]*$/u;
const MAX_TURNS_PER_USER = 2;

export interface PrefilterCtx {
  ownUserId: string;
  /** replies already sent to this user on this media/thread (including this one if applicable) */
  priorReplies: number;
  now: number;
}

/** Cheap deterministic gate: runs before the LLM so obvious noise costs nothing and adds no latency. */
export function prefilter(msg: Incoming, ctx: PrefilterCtx): Decision | null {
  if (msg.userId === ctx.ownUserId) return { action: "ignore", reason: "own comment" };
  const t = msg.text.trim();
  if (!t) return { action: "ignore", reason: "empty" };
  if (EMOJI_ONLY.test(t)) return { action: "ignore", reason: "emoji only" };
  if (msg.kind === "comment" && (URL_RE.test(t) || PHONE_RE.test(t))) return { action: "ignore", reason: "link or phone, likely spam" };
  if (ctx.priorReplies >= MAX_TURNS_PER_USER) return { action: "ignore", reason: "turn limit with this user" };
  if (msg.kind === "dm" && msg.timestampMs && ctx.now - msg.timestampMs > 23.5 * 3600_000) {
    return { action: "ignore", reason: "outside 24h messaging window" };
  }
  return null;
}

export function parseDecision(raw: string, kind: Incoming["kind"]): Decision {
  const m = raw.match(/\{[\s\S]*\}/);
  if (!m) return { action: "ignore", reason: "unparseable model output" };
  try {
    const j = JSON.parse(m[0]);
    if (j.action !== "reply") return { action: "ignore", reason: String(j.reason ?? "model ignore").slice(0, 80) };
    const text = String(j.text ?? "").trim();
    if (!text) return { action: "ignore", reason: "empty reply text" };
    if (text.length > 600) return { action: "ignore", reason: "reply too long" };
    return { action: "reply", reason: String(j.reason ?? "").slice(0, 80), text, flag: kind === "dm" ? j.flag === true : false };
  } catch {
    return { action: "ignore", reason: "bad json" };
  }
}

export async function decide(msg: Incoming, post: PostContext | null, llm: Llm, ctx: PrefilterCtx, timeoutMs = 3500): Promise<Decision> {
  const pre = prefilter(msg, ctx);
  if (pre) return pre;
  const ac = new AbortController();
  const timer = setTimeout(() => ac.abort(), timeoutMs);
  try {
    const raw = await llm(SYSTEM_PROMPT, buildUserPrompt(msg, post), ac.signal);
    return parseDecision(raw, msg.kind);
  } catch (e) {
    // A late reply is worse than none (5 s budget): fail closed.
    return { action: "ignore", reason: `llm error: ${(e as Error).name}` };
  } finally {
    clearTimeout(timer);
  }
}
