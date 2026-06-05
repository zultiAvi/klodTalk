---
skill_name: stop-hook-additional-context
triggers:
  - Nudging a finishing sub-agent (e.g. remind the coder to run its DONE-WHEN self-check)
  - Adding a Stop / SubagentStop hook that feeds text back to the model
  - Avoiding stop loops when a Stop hook injects context
summary: "Stop/SubagentStop hooks (Claude Code >= 2.1.163) can emit {\"hookSpecificOutput\":{\"additionalContext\":\"...\"}} on stdout to feed text back to the model; must be role-gated AND idempotent to avoid stop loops. KlodTalk uses it to remind a coder to run its DONE-WHEN self-check."
---

# Skill: Stop Hook additionalContext

## Quick Reference
- Hook script: `server/utils/hooks/subagent_stop_self_check.sh` (SubagentStop)
- Output shape (stdout): `{"hookSpecificOutput":{"additionalContext":"<text>"}}` then `exit 0`
- Requires Claude Code **>= 2.1.163**; older CLIs ignore unknown `hookSpecificOutput` keys (safe no-op, no version probe needed).
- Loop avoidance: **role-gated** (only `coder`) AND **idempotent** (per-`agent_id` marker under `${TMPDIR:-/tmp}/klodtalk_subagent_self_check/`) so it fires at most once per sub-agent.
- DISTINCT from `subagent_lifecycle_logger.sh` — that hook only logs JSONL and never emits additionalContext. Keep the two separate.

## When to Use
- You want the harness to inject a reminder into a sub-agent that is about to declare done (e.g. run the DONE-WHEN self-check, or replay unresolved `BLOCKER:` lines) instead of relying on the prompt being followed.

## Why It Is Safe Against Stop Loops
`additionalContext` re-feeds the model, which could in principle make the agent
run again and re-trigger SubagentStop. Two guards make a loop impossible:
1. **Role gate** — emits nothing unless the role is `coder` (resolved from
   `subagent_type` / `agent_type` in the stdin payload, falling back to the
   `KLODTALK_ROLE` env var; see `hook-agent-type-filter.md`).
2. **Idempotency** — the first fire for a given `agent_id` writes a marker file;
   any later SubagentStop for that same `agent_id` emits nothing.

The script ALWAYS `exit 0` (a non-zero exit blocks the stop pipeline). The
reminder text is a static, ASCII-safe string controlled in the script — no
untrusted env input is interpolated.

## Registration Snippet
Add to `/workspace/.claude/settings.json` (workspace-level — see
`hook-settings-location.md`; user-level `hooks` is clobbered each container start):

```json
{
  "hooks": {
    "SubagentStop": [
      {
        "matcher": "",
        "hooks": [
          { "type": "command",
            "command": "bash /workspace/server/utils/hooks/subagent_stop_self_check.sh" }
        ]
      }
    ]
  }
}
```

The observational `subagent_lifecycle_logger.sh` is registered separately under
the same `SubagentStop` group (it logs JSONL); both can coexist.

## Cross-References
- `subagent-lifecycle-hooks.md` — the observational SubagentStart/SubagentStop logger (distinct concern).
- `hook-settings-location.md` — why hooks go in `/workspace/.claude/settings.json`.
- `hook-agent-type-filter.md` — reading `agent_type` / `subagent_type` per role.
- `required-minimum-version-pin.md` — pin the CLI floor so this feature never silently no-ops.

## Source
- Claude Code CHANGELOG v2.1.163 —
  https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md
