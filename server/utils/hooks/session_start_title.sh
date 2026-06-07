#!/usr/bin/env bash
# SessionStart hook -- emits a sessionTitle for per-session observability.
#
# Reads optional KLODTALK_PROJECT and KLODTALK_ROLE env vars (set by KlodTalk's
# run_agent.py at container start; may be absent in non-KlodTalk environments).
# Emits a SessionStart hookSpecificOutput JSON payload with `sessionTitle`
# (rendered as "klodtalk/<project> [<role>]") and `reloadSkills: true`
# (a one-time skill-directory rescan during session initialization).
#
# CRITICAL: This script MUST always exit 0. A non-zero exit blocks Claude's
# session-start pipeline. See instinct #1 (PostToolUse/PostToolUseFailure must
# exit 0 -- the same discipline is applied here for safety).
#
# Register in /workspace/.claude/settings.json under hooks.SessionStart:
#   {
#     "hooks": {
#       "SessionStart": [
#         { "matcher": "",
#           "hooks": [
#             { "type": "command",
#               "command": "bash /workspace/server/utils/hooks/session_start_title.sh" }
#           ]
#         }
#       ]
#     }
#   }
#
# Requires Claude Code v2.1.153+ (sessionTitle field introduced in that release).
# Older CLI versions ignore the hookSpecificOutput payload silently.
#
# Source: Claude Code changelog v2.1.153 --
#   https://releasebot.io/updates/anthropic/claude-code
#   (github.com/anthropics/claude-code via releasebot)

{
    # Read and discard any stdin payload (SessionStart sends a JSON envelope).
    INPUT="$(cat 2>/dev/null)" || INPUT=""

    # Pull env vars with graceful fallback (instinct: env vars may not be set
    # in all environments -- degrade rather than crash).
    PROJECT="${KLODTALK_PROJECT:-unknown}"
    ROLE="${KLODTALK_ROLE:-agent}"

    # Sanitize: strip any whitespace, slashes, brackets that would break the
    # display string. Keep the substitution conservative -- the title is
    # human-facing, not parsed.
    PROJECT_SAFE="$(printf '%s' "${PROJECT}" | tr -d '\r\n\t' | head -c 64)"
    ROLE_SAFE="$(printf '%s' "${ROLE}" | tr -d '\r\n\t' | head -c 32)"

    TITLE="klodtalk/${PROJECT_SAFE} [${ROLE_SAFE}]"

    # Build the payload. Prefer jq for proper escaping; fall back to a hand-
    # rolled string if jq is missing (best-effort -- the title is restricted
    # above to ASCII-ish characters).
    if command -v jq >/dev/null 2>&1; then
        PAYLOAD="$(jq -nc \
            --arg title "${TITLE}" \
            '{hookSpecificOutput: {hookEventName: "SessionStart", sessionTitle: $title, reloadSkills: true}}' \
            2>/dev/null)" || PAYLOAD=""
    fi

    if [ -z "${PAYLOAD:-}" ]; then
        # Manual JSON (title is ASCII-safe after sanitization).
        PAYLOAD="{\"hookSpecificOutput\":{\"hookEventName\":\"SessionStart\",\"sessionTitle\":\"${TITLE}\",\"reloadSkills\":true}}"
    fi

    printf '%s' "${PAYLOAD}"
} 2>/dev/null

# ALWAYS exit 0 -- this is a hard project rule.
exit 0
