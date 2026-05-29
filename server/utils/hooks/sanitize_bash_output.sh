#!/usr/bin/env bash
# PostToolUse hook -- output sanitization via `updatedToolOutput`.
#
# Reads the PostToolUse JSON payload from stdin. If any line in the tool output
# matches a regex from $KLODTALK_REDACT_PATTERNS (newline-separated), the
# matched substrings are replaced with `[REDACTED]` and the cleaned output is
# emitted to stdout as:
#   {"hookSpecificOutput":{"hookEventName":"PostToolUse","updatedToolOutput":"<cleaned>"}}
#
# When no pattern matches (or no patterns are configured), the hook emits
# `{}` so Claude Code performs no replacement (no-op fast path).
#
# Independent of redaction, the hook captures `duration_ms`, `tool_name`, and
# `exit_code` and appends a one-line JSONL telemetry record to
#   /workspace/.klodTalk/team/current/hook_events.jsonl
#
# CRITICAL: This script MUST always exit 0. A non-zero exit blocks Claude's
# tool pipeline. See instinct #1 (PostToolUse/PostToolUseFailure must exit 0).
#
# Register in .claude/settings.json (NOT in role frontmatter -- frontmatter
# only forwards `mcpServers` and `disallowedTools`; see instinct #7):
#   {
#     "hooks": {
#       "PostToolUse": [
#         {
#           "matcher": "Bash",
#           "hooks": [
#             { "type": "command",
#               "command": "bash /workspace/server/utils/hooks/sanitize_bash_output.sh" }
#           ]
#         }
#       ]
#     }
#   }
#
# Operator extension: export newline-separated regex patterns via
#   KLODTALK_REDACT_PATTERNS=$'AKIA[0-9A-Z]{16}\nghp_[A-Za-z0-9]{36}'
# Empty / unset disables redaction (telemetry still runs).
#
# Source: docs.anthropic.com -- "PostToolUse Hooks Can Now Replace Tool Output
# for All Tools" -- https://docs.anthropic.com/en/docs/claude-code/sdk
# (Claude Code v2.1.141+).

# Read the full JSON payload from stdin (best effort; never fail the pipeline).
INPUT="$(cat 2>/dev/null)" || INPUT=""

LOG_DIR="/workspace/.klodTalk/team/current"
LOG_FILE="${LOG_DIR}/hook_events.jsonl"
mkdir -p "${LOG_DIR}" 2>/dev/null || true

# --- Telemetry side channel (always-on) --------------------------------------
{
    if command -v jq >/dev/null 2>&1 && [ -n "${INPUT}" ]; then
        TIMESTAMP="$(date -u +"%Y-%m-%dT%H:%M:%S.%3NZ" 2>/dev/null)" \
            || TIMESTAMP="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
        LOG_ENTRY="$(echo "${INPUT}" | jq -c \
            --arg ts "${TIMESTAMP}" \
            '{timestamp: $ts,
              hook: "sanitize_bash_output",
              tool_name: (.tool_name // "unknown"),
              duration_ms: (.duration_ms // null),
              exit_code: (.exit_code // null)}' 2>/dev/null)" || LOG_ENTRY=""
        if [ -n "${LOG_ENTRY}" ]; then
            echo "${LOG_ENTRY}" >> "${LOG_FILE}" 2>/dev/null || true
        fi
    fi
} 2>/dev/null

# --- Redaction (opt-in via KLODTALK_REDACT_PATTERNS) -------------------------
# Only attempt redaction if patterns and jq + python3 are present and we have
# non-empty input. Anything that fails falls through to the no-op `{}` output.
PATTERNS="${KLODTALK_REDACT_PATTERNS:-}"

if [ -n "${INPUT}" ] && [ -n "${PATTERNS}" ] \
   && command -v jq >/dev/null 2>&1 \
   && command -v python3 >/dev/null 2>&1; then

    # Extract `tool_response.output` (best effort), falling back to
    # `tool_response.stdout`, then the whole `tool_response`, then ""
    ORIGINAL="$(echo "${INPUT}" | jq -r '
        .tool_response.output
        // .tool_response.stdout
        // (.tool_response | tostring)
        // ""
    ' 2>/dev/null)" || ORIGINAL=""

    if [ -n "${ORIGINAL}" ]; then
        CLEANED="$(
            KLODTALK_REDACT_PATTERNS="${PATTERNS}" \
            ORIGINAL_TEXT="${ORIGINAL}" \
            python3 - <<'PY' 2>/dev/null
import json
import os
import re
import sys

original = os.environ.get("ORIGINAL_TEXT", "")
raw_patterns = os.environ.get("KLODTALK_REDACT_PATTERNS", "")

patterns = [p for p in raw_patterns.splitlines() if p.strip()]
cleaned = original
changed = False
for pat in patterns:
    try:
        new = re.sub(pat, "[REDACTED]", cleaned)
    except re.error:
        # Invalid regex -- skip, do not break the pipeline
        continue
    if new != cleaned:
        changed = True
        cleaned = new

if changed:
    payload = {
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "updatedToolOutput": cleaned,
        }
    }
    sys.stdout.write(json.dumps(payload))
else:
    sys.stdout.write("{}")
PY
        )"
        if [ -n "${CLEANED}" ]; then
            printf '%s' "${CLEANED}"
            exit 0
        fi
    fi
fi

# Default: no-op replacement.
printf '%s' '{}'
exit 0
