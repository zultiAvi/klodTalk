#!/usr/bin/env bash
# PostCompact hook -- confirm a context-window compaction completed.
#
# Fires after the Claude Code CLI finishes a context compaction pass. It appends
# ONE JSONL line to /workspace/.klodTalk/team/current/hook_events.jsonl recording
# the event and the most recent compaction snapshot file written by
# precompact_snapshot.sh, so the pre/post pair can be correlated.
#
# CRITICAL: This script MUST always exit 0. A non-zero exit blocks Claude's
# lifecycle pipeline. This is an observational hook only -- catch all internal
# errors and fall through to exit 0.
#
# Register in /workspace/.claude/settings.json under hooks.PostCompact with
# "matcher": "" so every compaction event is captured.
#
# Event fields written per line:
#   timestamp      - hook fire time, ISO-8601 UTC with millis
#   event_type     - "PostCompact"
#   snapshot_file  - most recent compaction_snapshot_*.json (or null if none)
#
# Requires Claude Code v2.1.169+ (PostCompact lifecycle hook). Older CLI versions
# never fire this hook (it is a no-op, not an error). See precompact-context-guard.md.
#
# Source: vinicius91carvalho/.claude (community hook collection) +
#   anthropics/claude-code issues #43946 / #43733 --
#   https://github.com/anthropics/claude-code/issues/43946

{
    INPUT="$(cat 2>/dev/null)" || INPUT=""

    LOG_DIR="/workspace/.klodTalk/team/current"
    LOG_FILE="${LOG_DIR}/hook_events.jsonl"
    mkdir -p "${LOG_DIR}" 2>/dev/null || true

    TIMESTAMP="$(date -u +"%Y-%m-%dT%H:%M:%S.%3NZ" 2>/dev/null)" \
        || TIMESTAMP="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

    # Best-effort reference to the most recent snapshot file.
    SNAP_FILE="$(ls -1t "${LOG_DIR}"/compaction_snapshot_*.json 2>/dev/null | head -1)" || SNAP_FILE=""

    if command -v jq >/dev/null 2>&1; then
        if [ -n "${SNAP_FILE}" ]; then
            LINE="$(jq -nc \
                --arg ts "${TIMESTAMP}" \
                --arg snap "${SNAP_FILE}" \
                '{timestamp:$ts, event_type:"PostCompact", snapshot_file:$snap}' 2>/dev/null)" || LINE=""
        else
            LINE="$(jq -nc \
                --arg ts "${TIMESTAMP}" \
                '{timestamp:$ts, event_type:"PostCompact", snapshot_file:null}' 2>/dev/null)" || LINE=""
        fi
        [ -n "${LINE}" ] && echo "${LINE}" >> "${LOG_FILE}" 2>/dev/null || true
    else
        # No-jq fallback: snapshot filenames are produced by precompact_snapshot.sh
        # and contain no '"' (timestamp + .json only), so interpolation is safe.
        if [ -n "${SNAP_FILE}" ]; then
            echo "{\"timestamp\":\"${TIMESTAMP}\",\"event_type\":\"PostCompact\",\"snapshot_file\":\"${SNAP_FILE}\"}" \
                >> "${LOG_FILE}" 2>/dev/null || true
        else
            echo "{\"timestamp\":\"${TIMESTAMP}\",\"event_type\":\"PostCompact\",\"snapshot_file\":null}" \
                >> "${LOG_FILE}" 2>/dev/null || true
        fi
    fi
} 2>/dev/null

# ALWAYS exit 0 - observational hook, must not block the pipeline.
exit 0
