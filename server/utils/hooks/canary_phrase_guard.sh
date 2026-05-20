#!/usr/bin/env bash
# PostToolUse canary-phrase guard hook
# Reads JSON from stdin; if tool_name is Write or Edit, scans the written content
# for known placeholder/stub canary phrases (raise NotImplementedError, # TODO:,
# pass  # placeholder, ...). Exits 2 with a stderr reason on match (must be paired
# with "continueOnBlock": true in .claude/settings.json), otherwise exits 0.
#
# Per-file block cap of 3 prevents tripping the Stop-hook 8-block termination
# (see CLAUDE/skills/stop-hook-block-cap.md). After 3 blocks on the same file
# the hook logs a pass-through event to hook_events.jsonl and exits 0.
#
# Register in .claude/settings.json (matcher MUST be present):
#   "hooks": {
#     "PostToolUse": [{
#       "matcher": "Write",
#       "continueOnBlock": true,
#       "hooks": [{ "type": "command",
#                   "command": "bash /workspace/server/utils/hooks/canary_phrase_guard.sh" }]
#     }, {
#       "matcher": "Edit",
#       "continueOnBlock": true,
#       "hooks": [{ "type": "command",
#                   "command": "bash /workspace/server/utils/hooks/canary_phrase_guard.sh" }]
#     }]
#   }
#
# Source: mann1x/claude-hooks (https://github.com/mann1x/claude-hooks, stop-phrase canary detection)

INPUT="$(cat 2>/dev/null)" || INPUT=""

# Empty payload -> allow (nothing to inspect).
if [ -z "${INPUT}" ]; then
    exit 0
fi

# Extract tool_name + candidate content + file_path. Raw fallback if jq is unavailable.
if command -v jq &>/dev/null; then
    TOOL_NAME="$(echo "${INPUT}" | jq -r '.tool_name // ""' 2>/dev/null)" || TOOL_NAME=""
    FILE_PATH="$(echo "${INPUT}" | jq -r '.tool_input.file_path // ""' 2>/dev/null)" || FILE_PATH=""
    if [ "${TOOL_NAME}" = "Write" ]; then
        CONTENT="$(echo "${INPUT}" | jq -r '.tool_input.content // ""' 2>/dev/null)" || CONTENT=""
    elif [ "${TOOL_NAME}" = "Edit" ]; then
        CONTENT="$(echo "${INPUT}" | jq -r '.tool_input.new_string // ""' 2>/dev/null)" || CONTENT=""
    else
        CONTENT=""
    fi
