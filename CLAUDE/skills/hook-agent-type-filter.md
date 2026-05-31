---
skill_name: hook-agent-type-filter
triggers:
  - Extending a hook script to behave differently per role
  - Auditing which role triggered a specific tool call in hook_events.jsonl
  - Reading the claude-agent-sdk-python hook payload schema
summary: "Hook stdin payloads now carry agent_id and agent_type fields (claude-agent-sdk-python, May 2026); read with jq, log for observability, gate per-role branching behind safety review."
---

# Skill: Hook agent_type Filter

## Quick Reference
- Fields: `agent_id` (string), `agent_type` (string — typically the role name set by the Task tool)
- Extraction: `jq -r '.agent_type // "unknown"'` on the hook stdin payload
- SDK source: `claude-agent-sdk-python` `PreToolUseHookInput`, `PostToolUseHookInput`, `PostToolUseFailureHookInput` (May 2026)
- Current usage in KlodTalk: `post_tool_use_logger.sh` and `sanitize_bash_output.sh` log the fields. No behavioural branching yet — observability only.

## When to Use
- You want a single hook script to apply different policies depending on which role is invoking the tool (e.g. stricter sanitization for the coder, lighter logging for the planner) — without registering N per-role hook scripts in `settings.json`.
- You are debugging a multi-agent run and need to know which subagent emitted a specific JSONL row.

## Instructions

### Payload Fields
With the May 2026 update to `claude-agent-sdk-python`, the hook stdin JSON payload includes:

| Field        | Type   | Meaning |
|--------------|--------|---------|
| `agent_id`   | string | Unique identifier for the agent instance (stable for the lifetime of one Task subagent). |
| `agent_type` | string | Role tag set by the Task tool (e.g. `coder`, `planner`, `reviewer`). Maps to the role file name in `teams/roles/`. |

Both fields are present in `PreToolUseHookInput`, `PostToolUseHookInput`, and `PostToolUseFailureHookInput`. Earlier SDK versions omit the field; defensively use `// null` (jq) or `// "unknown"` to fall back without breaking.

### jq Extraction Snippet
```bash
# Read once; reuse for both telemetry and any policy gate.
AGENT_TYPE="$(echo "${INPUT}" | jq -r '.agent_type // "unknown"' 2>/dev/null)"
AGENT_ID="$(echo "${INPUT}" | jq -r '.agent_id // "unknown"' 2>/dev/null)"
```

When building a JSONL line, prefer letting `jq` do the field plumbing in one pass so quoting is handled correctly:
```bash
jq -c '{timestamp: $ts, tool_name: (.tool_name // "unknown"),
        agent_id: (.agent_id // null), agent_type: (.agent_type // null)}'
```

### Current KlodTalk Logging
The following hook scripts now emit `agent_id` and `agent_type` in their JSONL telemetry. Behaviour is **unchanged** — fields are added for downstream analysis only:
- `server/utils/hooks/post_tool_use_logger.sh`
- `server/utils/hooks/sanitize_bash_output.sh`

You can grep the resulting `/workspace/.klodTalk/team/current/hook_events.jsonl` by role:
```bash
jq -c 'select(.agent_type == "coder")' /workspace/.klodTalk/team/current/hook_events.jsonl
```

### Future Per-Role Branching (NOT yet enabled)
The same field can drive per-role policy gates. **This is deliberately left unimplemented** for now — gating sanitization or logging on `agent_type` is a security-sensitive change that should go through a separate review pass (e.g. a fresh-context evaluator — see `fresh-context-evaluator.md`). Sketch for future use:

```bash
AGENT_TYPE="$(echo "${INPUT}" | jq -r '.agent_type // "unknown"' 2>/dev/null)"
case "${AGENT_TYPE}" in
    planner|reviewer)
        # Read-only roles: skip the expensive redaction pass.
        printf '%s' '{}'
        exit 0
        ;;
    coder|coder_tdd|coder_unit_test)
        # Code-producing roles: full redaction.
        ;;
    *)
        # Unknown / older SDK: be conservative -- full redaction.
        ;;
esac
```

Do **not** add the branching above until:
1. A fresh-context evaluator has reviewed the policy table.
2. There is a test that verifies the JSONL telemetry shows the expected per-role pattern on a sample multi-agent run.
3. There is a fallback path for `agent_type == "unknown"` that matches today's behaviour exactly.

### Safety Note on Trusting agent_type
`agent_type` is set by the Task tool's caller and is **not a security boundary** — a compromised agent could in principle spoof its own type. Use it for observability and convenience, not for granting elevated capabilities. Hard restrictions belong in `disallowedTools` frontmatter (see `disallowed-tools-frontmatter.md`) and in `pre_tool_use_guard.sh` deny-lists (see `pre-tool-use-guard.md`).

## Related
- `hook-event-logging.md` — JSONL schema and exit-0 discipline.
- `post-tool-output-sanitize.md` — the sanitization hook that now logs the fields.
- `multi-agent-hook-observability.md` — wider context for per-subagent correlation.
- `disallowed-tools-frontmatter.md` — the actual security boundary for per-role restriction.
- `subagent-lifecycle-hooks.md` — SubagentStart/SubagentStop events that also carry `agent_type`.

## Source
anthropics/claude-agent-sdk-python — https://github.com/anthropics/claude-agent-sdk-python (official Anthropic, May 2026). Hook input payloads now include `agent_id` and `agent_type` in `PreToolUseHookInput`, `PostToolUseHookInput`, and `PostToolUseFailureHookInput`.
