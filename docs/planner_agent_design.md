# Planner Agent Design

**Date:** 2026-03-13
**Status:** Design / Pre-implementation

---

## Overview

Introduce a multi-phase pipeline between the user's request and the coder agent. The new flow is:

```
User Request
    │
    ▼
[Planner Agent]  ─── plan.txt ───►
    │
    ▼ (user optionally reviews)
[Coder Agent]   ◄─── in_message.txt + plan.txt
    │
    ▼
[Code Reviewer] ◄─── in_message.txt + plan.txt + changed_files.txt
    │
    ▼ (up to 3 rounds)
[Coder Agent]   ← fix round
    │
    ▼
Done → history logged
```

---

## Workflow Modes

Three modes give users control over how much process overhead to apply:

| Mode | Trigger Phrase | Planning | Review Rounds |
|------|---------------|----------|---------------|
| **Full** | `start working` | Yes | 3 |
| **Quick** | `start quick` | No | 1 |
| **Simple** | `start simple` | No | 0 |

Agents can override the default `max_review_rounds` in `projects.json`.

---

## Phase Details

### Phase 1: Planning (`plan` mode)

- Agent: same Claude instance, different system prompt focused on planning
- Input: `in_message.txt`
- Output: `.klodTalk/plan_messages/plan.txt`
- Claude is told:
  - Analyse the request
  - Output a concise implementation plan (steps, files to touch, risks)
  - State assumptions explicitly (no interactive Q&A — voice UX doesn't support blocking wait)
  - Do **not** write any code
- Server watches for `plan.txt`, sends it to client as `"plan"` message type
- Client displays the plan in inbox; user can:
  - Add voice corrections and then say "start working" to approve and proceed to EXECUTING
    (the coder agent sees both the updated `in_message.txt` and the original `plan.txt`)
  - Accept the plan as-is by saying "start working" with no new corrections

### Phase 2: Coding (`execute` mode)

- Same as today, but run_agent.sh also receives `plan.txt` in its context
- Claude is told: "Here is the plan — implement it"
- Output: `out_message.txt`, `changed_files.txt`

### Phase 3: Code Review (`review` mode)

- Same as today, but reviewer also receives `plan.txt`
- Reviewer checks code against the plan as well as general quality
- Up to `max_review_rounds` rounds (default 3 for Full, 1 for Quick, 0 for Simple)
- Each round: reviewer → pr_message.txt → coder fixes → re-review

### Phase 4: History Logging

After each session completes, append to `.klodTalk/history/session_TIMESTAMP.md`:

```markdown
# Session 2026-03-13T06:22:29Z  [mode: full]

## User Request
<contents of in_message.txt>

## Plan
<contents of plan.txt>

## Execution Round 1
<out_message.txt>
Changed files: <changed_files.txt>

## Code Review Round 1
<pr_message.txt>

## Execution Round 2
<out_message.txt>
...

## Final State
Completed after N execution rounds.
```

History is written inside the agent's workspace (same Docker volume mount), so it is version-controlled alongside the code.

> **Implementation note:** `out_message.txt` and `pr_message.txt` are overwritten on
> each execution/review round. The server **must snapshot each file immediately after
> the subprocess finishes** (before triggering the next round) and append the snapshot
> to the history file. If the server reads these files only at the end of the session,
> the history will contain only the final round's output repeated N times.

---

## Configuration Changes (`projects.json`)

Add two optional fields per agent:

```json
{
  "name": "...",
  "planning": true,
  "max_review_rounds": 3
}
```

- `planning` (bool, **default `false`**): enables/disables the planner phase.
  The server must treat a missing `planning` field as `false` — agents without the
  field run exactly as today (no planning phase, straight to EXECUTING on "start working").
- `max_review_rounds` (int, 0–3, **default `3`**): maximum code review iterations.
  A missing field is treated as `3` for Full mode, `1` for Quick, and `0` for Simple.

Backward-compatible: existing agents without these fields keep current behaviour.

---

## New Message Types (WebSocket Protocol)

| Direction | Type | Fields | Meaning |
|-----------|------|--------|---------|
| Server → Client | `plan` | `agent`, `content` | Planner output — the plan |
| Server → Client | `ack` | `agent`, `content` | (existing — reused for phase transitions) |

The `"plan"` message is displayed in the inbox like any other message, but with a distinct icon/label ("Plan") so users know it's a planning artifact rather than a final result.

---

## Server State Machine Changes (`server.py`)

Current states (implicit):
```
IDLE → EXECUTING → REVIEWING (×3) → DONE
```

New states:
```
IDLE → PLANNING → PLAN_REVIEW → EXECUTING → REVIEWING (×N) → DONE
           │ (planning=false)       ▲
           └────────────────────────┘  (skip planning; go straight to EXECUTING)
```

After the server sends a `"plan"` message, it enters **PLAN_REVIEW** and waits for an
explicit trigger phrase before proceeding to EXECUTING. This gives users a chance to
voice-correct the plan before any code is written.

New per-agent tracking dictionary:
```python
agent_phase: dict[str, str] = {}       # "planning" | "plan_review" | "executing" | "reviewing" | "idle"
workflow_mode: dict[str, str] = {}     # "full" | "quick" | "simple"
```

Trigger phrase handling:

| Phrase | Valid in states | Action |
|--------|----------------|--------|
| `start working` | IDLE | workflow_mode = "full"; if `planning=true` → PLANNING; else → EXECUTING |
| `start quick` | IDLE, PLAN_REVIEW | workflow_mode = "quick"; skip/abort planning → EXECUTING; max 1 review |
| `start simple` | IDLE, PLAN_REVIEW | workflow_mode = "simple"; skip/abort planning → EXECUTING; skip review |
| `start working` | PLAN_REVIEW | approve plan; proceed to EXECUTING with full review rounds |

`start working` in PLAN_REVIEW reuses the existing phrase so the user does not need to
learn a new command — saying "start working" again after reviewing the plan confirms it.

---

## `run_agent.sh` Changes

Add `plan` mode alongside existing `execute`, `confirm`, `review`:

```bash
MODE=plan
# Claude system prompt focuses on planning, not coding
# Reads in_message.txt
# Writes .klodTalk/plan_messages/plan.txt
```

For `execute` and `review` modes: if `plan.txt` exists, prepend it to the context Claude receives:
```
## The Plan
<plan.txt contents>

## Your Task
<in_message.txt contents>
```

---

## Client UI Changes

### Review Screen Buttons (Android & Web)

**Current:**
```
[Hear 🔊]  [Add 🎤]  [Execute ▶️]  [Understood? ❓]  [Cancel ❌]
```

**New:**
```
[Hear 🔊]  [Add 🎤]  [Cancel ❌]

Workflow:
[Full Plan 📋]   [Quick ⚡]   [Simple ▶️]   [Understood? ❓]
```

- **Full Plan 📋** — sends `start working` (triggers plan → code → 3 reviews)
- **Quick ⚡** — sends `start quick` (skips plan, 1 review)
- **Simple ▶️** — sends `start simple` (skips plan, no review)
- **Understood? ❓** — unchanged, sends `read back`

If the project config has `planning: false`, "Full Plan" and "Quick" behave identically to their review-round behaviour but skip the planning step (the label could change to "Full 📋" and "Quick ⚡" with the same semantics).

### Inbox (Android & Web)

- `"plan"` message type displayed with a distinct label, e.g. **[Plan]** badge
- Otherwise identical to regular response messages

---

## File-System Layout (per agent workspace)

```
.klodTalk/
├── in_messages/
│   └── in_message.txt          (existing - user request accumulates here)
├── plan_messages/
│   └── plan.txt                (NEW - planner output)
├── out_messages/
│   └── out_message.txt         (existing - coder output)
├── pr_messages/
│   └── pr_message.txt          (existing - reviewer output)
└── history/
    └── session_2026-03-13T06:22:29Z.md   (NEW - full session log)
```

---

## Files to Modify

| File | Change |
|------|--------|
| `src/computer/server.py` | Add PLANNING phase, new trigger phrases, workflow_mode tracking, history logging, `"plan"` message type |
| `src/computer/run_agent.sh` | Add `plan` mode; inject plan.txt into execute/review context; history append |
| `config/projects.json` | Add `planning`, `max_review_rounds` fields to each agent |
| `src/app/android/.../MainViewModel.kt` | Handle `"plan"` message type; new trigger phrases |
| `src/app/android/.../MainScreen.kt` | Redesign review screen buttons (Full Plan / Quick / Simple) |
| `src/web/index.html` | Same button redesign + `"plan"` message handling |

New files created at runtime (not in source):
- `.klodTalk/plan_messages/plan.txt` (per agent workspace)
- `.klodTalk/history/session_*.md` (per agent workspace)

---

## Open Questions & Decisions

1. **Re-planning loop**: **Resolved** — In PLAN_REVIEW, `start working` approves the current
   plan and proceeds to EXECUTING; it does **not** re-run the planner. If the user wishes to
   incorporate voice corrections before coding, they add them (via the "Add" button in the
   review screen) and then say `start working`. The coder agent receives both the updated
   `in_message.txt` and the original `plan.txt`. To discard the plan entirely and re-plan from
   scratch, the user must cancel and restart the session.

2. **Plan approval step**: **Resolved** — execution waits for an explicit trigger phrase after
   planning. After sending `"plan"` to the client the server enters PLAN_REVIEW and waits
   for `start working` (proceed with full review rounds), `start quick` (1 review), or
   `start simple` (no review). State machine: IDLE → PLANNING → **PLAN_REVIEW** → EXECUTING
   → REVIEWING → DONE. See the Server State Machine Changes section for full details.

3. **Planner asking questions**: Planner should NOT block for interactive Q&A. Instead it states assumptions explicitly in the plan. User can voice-correct before saying "start coding".

4. **History file size**: Cap per-session history? Log rotation? Low priority for now.

5. **UI label when agent has `planning: false`**: The "Full Plan" button still runs "start working" — perhaps rename to just "Full" when planning is disabled by the project config.

---

## Implementation Order (suggested)

1. **server.py** — state machine, new trigger phrases, plan phase watcher, history logging
2. **run_agent.sh** — plan mode, inject plan into execute/review
3. **projects.json** — add fields
4. **Web client** — easier to iterate on than Android
5. **Android client** — redesign review screen buttons

---

## Summary

The planner agent feature introduces a lightweight orchestration layer above the existing execute→review loop. The key design choices are:

- **Voice-friendly**: No blocking Q&A. Planner states assumptions; user corrects via voice if needed.
- **Skip-able**: Three trigger phrases let users choose Full / Quick / Simple on a per-request basis.
- **Backward-compatible**: Agents without `planning: true` behave exactly as today.
- **History**: Full session logs live in the workspace for traceability.
- **Minimal new concepts**: Reuses file-based I/O, Docker exec, and the existing review loop. The planner is just another `run_agent.sh` mode.
