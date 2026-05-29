---
skill_name: post-tool-output-sanitize
triggers:
  - Redacting secrets/tokens from Bash tool stdout before Claude reads it
  - Capturing per-tool `duration_ms` telemetry from PostToolUse hooks
  - Configuring KLODTALK_REDACT_PATTERNS for a project or operator
summary: PostToolUse hook sanitize_bash_output.sh replaces matched regex output with [REDACTED] via hookSpecificOutput.updatedToolOutput and logs duration_ms; register in .claude/settings.json (NOT role frontmatter).
---

# Skill: PostToolUse Output Sanitization via `updatedToolOutput`

## Quick Reference
- Script: `server/utils/hooks/sanitize_bash_output.sh`
- Env var: `KLODTALK_REDACT_PATTERNS` (newline-separated Python regexes)
- Output field: `hookSpecificOutput.hookEventName = "PostToolUse"` + `updatedToolOutput`
- Telemetry side channel: `/workspace/.klodTalk/team/current/hook_events.jsonl`
- CLI requirement: Claude Code v2.1.141+ (the `updatedToolOutput` field was previously MCP-only)
- Hook must always `exit 0` -- non-zero blocks Claude's tool pipeline (instinct #1).

## When to Use
- A KlodTalk Coder/Reviewer container runs Bash whose stdout may include
  secrets (cloud keys, OAuth tokens, internal hostnames) -- you want them
  redacted *before* Claude ingests them into its context window.
- You want per-Bash-call `duration_ms` telemetry to drive a "slow command"
  audit without writing a separate hook.
- You need a sanitizer that is safe to ship on every container (no-op fast
  path when no patterns are configured).

## What the Hook Does

1. Reads the PostToolUse JSON payload from stdin (the same payload Claude
   Code passes to any PostToolUse hook).
2. Always appends a one-line JSONL telemetry record to
   `/workspace/.klodTalk/team/current/hook_events.jsonl` with:
   `timestamp`, `hook: "sanitize_bash_output"`, `tool_name`, `duration_ms`,
   `exit_code`.
3. If `KLODTALK_REDACT_PATTERNS` is set, loads the patterns (one regex per
   line) and applies each to the tool's textual output. Every match is
   replaced with the literal string `[REDACTED]`.
4. If any pattern matched, prints the replacement payload:
   ```json
   {"hookSpecificOutput":{"hookEventName":"PostToolUse","updatedToolOutput":"<cleaned>"}}
   ```
   Otherwise prints `{}` (no-op) so Claude Code performs no replacement.
5. Always exits 0.

## Registration (operator step)

Per instinct #7, role-file YAML frontmatter currently forwards only
`mcpServers` and `disallowedTools`. Hooks **cannot** be registered via role
frontmatter -- the entry would be silently ignored. Register the hook in
`.claude/settings.json` inside the agent container (or in the
workspace-level `/workspace/.claude/settings.json` if you want every team to
inherit it):

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "bash /workspace/server/utils/hooks/sanitize_bash_output.sh"
          }
        ]
      }
    ]
  }
}
```

Notes:
- `matcher: "Bash"` scopes the hook to the Bash tool only. Use `""` to
  match every tool.
- The hook group object **requires** a `matcher` key (instinct #3).
- For programmatic registration patterns, see `server/run_agent.py`
  `_setup_agent_hooks()` -- that function already writes a `PostToolUse`
  entry; the operator can either extend that block or layer a second
  matcher group via the workspace settings file.

## Configuring redaction patterns

Patterns live in the `KLODTALK_REDACT_PATTERNS` env var on the agent
container, newline-separated. Empty / unset disables redaction (telemetry
still runs).

Example (docker-compose):

```yaml
environment:
  - |
    KLODTALK_REDACT_PATTERNS=AKIA[0-9A-Z]{16}
    ghp_[A-Za-z0-9]{36}
    sk-ant-[A-Za-z0-9_-]{32,}
    Bearer\s+[A-Za-z0-9._~+/=-]{20,}
```

Or in `docker run`:

```bash
docker run -e KLODTALK_REDACT_PATTERNS=$'AKIA[0-9A-Z]{16}\nghp_[A-Za-z0-9]{36}' ...
```

### Pattern flavor
The patterns are Python `re` regexes (the hook uses `python3 -c re.sub`).
Use Python regex syntax, not PCRE. Invalid patterns are silently skipped so
that one bad entry cannot break the pipeline.

### Extending patterns per project
Operators can layer project-specific patterns by appending to the env var
in the project's container env block (e.g. an internal SaaS API key prefix
or an internal hostname). Keep one pattern per line for readability.

## Telemetry side channel

Each invocation appends a JSONL line to
`/workspace/.klodTalk/team/current/hook_events.jsonl`, for example:

```json
{"timestamp":"2026-05-29T01:11:42.481Z","hook":"sanitize_bash_output","tool_name":"Bash","duration_ms":2147,"exit_code":0}
```

The `duration_ms` field comes directly from the PostToolUse JSON payload
(Claude Code v2.1.141+) and can be aggregated by downstream tools (e.g. the
multi-agent hook observability skill) to surface slow Bash calls without an
extra hook.

## Failure modes & guardrails

- **Always exit 0.** Per instinct #1, a non-zero exit from a PostToolUse
  hook blocks Claude's tool pipeline. This script catches every internal
  error and falls through to `{}` rather than failing.
- **Missing `jq` / `python3`.** The hook checks for both before attempting
  redaction. If either is absent, it emits `{}` (no-op) and still logs the
  raw telemetry line when `jq` is present.
- **Invalid regex.** A `re.error` is caught per-pattern and the bad
  pattern is skipped. Other patterns still apply.
- **Empty tool output.** Hook falls through to `{}` -- nothing to redact.

## Verifying

Inside an agent container after registering the hook:

```bash
echo '{"tool_name":"Bash","duration_ms":42,"tool_response":{"output":"key=AKIAABCDEFGHIJKLMNOP done"}}' \
  | KLODTALK_REDACT_PATTERNS='AKIA[0-9A-Z]{16}' \
    bash /workspace/server/utils/hooks/sanitize_bash_output.sh
```

Expected stdout:
```json
{"hookSpecificOutput": {"hookEventName": "PostToolUse", "updatedToolOutput": "key=[REDACTED] done"}}
```

And `hook_events.jsonl` should gain a new line with `duration_ms: 42`.

## Related
- `pre-tool-use-guard.md` -- input-side guard (blocks dangerous commands).
- `large-output-spill.md` -- spills oversized output to a file (size, not secrets).
- `multi-agent-hook-observability.md` -- consumer of `hook_events.jsonl`.
- `continue-on-block-hooks.md` -- when a hook *should* exit non-zero.
- `hook-event-logging.md` -- the broader JSONL telemetry contract.

## Source
- docs.anthropic.com -- "PostToolUse Hooks Can Now Replace Tool Output for
  All Tools" -- https://docs.anthropic.com/en/docs/claude-code/sdk
  (Claude Code v2.1.141+, 2026-05).
