export interface Env {
  KV: KVNamespace;
  ANTHROPIC_API_KEY: string;
  IG_ACCESS_TOKEN: string;
  IG_APP_SECRET: string;
  WEBHOOK_VERIFY_TOKEN: string;
  ADMIN_TOKEN: string;
  DRY_RUN: string;
  IG_USER_ID: string;
  IG_USERNAME: string;
  MODEL: string;
  GRAPH_VERSION: string;
  LLM_TIMEOUT_MS: string;
}

export interface PostContext {
  media_id: string;
  topic: string;
  caption: string;
  allowed_claims?: string[];
}

export type IncomingKind = "comment" | "dm";

export interface Incoming {
  kind: IncomingKind;
  id: string; // comment id or message mid
  userId: string;
  username?: string;
  text: string;
  mediaId?: string; // comments only
  parentId?: string; // comment is a reply inside a thread
  timestampMs?: number; // DMs: when the user wrote it
}

export interface Decision {
  action: "reply" | "ignore";
  reason: string;
  text?: string;
  flag?: boolean; // DM needs Mahdi (collaboration, ads, pricing)
}

export type Llm = (system: string, user: string, signal: AbortSignal) => Promise<string>;