else
    # Raw fallback: best-effort regex; if either field is missing, allow.
    TOOL_NAME="$(echo "${INPUT}" | grep -oE '"tool_name"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed -E 's/.*"tool_name"[[:space:]]*:[[:space:]]*"([^"]*)".*/\1/')"
    FILE_PATH="$(echo "${INPUT}" | grep -oE '"file_path"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed -E 's/.*"file_path"[[:space:]]*:[[:space:]]*"([^"]*)".*/\1/')"
    if [ "${TOOL_NAME}" = "Write" ]; then
        CONTENT="$(echo "${INPUT}" | grep -oE '"content"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed -E 's/.*"content"[[:space:]]*:[[:space:]]*"([^"]*)".*/\1/')"
    elif [ "${TOOL_NAME}" = "Edit" ]; then
        CONTENT="$(echo "${INPUT}" | grep -oE '"new_string"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed -E 's/.*"new_string"[[:space:]]*:[[:space:]]*"([^"]*)".*/\1/')"
    else
        CONTENT=""
    fi
fi

# Only guard Write/Edit tool calls with non-empty content.
if [ "${TOOL_NAME}" != "Write" ] && [ "${TOOL_NAME}" != "Edit" ]; then
    exit 0
fi
if [ -z "${CONTENT}" ]; then
    exit 0
fi

# Canary deny-list: narrow, well-known placeholder patterns. Keep tight to avoid
# false positives on legitimate code that mentions these tokens in strings/docs.
CANARY_PATTERNS=(
    'raise[[:space:]]+NotImplementedError'
    '#[[:space:]]*TODO:'
    '#[[:space:]]*TODO[[:space:]]'
    '//[[:space:]]*TODO:'
    '/\*[[:space:]]*TODO[[:space:]]*\*/'
    'pass[[:space:]]+#[[:space:]]*placeholder'
    'pass[[:space:]]+#[[:space:]]*implement'
    'TODO:[[:space:]]*implement'
    '#[[:space:]]*FIXME:'
    '//[[:space:]]*FIXME:'
    '#[[:space:]]*XXX:'
)

MATCHED_PATTERN=""
for pat in "${CANARY_PATTERNS[@]}"; do
    if echo "${CONTENT}" | grep -Eq "${pat}"; then
        MATCHED_PATTERN="${pat}"
        break
    fi
done

# No canary -> allow.
if [ -z "${MATCHED_PATTERN}" ]; then
    exit 0
fi

# Per-file block counter: hash file_path so counter filenames are filesystem-safe.
SESSION_ID="${CLAUDE_CODE_SESSION_ID:-no_session}"
if command -v sha1sum &>/dev/null; then
    FILE_HASH="$(printf '%s' "${FILE_PATH}" | sha1sum 2>/dev/null | awk '{print $1}')"
else
    # Fallback: strip non-alphanumerics from the path (sufficient for filename use).
    FILE_HASH="$(printf '%s' "${FILE_PATH}" | tr -c 'a-zA-Z0-9' '_' | head -c 40)"
fi
COUNTER_FILE="/tmp/canary_block_count_${SESSION_ID}_${FILE_HASH}"

CURRENT_COUNT=0
if [ -f "${COUNTER_FILE}" ]; then
    CURRENT_COUNT="$(cat "${COUNTER_FILE}" 2>/dev/null || echo 0)"
    case "${CURRENT_COUNT}" in
        ''|*[!0-9]*) CURRENT_COUNT=0 ;;
    esac
fi
NEW_COUNT=$((CURRENT_COUNT + 1))

# Cap at 3 consecutive blocks per file to stay below the Stop-hook 8-block cap.
MAX_BLOCKS=3
if [ "${NEW_COUNT}" -gt "${MAX_BLOCKS}" ]; then
    # Log cap-reached pass-through event and allow the write.
    LOG_DIR="/workspace/.klodTalk/team/current"
    LOG_FILE="${LOG_DIR}/hook_events.jsonl"
    mkdir -p "${LOG_DIR}" 2>/dev/null || true
    TIMESTAMP="$(date -u +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null)" || TIMESTAMP="unknown"
    if command -v jq &>/dev/null; then
        echo "${INPUT}" | jq -c \
            --arg ts "${TIMESTAMP}" \
            --arg pat "${MATCHED_PATTERN}" \
            --arg fp "${FILE_PATH}" \
            '{timestamp: $ts, event: "canary_cap_reached", tool_name: (.tool_name // "unknown"), file_path: $fp, matched_pattern: $pat}' \
            >> "${LOG_FILE}" 2>/dev/null || true
    else
        echo "{\"timestamp\":\"${TIMESTAMP}\",\"event\":\"canary_cap_reached\",\"file_path\":\"${FILE_PATH}\",\"matched_pattern\":\"${MATCHED_PATTERN}\"}" \
            >> "${LOG_FILE}" 2>/dev/null || true
    fi
    echo "Canary cap reached for ${FILE_PATH} (${MAX_BLOCKS} blocks); allowing write -- see CLAUDE/skills/canary-phrase-guard.md" >&2
    exit 0
fi

# Persist the new counter and block the write.
echo "${NEW_COUNT}" > "${COUNTER_FILE}" 2>/dev/null || true
echo "CANARY DETECTED: '${MATCHED_PATTERN}' in ${FILE_PATH} -- implement before continuing (block ${NEW_COUNT}/${MAX_BLOCKS})" >&2
exit 2
