---
skill_name: subagent-lifecycle-hooks
triggers:
  - Tracking when sub-agents spawn or finish in a team pipeline
  - Diagnosing premature container teardown while background tasks are pending
  - Correlating sub-agent activity with parent session IDs in logs
summary: SubagentStart / SubagentStop hooks log every Task-tool sub-agent spawn and exit (with background_tasks + session_crons) to the shared JSONL.
---

# Skill: SubagentStart / SubagentStop Lifecycle Hooks

## Quick Reference
- Hook script: `server/utils/hooks/subagent_lifecycle_logger.sh`
- Registration: `.claude/settings.json` under `hooks.SubagentStart` and `hooks.SubagentStop`, each with `"matcher": ""`
- Event source: anthropics/claude-code v2.1.145-v2.1.147
- Output: appended to `/workspace/.klodTalk/team/current/hook_events.jsonl` alongside PostToolUse entries
- Exit discipline: ALWAYS `exit 0` -- observational hook, never blocks the pipeline

## When to Use
- You need to know exactly *when* a sub-agent was spawned by the Task tool, and which role it represents.
- You are debugging why a container shut down while background work was still in flight (`background_tasks > 0` at SubagentStop time is the smoking gun).
- You want to reconstruct a full cross-agent timeline from a single JSONL file.

## Event Fields

| Field | When set | Meaning |
|-------|----------|---------|
| `timestamp` | always | Hook fire time, ISO-8601 UTC with millisecond precision |
| `event_type` | always | `SubagentStart` or `SubagentStop` |
| `agent_id` | always | The subagent's own id (matches the `x-claude-code-agent-id` API header -- see `claude-agents-cli.md`) |
| `parent_agent_id` | always | The spawning agent's id (matches `x-claude-code-parent-agent-id`) |
| `subagent_type` | SubagentStart | Role tag (e.g. `coder`, `planner`, `reviewer`) when the Task tool sets it |
| `description` | SubagentStart | Free-form task description from the Task tool call |
| `background_tasks` | SubagentStop | Count of pending background tasks at stop time -- non-zero means work is still in flight |
| `session_crons` | SubagentStop | List of scheduled cron entries still active when the sub-agent stopped |

## Registration

The hooks are registered with a `"matcher": ""` (matches all sub-agent events). The settings.json command wrapper passes the event type as the first positional argument so a single script handles both events:

```json
"SubagentStart": [
  {
    "matcher": "",
    "hooks": [
      { "type": "command", "command": "bash /workspace/server/utils/hooks/subagent_lifecycle_logger.sh SubagentStart" }
    ]
  }
]
```

`hooks.<EventGroup>` entries always require the `matcher` field -- see `hook-event-logging.md`.

## Correlating With Other Logs

- Join `agent_id` to the `x-claude-code-agent-id` HTTP header from API access logs -- see `claude-agents-cli.md`.
- Join `parent_agent_id` to the parent's `CLAUDE_CODE_SESSION_ID` Bash-tool env var -- see `session-id-in-bash-tools` if you need to bridge a Bash subprocess back to the spawning agent.
- All PostToolUse entries in the same JSONL file share the same `timestamp` clock, so you can interleave tool activity with sub-agent lifecycle in a single sorted view.

## Drain Check at Container Stop

Before tearing down an agent container at the end of a pipeline, scan the most recent `SubagentStop` entries and check `background_tasks`. Non-zero values mean the container was about to be reaped with work still pending -- raise it as a WARNING in `out_message.txt` so the operator can decide whether to extend the run.

```bash
jq -c 'select(.event_type=="SubagentStop" and (.background_tasks // 0) > 0)' \
  /workspace/.klodTalk/team/current/hook_events.jsonl
```

## Related
- `hook-event-logging.md` -- exit-0 discipline, JSONL format conventions, matcher requirement.
- `multi-agent-hook-observability.md` -- the shared JSONL pattern these events plug into.
- `claude-agents-cli.md` -- the `x-claude-code-agent-id` correlation headers.

## Source
- anthropics/claude-code v2.1.145-v2.1.147 release notes -- https://github.com/anthropics/claude-code/releases (Official Anthropic repo)
