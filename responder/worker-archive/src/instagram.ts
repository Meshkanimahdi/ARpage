import type { Env, Incoming } from "./types";

const enc = new TextEncoder();

function hex(buf: ArrayBuffer): string {
  return [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

export async function sign(secret: string, body: string): Promise<string> {
  const key = await crypto.subtle.importKey("raw", enc.encode(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  return "sha256=" + hex(await crypto.subtle.sign("HMAC", key, enc.encode(body)));
}

/** X-Hub-Signature-256 check, constant-time over equal-length hex strings. */
export async function verifySignature(secret: string, body: string, header: string | null): Promise<boolean> {
  if (!secret || !header) return false;
  const expected = await sign(secret, body);
  if (expected.length !== header.length) return false;
  let diff = 0;
  for (let i = 0; i < expected.length; i++) diff |= expected.charCodeAt(i) ^ header.charCodeAt(i);
  return diff === 0;
}

/** Flatten a webhook payload (object "instagram") into incoming items. Echoes and non-text events are dropped. */
export function parseWebhook(payload: any): Incoming[] {
  const out: Incoming[] = [];
  for (const entry of payload?.entry ?? []) {
    for (const ch of entry.changes ?? []) {
      if (ch.field !== "comments" && ch.field !== "live_comments") continue;
      const v = ch.value ?? {};
      if (!v.id || !v.from?.id || typeof v.text !== "string") continue;
      out.push({
        kind: "comment",
        id: String(v.id),
        userId: String(v.from.id),
        username: v.from.username,
        text: v.text,
        mediaId: v.media?.id ? String(v.media.id) : undefined,
        parentId: v.parent_id ? String(v.parent_id) : undefined,
      });
    }
    for (const m of entry.messaging ?? []) {
      const msg = m.message;
      if (!msg || msg.is_echo || typeof msg.text !== "string" || !msg.mid || !m.sender?.id) continue;
      out.push({ kind: "dm", id: String(msg.mid), userId: String(m.sender.id), text: msg.text, timestampMs: Number(m.timestamp) || undefined });
    }
  }
  return out;
}

function graph(env: Env, path: string): string {
  return `https://graph.instagram.com/${env.GRAPH_VERSION}/${path}`;
}

async function post(env: Env, url: string, body: unknown): Promise<void> {
  const res = await fetch(url, {
    method: "POST",
    headers: { Authorization: `Bearer ${env.IG_ACCESS_TOKEN}`, "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`instagram ${res.status}: ${(await res.text()).slice(0, 200)}`);
}

export function replyToComment(env: Env, commentId: string, text: string) {
  return post(env, graph(env, `${commentId}/replies`), { message: text });
}

export function sendDm(env: Env, recipientId: string, text: string) {
  return post(env, graph(env, "me/messages"), { recipient: { id: recipientId }, message: { text } });
}

export async function fetchCaption(env: Env, mediaId: string): Promise<string | null> {
  const res = await fetch(graph(env, `${mediaId}?fields=caption`), { headers: { Authorization: `Bearer ${env.IG_ACCESS_TOKEN}` } });
  if (!res.ok) return null;
  return ((await res.json()) as any).caption ?? null;
}
