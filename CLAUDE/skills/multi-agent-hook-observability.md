---
skill_name: multi-agent-hook-observability
triggers:
  - Debugging a multi-agent team run
  - Summarizing per-role tool activity after a pipeline finishes
  - Building cross-agent timelines from PostToolUse events
summary: "Shared JSONL at .klodTalk/team/current/hook_events.jsonl gives a cross-agent timeline; orchestrator should append a per-role tool-count summary to out_message.txt."
---

# Skill: Multi-Agent Hook Observability

## Quick Reference
- Shared log path: `/workspace/.klodTalk/team/current/hook_events.jsonl`
- Writer: `server/utils/hooks/post_tool_use_logger.sh` (already registered in `.claude/settings.json`)
- Fields per line: `timestamp`, `role`, `tool_name`, `duration_ms`, `file_path`, `exit_code`, `effort_level`
- Reader: orchestrator Step 4 (Reporting), summarized into the final `out_message.txt`

## When to Use
- A team pipeline just finished and you want a one-glance view of which role touched what.
- You are debugging why a sub-agent stalled or produced unexpected writes.
- You want to add a future "live agent activity" feed in the web client without changing the client.

## Instructions

### Reading the log
The JSONL accumulates events from every container in the team run (each container appends to the same path because workspaces are mounted in). Each line is one tool call. Lines are independent — partial files are safe to parse.

### Per-role tool-count summary (one-liner with jq)
```bash
jq -r '"\(.role)\t\(.tool_name)"' \
  /workspace/.klodTalk/team/current/hook_events.jsonl \
  | sort | uniq -c | sort -rn
```

### Orchestrator integration
At the end of Step 4 (Reporting), the orchestrator appends a compact tool-count table to the final `out_message.txt`. See `teams/orchestrator.md` Step 4 "Final Summary" section. Skip silently if the JSONL is absent (e.g., for SIMPLE tasks that bypassed the pipeline).

### Notes
- The hook script already exits 0 on failure (see `hook-event-logging.md`) — observability is best-effort and never blocks the pipeline.
- For >5 MB logs, sample the tail rather than parsing the whole file in the summary step.

### Sub-agent Lifecycle Events
The same JSONL also receives `SubagentStart` and `SubagentStop` events (event_type field) emitted by `server/utils/hooks/subagent_lifecycle_logger.sh` and registered in `.claude/settings.json` since the v2.1.145 lifecycle hook rollout. These let the orchestrator's Step 4 reporting distinguish per-role spawn timestamps and -- via the `background_tasks` field on Stop -- detect premature container teardown while async work is still pending. See `subagent-lifecycle-hooks.md` for the field reference and the drain-check `jq` snippet.

## Cross-References
- `otel-assistant-response-event.md` — the OTEL `claude_code.assistant_response` event (CLI 2.1.193) captures the model's **response text**, the channel this JSONL lifecycle pipeline does not cover.

## Source
- disler/claude-code-hooks-multi-agent-observability — https://github.com/disler/claude-code-hooks-multi-agent-observability
- disler/claude-code-hooks-mastery — https://github.com/disler/claude-code-hooks-mastery (~3,000 stars)
