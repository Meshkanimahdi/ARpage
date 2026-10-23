// Local dry-run: prints decisions, never calls Instagram.
//   npm run dry                 -> prefilter only (no API key needed), shows which cases reach the LLM
//   ANTHROPIC_API_KEY=... npm run eval  -> real model on all examples, compares with expected action
import examples from "../examples.json";
import { decide } from "../src/decide";
import { anthropicLlm } from "../src/llm";
import type { Incoming, Llm } from "../src/types";

const live = process.argv.includes("--live");
const key = process.env.ANTHROPIC_API_KEY;
if (live && !key) {
  console.error("Set ANTHROPIC_API_KEY in your shell for --live (never paste it in chat).");
  process.exit(1);
}
const llm: Llm = live ? anthropicLlm(key!, process.env.MODEL ?? "claude-sonnet-5-5") : async () => '{"action":"ignore","reason":"(no llm in offline dry run)"}';

let ok = 0;
for (const c of examples.cases) {
  const msg: Incoming = { kind: c.kind as "comment" | "dm", id: String(c.id), userId: "u" + c.id, text: c.text, mediaId: "FIXTURE_1", timestampMs: Date.now() };
  const t = Date.now();
  const d = await decide(msg, examples.fixture_post, llm, { ownUserId: "own", priorReplies: 0, now: Date.now() });
  const ms = Date.now() - t;
  const match = d.action === c.action;
  if (match) ok++;
  console.log(`#${c.id} [${c.label}] expected=${c.action} got=${d.action}${live ? (match ? " ✓" : " ✗") : ""} ${ms}ms flag=${d.flag ?? false}\n   reason: ${d.reason}${d.text ? `\n   reply: ${d.text}` : ""}`);
}
if (live) console.log(`\n${ok}/${examples.cases.length} actions match expected`);
