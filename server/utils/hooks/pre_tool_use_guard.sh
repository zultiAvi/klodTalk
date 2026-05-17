#!/usr/bin/env bash
# PreToolUse destructive-command blocker hook
# Reads JSON from stdin; if tool_name == "Bash", checks tool_input.command against
# a narrow deny-list of destructive patterns. Exits non-zero with stderr reason on
# match (must be paired with "continueOnBlock": true in .claude/settings.json),
# otherwise exits 0.
#
# Register in .claude/settings.json (matcher MUST be present):
#   "hooks": {
#     "PreToolUse": [{
#       "matcher": "Bash",
#       "continueOnBlock": true,
#       "hooks": [{ "type": "command",
#                   "command": "bash /workspace/server/utils/hooks/pre_tool_use_guard.sh" }]
#     }]
#   }
#
# Source: disler/claude-code-hooks-mastery (https://github.com/disler/claude-code-hooks-mastery, ~3,700 stars)

INPUT="$(cat 2>/dev/null)" || INPUT=""

# Empty payload -> allow (nothing to inspect).
if [ -z "${INPUT}" ]; then
    exit 0
fi

# Extract tool_name + command, with a raw fallback if jq is unavailable.
if command -v jq &>/dev/null; then
    TOOL_NAME="$(echo "${INPUT}" | jq -r '.tool_name // ""' 2>/dev/null)" || TOOL_NAME=""
    CMD="$(echo "${INPUT}" | jq -r '.tool_input.command // ""' 2>/dev/null)" || CMD=""
else
    # Raw fallback: best-effort regex; if either field is missing, allow.
    TOOL_NAME="$(echo "${INPUT}" | grep -oE '"tool_name"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed -E 's/.*"tool_name"[[:space:]]*:[[:space:]]*"([^"]*)".*/\1/')"
    CMD="$(echo "${INPUT}" | grep -oE '"command"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed -E 's/.*"command"[[:space:]]*:[[:space:]]*"([^"]*)".*/\1/')"
fi

# Only guard Bash tool calls.
if [ "${TOOL_NAME}" != "Bash" ] || [ -z "${CMD}" ]; then
    exit 0
fi

# Deny-list: narrow, well-known destructive patterns. Keep tight to avoid false positives.
DENY_PATTERNS=(
    'rm[[:space:]]+-[a-zA-Z]*r[a-zA-Z]*f'
    'git[[:space:]]+reset[[:space:]]+--hard'
    'git[[:space:]]+push[[:space:]]+(.*[[:space:]]+)?--force'
    'git[[:space:]]+push[[:space:]]+(.*[[:space:]]+)?-f($|[[:space:]])'
    'chmod[[:space:]]+777'
    'dd[[:space:]]+.*of=/dev/'
    'mkfs\b'
    '\bshutdown\b'
    '\breboot\b'
)

for pat in "${DENY_PATTERNS[@]}"; do
    if echo "${CMD}" | grep -Eq "${pat}"; then
        echo "Refused: destructive command pattern '${pat}' matched -- see CLAUDE/skills/pre-tool-use-guard.md" >&2
        exit 2
    fi
done

exit 0
