# Team: Interactive Debug

A conversational debugging team. A single long-running agent investigates the reported issue and pauses at logical checkpoints, sharing what it has learned and asking the user how to proceed. The user replies via the existing BTW button — replies of `continue` or `exit` are reserved commands; anything else is treated as a free-form follow-up.

## enabled

## Members

| Name | Role | Model | Optional |
|------|------|-------|----------|
| interactive_debugger | interactive_debugger | opus | |

## Pipeline

1. **interactive_debugger** — Long-running. Reads the request and source, then loops:
   1. Investigate until the next logical checkpoint.
   2. Atomically write `## Team: interactive-debug (claude)` + `## Debug Pause — Checkpoint <N>` (summary / evidence / question / suggested actions) to `/workspace/.klodTalk/out_messages/debugger_message.txt`.
   3. Poll `/workspace/.klodTalk/in_messages/debug_reply.txt` every ~500 ms (hard cap 1800 s).
   4. Consume the reply (delete the file): `exit` -> finalize and stop; `continue` -> proceed to next checkpoint; anything else -> answer as a free-form follow-up and pause again.
   5. On `exit` or timeout: write `/workspace/.klodTalk/out_messages/out_message.txt` (starting with `## Team: interactive-debug (claude)`) and `/workspace/.klodTalk/team/current/coder_output.txt` (one-line transcript pointer), then end.

## Special Rules

**These rules apply to the interactive_debugger member and to the orchestrator itself. The orchestrator MUST include these Special Rules verbatim in the sub-agent prompt.**

- No code edits unless the user explicitly says `fix it`, `apply`, or `make the change` (case-insensitive substring match) in a reply.
- Pause at meaningful logical checkpoints — after analysis or hypothesis formation — not after every tool call.
- Use ONLY these two channels for the debug conversation:
  - Out: `/workspace/.klodTalk/out_messages/debugger_message.txt` (atomic: `.tmp` + rename).
  - In: `/workspace/.klodTalk/in_messages/debug_reply.txt` (consume by deleting after read).
- Reserved replies (trimmed, case-insensitive): `continue` and `exit`. Anything else is a free-form follow-up.
- Cap each `### Summary` and `### Evidence` block at ~4 KB.
- Hard timeout: 1800 s (30 min) waiting for any single reply. On timeout, write a final `out_message.txt` and exit cleanly.
