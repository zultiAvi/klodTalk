---
skill_name: precompact-context-guard
triggers:
  - Preserving task state across a context-window compaction pass
  - Diagnosing why an agent "forgot" its task after a long run
  - Pairing snapshot artifacts with compaction-api-opt-in
summary: PreCompact snapshots in_message.txt + progress.json + last 5 hook_events.jsonl lines before compaction; PostCompact appends a JSONL confirmation. Always exit 0.
---

# Skill: PreCompact / PostCompact Context-Guard Hooks

## Quick Reference
- Events: `PreCompact` (fires before context compaction), `PostCompact` (fires after)
- Snapshot file: `/workspace/.klodTalk/team/current/compaction_snapshot_<timestamp>.json`
- Telemetry sink: `/workspace/.klodTalk/team/current/hook_events.jsonl`
- Registration: `/workspace/.claude/settings.json` (NOT `~/.claude/settings.json`) — see `hook-settings-location.md`
- Exit discipline: ALWAYS `exit 0` — observational, never blocks
- Companion: enable only when `compaction-api-opt-in.md` is in effect

## When to Use
- A long-running Coder or Planner is using the Compaction API (`KLODTALK_CONTEXT_COMPACTION=1`) and you want to verify what was preserved versus summarized.
- Diagnosing post-mortem why an agent "lost its thread" — the snapshot lets you compare pre-compaction context with post-compaction behavior.
- Completing the lifecycle hook coverage gap: KlodTalk already logs `PreToolUse`, `PostToolUse`, `SubagentStart/Stop`, and `Stop`; `PreCompact`/`PostCompact` are the missing pair.

## What the Hooks Do

### PreCompact
Fires immediately before the Claude Code CLI performs a context compaction
pass. The stdin payload includes the current session summary. The hook
snapshots a single JSON file to
`/workspace/.klodTalk/team/current/compaction_snapshot_<timestamp>.json`
containing:

- `original_task`: contents of `/workspace/.klodTalk/in_messages/in_message.txt` (the user's original request)
- `pipeline_stage`: contents of `/workspace/.klodTalk/team/current/progress.json` if present (current Planner/Coder/Reviewer stage)
- `recent_hook_events`: the last 5 lines of `hook_events.jsonl`
- `timestamp`: ISO-8601 UTC at snapshot time

### PostCompact
Fires after compaction completes. Appends one JSONL line to
`hook_events.jsonl`:

```json
{"timestamp":"2026-05-30T01:42:11.003Z","event_type":"PostCompact","snapshot_file":"/workspace/.klodTalk/team/current/compaction_snapshot_2026-05-30T01-42-09Z.json"}
```

## Registration

Per `hook-settings-location.md`, register in `/workspace/.claude/settings.json`
(workspace-level). The user-level `~/.claude/settings.json` `hooks` key is
overwritten by `_setup_agent_hooks()` on every container start.

Both hook groups require the `matcher` field (use `""` to match all
compaction events):

```json
{
  "hooks": {
    "PreCompact": [
      {
        "matcher": "",
        "hooks": [
          { "type": "command", "command": "bash /workspace/server/utils/hooks/precompact_snapshot.sh" }
        ]
      }
    ],
    "PostCompact": [
      {
        "matcher": "",
        "hooks": [
          { "type": "command", "command": "bash /workspace/server/utils/hooks/postcompact_confirm.sh" }
        ]
      }
    ]
  }
}
```

## Exit Discipline

Both hooks ALWAYS `exit 0`. They are purely observational. A non-zero exit
from PreCompact would block compaction itself, defeating the
`compaction-api-opt-in.md` opt-in. Catch all internal errors and fall
through to `exit 0`.

## Verifying

After triggering a compaction pass in a long-running session:

```bash
ls -1 /workspace/.klodTalk/team/current/compaction_snapshot_*.json
jq -c 'select(.event_type=="PostCompact")' \
  /workspace/.klodTalk/team/current/hook_events.jsonl
```

Each compaction event produces exactly one snapshot file and one PostCompact
JSONL record. Mismatched counts indicate a hook script failure (which
should still have exited 0 — check stderr in the container logs).

## Related
- `compaction-api-opt-in.md` — the opt-in this skill protects.
- `hook-settings-location.md` — workspace-level settings file requirement.
- `hook-event-logging.md` — JSONL telemetry format and exit-0 discipline.
- `multi-agent-hook-observability.md` — downstream consumer of `hook_events.jsonl`.
- `subagent-lifecycle-hooks.md` — sibling lifecycle hooks.

## Source
- vinicius91carvalho/.claude — https://github.com/vinicius91carvalho/.claude
  (community hook collection covering PreCompact/PostCompact among 23
  enforcement hooks across 8 lifecycle events).
