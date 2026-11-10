# Automated production pipeline (posts, stories, reels)

How to run a page's content as a scheduled, unattended system that never double-publishes, never publishes
late, never leaves a slot empty, and still keeps quality. Page-specific values (slots, ids, voice, limits) come
from the brand profile (`brand-profile-template.md`).

## 1. Phases
| phase | when | does |
|---|---|---|
| TOPIC BANK | weekly (e.g. Friday) | research team proposes ≥ 3 topics per slot of next week; the owner ticks (`topics-and-research.md`) |
| ANALYTICS | daily, before the first prepare | measures every item, writes `insights.json` (`analytics-loop.md`) |
| PREPARE | main run ~1.5–2.5 h before the slot, retry ~1 h before | research → concept gate → production → QA → `READY` |
| PUBLISH | starts 3 min before the slot | identity + gates → publish → verify → stories → refresh performance |

Each run is a fresh session told only its phase. Everything it needs is on disk or in shared state.

## 2. State, locks, idempotency
- **One state file per slot** (`slot_YYYY-MM-DD_HHMM.json`) is the source of truth; the sheet is the human view.
  Statuses: `RESEARCHING → DESIGNING → QA → READY → PUBLISHING → PUBLISHED`, plus `SKIPPED_LATE`,
  `SKIPPED_NO_NEWS`, `SKIPPED_KILL_SWITCH`, `SKIPPED_QA`, `FAILED`, `NEEDS_RECONCILIATION`.
- Write state after every status change and **immediately after every platform call that returns an id**.
- **Phase lock** per slot (`<slot>__prepare`, `__prepare_retry`, `__publish`): a run that loses the lock logs
  `DUPLICATE_RUN_STOPPED` and stops.
- **Takeover:** a slot stuck in `RESEARCHING/DESIGNING/QA` for > 15 min with no platform id recorded may be
  taken over; reuse every finished, QA-passed asset.
- **Kill switch + mode** in a control tab: `Kill Switch=ON` stops everything (check again right before every
  publish call); `DRY_RUN` does everything except the publish calls; unreadable = ON.
- **Identity check before publishing:** the account must read back the expected username and id.
- **Duplicate guard:** before publishing, list the latest media; if this caption is already live, record it
  as published instead of posting again.
- **Reconciliation:** after an unclear publish result, never call publish again until you know: check the
  container status and the latest media; one retry on the *same* container only if it is `FINISHED` and
  nothing is live a minute later; otherwise `NEEDS_RECONCILIATION` and stop.
- **Publish window:** slot time → slot + 30 min. A missed slot is never caught up later.
- Never print or store API keys, upload-session URLs or temporary public links; unshare files after use.

## 3. Never an empty slot, never a bad post — both
The tension that broke this pipeline twice:
- **Fail-closed gates with no fallback** left slots empty (every reel failed an 8/10 bar).
- **"Publish first" with no limits** let repeats out (four of six reels on one motion engine).

The rule that resolves it:
1. **Bars 6/10, at most 3 fix rounds** per stage; then take the best version.
2. **Gate results are split** into `hard_fails` and `score_fails` (`quality-gates.md`). Only score fails may
   publish, with a `low_score` note. A hard fail (repeat of engine/prompt family/category/voice/voice gender/
   SFX set/cover element, missing concept gate or preflight, broken file, factual error, policy risk) is
   **never** published.
3. **Backlog first:** an already-rendered unpublished item fills a slot before anything new is made.
4. If neither works: take the next option from the rotation list and rebuild cheaply (code/typography only),
   or skip with a logged reason. Never quietly lower the rule.

## 4. Cost control
- **Images: one or two generation calls per package**, never one per image. Generate boards (a 3×3 grid of
  4:5 panels for a 9-slide carousel, 3×1 of 9:16 for three stories, 4×1 or 6×2 of 9:16 for reels and covers)
  and cut them. A per-package ledger refuses a third call unless an override reason is logged.
- Text is free: fix headlines, layout and crops in code, never by regenerating images.
- Real photos and real logos cost nothing; prefer them.
- Audio: use the voice/music/SFX library first; at most one new generated audio file a day.
- Never re-render a full video for a cover/headline/hook problem: those are caught on stills (preflight).
- Track cost per item in state; report cost per published item weekly.
- When a provider runs out of credit (HTTP 402), tell the owner at once with the exact top-up place, and fall
  back to code-drawn visuals rather than leaving the slot empty. Never reuse old plates silently.

## 5. Model and roles
- One strong model for all content (research, writing, scripts, prompts, design, QC). A run on the wrong
  model still runs (no missed slot) but logs `MODEL_MISMATCH`.
- **You never grade your own work:** every gate's critic is a fresh subagent with no shared context.
- Separate sessions for publishing and for comment/DM replies; if they share a sandbox, never pass data in
  plain globals (a collision wrote comment rows into the stories sheet).

## 6. Rules live in one place, change in one place
- Keep the page's operating rules in a runbook the runs read at start, and **mirror it to a sheet tab** the
  owner can read; resync when the commit changes.
- Every rule the owner gives is recorded with their exact words, the date and the evidence, and is enforced
  in code (a gate) wherever possible. A rule only in prose gets skipped under deadline pressure.
- When a new rule conflicts with an old one, rewrite the old one; never leave both (an old "vary the
  headline position" rule kept failing every reel after "always centre" was introduced).
- Changing rules mid-run breaks the run: apply new rules from the next prepare, and tell the owner which
  slot is the first under the new rule.

## 7. Reporting to the owner
- Live numbers only (fetch them; never quote a stale figure).
- When something fails, say what failed, why, what was done, and what the owner must do (with the exact
  place: "Settings → Credits"), in that order.
- If a published item turns out to be wrong (wrong voice gender, weak cover), say so plainly, offer the fix
  (a new cover file to swap in the app; a corrected re-post), and change the rule so it cannot recur.
