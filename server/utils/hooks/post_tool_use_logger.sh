#!/usr/bin/env bash
# PostToolUse / PostToolUseFailure hook logger
# Reads JSON from stdin, extracts key fields, appends a JSONL line to hook_events.jsonl.
#
# CRITICAL: This script MUST always exit 0. A non-zero exit blocks Claude's tool pipeline.
#
# Register in .claude/settings.json under hooks.PostToolUse and hooks.PostToolUseFailure:
#   "hooks": {
#     "PostToolUse": [{ "type": "command", "command": "bash /workspace/server/utils/hooks/post_tool_use_logger.sh" }],
#     "PostToolUseFailure": [{ "type": "command", "command": "bash /workspace/server/utils/hooks/post_tool_use_logger.sh" }]
#   }
#
# Source: disler/claude-code-hooks-mastery (https://github.com/disler/claude-code-hooks-mastery, ~3,500 stars)

{
    # Read the full JSON payload from stdin
    INPUT="$(cat 2>/dev/null)" || INPUT=""

    # Determine output directory; default to the team current folder
    LOG_DIR="/workspace/.klodTalk/team/current"
    LOG_FILE="${LOG_DIR}/hook_events.jsonl"

    # Ensure the log directory exists
    mkdir -p "${LOG_DIR}" 2>/dev/null || true

    # Capture optional effort level from Claude Code env (available since v2.1.133+).
    # Empty when running on older CLI versions or when no explicit effort was set.
    EFFORT="${CLAUDE_EFFORT:-}"

    # Extract fields using jq if available, otherwise fall back to raw logging
    if command -v jq &>/dev/null && [ -n "${INPUT}" ]; then
        TIMESTAMP="$(date -u +"%Y-%m-%dT%H:%M:%S.%3NZ" 2>/dev/null)" || TIMESTAMP="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

        # Build a compact JSON line directly from the input payload
        # This avoids shell-variable round-tripping that loses null vs "null" distinction
        # `agent_id` and `agent_type` are present in hook payloads from
        # claude-agent-sdk-python (May 2026) -- they identify the role
        # currently issuing the tool call when the Task tool spawns sub-agents.
        # Older SDK versions omit the field; jq's `// null` falls back cleanly.
        # See CLAUDE/skills/hook-agent-type-filter.md.
        LOG_ENTRY="$(echo "${INPUT}" | jq -c \
            --arg ts "${TIMESTAMP}" \
            --arg effort "${EFFORT}" \
            '{timestamp: $ts, tool_name: (.tool_name // "unknown"), duration_ms: (.duration_ms // null), file_path: (.file_path // null), exit_code: (.exit_code // null), effort_level: ($effort | if . == "" then null else . end), agent_id: (.agent_id // null), agent_type: (.agent_type // null)}' 2>/dev/null)" || LOG_ENTRY=""

        if [ -n "${LOG_ENTRY}" ]; then
            echo "${LOG_ENTRY}" >> "${LOG_FILE}" 2>/dev/null || true
        fi
    elif [ -n "${INPUT}" ]; then
        # Fallback: log the raw input with a timestamp prefix
        TIMESTAMP="$(date -u +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null)" || TIMESTAMP="unknown"
        echo "{\"timestamp\":\"${TIMESTAMP}\",\"raw\":true,\"effort_level\":\"${EFFORT}\",\"data\":$(echo "${INPUT}" | head -c 4096 | jq -Rs . 2>/dev/null || echo '""')}" >> "${LOG_FILE}" 2>/dev/null || true
    fi
    # If INPUT is empty, silently do nothing
} 2>/dev/null

# ALWAYS exit 0 -- this is a hard project rule
exit 0
