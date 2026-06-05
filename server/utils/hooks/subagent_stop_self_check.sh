#!/usr/bin/env bash
# SubagentStop hook -- injects a DONE-WHEN self-check reminder into a finishing
# `coder` sub-agent via hookSpecificOutput.additionalContext.
#
# On SubagentStop, Stop/SubagentStop hooks may emit a JSON object on stdout:
#   {"hookSpecificOutput":{"additionalContext":"<text>"}}
# whose text is fed back to the model (Claude Code v2.1.163+). We use it to
# remind a coder to run its DONE-WHEN self-check before declaring done.
#
# Behaviour:
#   - role == coder  -> emit the reminder JSON ONCE per sub-agent, then exit 0.
#   - any other role -> emit nothing, exit 0.
#
# Loop avoidance: this hook re-injects context, which could in principle make a
# coder run again and re-trigger SubagentStop. To guarantee it can never create
# a stop loop it is BOTH role-gated AND idempotent: a per-agent marker file is
# written the first time it fires for a given agent_id, and on any subsequent
# SubagentStop for that same agent_id it emits nothing. The marker lives under a
# temp dir so it is naturally cleaned up between container lifetimes.
#
# CLI compatibility: older CLIs (< 2.1.163) ignore unknown hookSpecificOutput
# keys, so emitting this JSON on an older CLI is a safe no-op (the reminder is
# simply dropped). No version probing is required.
#
# CRITICAL: This script MUST always exit 0. A non-zero exit blocks Claude's
# stop pipeline. This hook only ADDS context; it never blocks.
#
# This is SEPARATE from the observational subagent_lifecycle_logger.sh -- that
# hook only logs JSONL and never emits additionalContext. Keep them distinct.
#
# Register in /workspace/.claude/settings.json under hooks.SubagentStop with
# "matcher": "" (see CLAUDE/skills/stop-hook-additional-context.md).
#
# Source: Claude Code CHANGELOG v2.1.163 --
#   https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md

# NOTE: keep this text free of literal double-quote characters so the no-jq
# fallback below (which builds the JSON by hand) stays valid JSON.
CODER_REMINDER='Before declaring done, run your DONE-WHEN self-check: score 0-10 against the plan.md DONE-WHEN line, and if it is below 7 do another pass. Record the score in your handoff before finishing.'

{
    INPUT="$(cat 2>/dev/null)" || INPUT=""

    # Resolve the role. SubagentStart carries `subagent_type`; the hook payload
    # may also carry `agent_type` (see hook-agent-type-filter.md). Try both, and
    # fall back to the KLODTALK_ROLE env var set by run_agent.py at container
    # start. Default to "unknown" so unknown roles are silently skipped.
    ROLE="unknown"
    AGENT_ID="unknown"
    if command -v jq >/dev/null 2>&1 && [ -n "${INPUT}" ]; then
        ROLE="$(printf '%s' "${INPUT}" | jq -r '.subagent_type // .agent_type // empty' 2>/dev/null)"
        AGENT_ID="$(printf '%s' "${INPUT}" | jq -r '.agent_id // empty' 2>/dev/null)"
    fi
    [ -z "${ROLE}" ] && ROLE="${KLODTALK_ROLE:-unknown}"
    [ -z "${AGENT_ID}" ] && AGENT_ID="unknown"

    # Only the coder gets the self-check nudge.
    if [ "${ROLE}" != "coder" ]; then
        exit 0
    fi

    # Idempotency: fire at most once per agent_id to avoid a stop loop. Sanitize
    # agent_id for use as a filename (alphanumerics, dash, underscore only).
    AGENT_ID_SAFE="$(printf '%s' "${AGENT_ID}" | tr -cd 'A-Za-z0-9_-' | head -c 128)"
    [ -z "${AGENT_ID_SAFE}" ] && AGENT_ID_SAFE="unknown"
    MARKER_DIR="${TMPDIR:-/tmp}/klodtalk_subagent_self_check"
    MARKER_FILE="${MARKER_DIR}/${AGENT_ID_SAFE}.done"
    mkdir -p "${MARKER_DIR}" 2>/dev/null || true
    if [ -e "${MARKER_FILE}" ]; then
        # Already nudged this sub-agent once -- stay silent to avoid a loop.
        exit 0
    fi
    : > "${MARKER_FILE}" 2>/dev/null || true

    # Emit the additionalContext payload. Prefer jq for proper escaping.
    PAYLOAD=""
    if command -v jq >/dev/null 2>&1; then
        PAYLOAD="$(jq -nc --arg ctx "${CODER_REMINDER}" \
            '{hookSpecificOutput: {additionalContext: $ctx}}' 2>/dev/null)" || PAYLOAD=""
    fi
    if [ -z "${PAYLOAD}" ]; then
        # Fallback: the reminder is static and ASCII-safe.
        PAYLOAD="{\"hookSpecificOutput\":{\"additionalContext\":\"${CODER_REMINDER}\"}}"
    fi
    printf '%s' "${PAYLOAD}"
} 2>/dev/null

# ALWAYS exit 0 -- this is a hard project rule.
exit 0
