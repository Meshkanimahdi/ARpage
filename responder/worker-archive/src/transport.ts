// Reply/lookup actions, routed through Composio (default) or the Meta Graph API directly.
import * as meta from "./instagram";
import { composio } from "./composio";
import type { Env } from "./types";

export async function replyToComment(env: Env, commentId: string, text: string): Promise<void> {
  if (env.TRANSPORT !== "composio") return meta.replyToComment(env, commentId, text);
  await composio(env, "INSTAGRAM_POST_IG_COMMENT_REPLIES", { ig_comment_id: commentId, message: text.slice(0, 300) });
}

export async function sendDm(env: Env, recipientId: string, text: string): Promise<void> {
  if (env.TRANSPORT !== "composio") return meta.sendDm(env, recipientId, text);
  await composio(env, "INSTAGRAM_SEND_TEXT_MESSAGE", { recipient_id: recipientId, text });
}

export async function fetchCaption(env: Env, mediaId: string): Promise<string | null> {
  if (env.TRANSPORT !== "composio") return meta.fetchCaption(env, mediaId);
  const r = await composio(env, "INSTAGRAM_GET_IG_MEDIA", { ig_media_id: mediaId, fields: "caption" }).catch(() => null);
  return r?.caption ?? null;
}
