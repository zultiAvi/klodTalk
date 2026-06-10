#!/usr/bin/env bash
# PostSession hook -- snapshot per-role session transcript + token usage.
#
# Fires at the SESSION level (after the CLI session itself closes), NOT at the
# Task-tool sub-agent level (that is subagent_lifecycle_logger.sh). It copies the
# session transcript file plus a one-line token-usage summary into
# .klodTalk/team/current/ before the container is torn down, so a complete
# per-role run record survives container teardown alongside coder_output.txt.
#
# CRITICAL: This script MUST always exit 0. A non-zero exit could disrupt
# Claude's session-teardown pipeline. This is an observational hook only.
#
# Env vars (all OPTIONAL -- every access is guarded, script degrades gracefully):
#   CLAUDE_CODE_SESSION_ID            - the session id (best-guess name)
#   CLAUDE_CODE_ROLE / KLODTALK_ROLE  - role tag (coder/planner/reviewer/...)
#   CLAUDE_CODE_USAGE_INPUT_TOKENS    - input token count for the session
#   CLAUDE_CODE_USAGE_OUTPUT_TOKENS   - output token count for the session
#   CLAUDE_CODE_USAGE_CACHE_READ_TOKENS - cache-read token count for the session
# The hook also reads the stdin JSON envelope and pulls session_id / usage from
# it as a fallback when the env vars are absent.
#
# Output (in /workspace/.klodTalk/team/current/):
#   post_session_log.jsonl                      - one summary line per session
#   session_transcript_<role>_<id8>.jsonl       - copy of the transcript (if found)
#
# Register in /workspace/.claude/settings.json under hooks.PostSession with
# "matcher": "" so every session is captured.
#
# Requires Claude Code v2.1.169+ (PostSession lifecycle hook introduced there).
# Older CLI versions never fire this hook (it is a no-op, not an error).
#
# Source: anthropics/claude-code CHANGELOG v2.1.169 --
#   https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md

{
    INPUT="$(cat 2>/dev/null)" || INPUT=""

    OUT_DIR="/workspace/.klodTalk/team/current"
    mkdir -p "${OUT_DIR}" 2>/dev/null || true

    TIMESTAMP="$(date -u +"%Y-%m-%dT%H:%M:%S.%3NZ" 2>/dev/null)" \
        || TIMESTAMP="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

    # Resolve fields from env vars first, fall back to the stdin JSON envelope.
    SESSION_ID="${CLAUDE_CODE_SESSION_ID:-}"
    ROLE="${CLAUDE_CODE_ROLE:-${KLODTALK_ROLE:-}}"
    IN_TOK="${CLAUDE_CODE_USAGE_INPUT_TOKENS:-}"
    OUT_TOK="${CLAUDE_CODE_USAGE_OUTPUT_TOKENS:-}"
    CACHE_TOK="${CLAUDE_CODE_USAGE_CACHE_READ_TOKENS:-}"

    if command -v jq >/dev/null 2>&1 && [ -n "${INPUT}" ]; then
        [ -z "${SESSION_ID}" ] && SESSION_ID="$(printf '%s' "${INPUT}" | jq -r '.session_id // empty' 2>/dev/null)"
        [ -z "${IN_TOK}" ]   && IN_TOK="$(printf '%s' "${INPUT}" | jq -r '.usage.input_tokens // empty' 2>/dev/null)"
        [ -z "${OUT_TOK}" ]  && OUT_TOK="$(printf '%s' "${INPUT}" | jq -r '.usage.output_tokens // empty' 2>/dev/null)"
        [ -z "${CACHE_TOK}" ] && CACHE_TOK="$(printf '%s' "${INPUT}" | jq -r '.usage.cache_read_input_tokens // empty' 2>/dev/null)"
    fi

    SESSION_ID="${SESSION_ID:-unknown}"
    ROLE="${ROLE:-unknown}"
    IN_TOK="${IN_TOK:-0}"
    OUT_TOK="${OUT_TOK:-0}"
    CACHE_TOK="${CACHE_TOK:-0}"

    # Append a compact usage summary line to the shared log.
    if command -v jq >/dev/null 2>&1; then
        LINE="$(jq -nc \
            --arg ts "${TIMESTAMP}" \
            --arg sid "${SESSION_ID}" \
            --arg role "${ROLE}" \
            --arg in "${IN_TOK}" \
            --arg out "${OUT_TOK}" \
            --arg cache "${CACHE_TOK}" \
            '{timestamp:$ts, event_type:"PostSession", session_id:$sid, role:$role,
              input_tokens:($in|tonumber? // 0),
              output_tokens:($out|tonumber? // 0),
              cache_read_tokens:($cache|tonumber? // 0)}' 2>/dev/null)" || LINE=""
        [ -n "${LINE}" ] && echo "${LINE}" >> "${OUT_DIR}/post_session_log.jsonl" 2>/dev/null || true
    else
        echo "{\"timestamp\":\"${TIMESTAMP}\",\"event_type\":\"PostSession\",\"session_id\":\"${SESSION_ID}\",\"role\":\"${ROLE}\"}" \
            >> "${OUT_DIR}/post_session_log.jsonl" 2>/dev/null || true
    fi

    # Copy the session transcript if it can be located. The standard project
    # session store lives under ~/.claude/projects/<dashed-cwd>/sessions/.
    if [ "${SESSION_ID}" != "unknown" ]; then
        PROJ_DIR="$(printf '%s' "/workspace" | tr '/' '-' | sed 's/^-//')"
        SHORT_ID="${SESSION_ID:0:8}"
        for SRC in \
            "${HOME}/.claude/projects/-${PROJ_DIR}/sessions/${SESSION_ID}.jsonl" \
            "${HOME}/.claude/projects/${PROJ_DIR}/sessions/${SESSION_ID}.jsonl" \
            "${HOME}/.claude/projects/-${PROJ_DIR}/${SESSION_ID}.jsonl"; do
            if [ -f "${SRC}" ]; then
                cp "${SRC}" "${OUT_DIR}/session_transcript_${ROLE}_${SHORT_ID}.jsonl" 2>/dev/null || true
                break
            fi
        done
    fi
} 2>/dev/null

# ALWAYS exit 0 -- observational hook, must not block the pipeline.
exit 0
