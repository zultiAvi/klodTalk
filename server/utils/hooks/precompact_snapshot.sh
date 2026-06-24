#!/usr/bin/env bash
# PreCompact hook -- snapshot task state before a context-window compaction pass.
#
# Fires immediately before the Claude Code CLI performs a context compaction
# pass. It writes a single JSON file to
# /workspace/.klodTalk/team/current/compaction_snapshot_<timestamp>.json
# preserving the original task, current pipeline stage, and recent hook events
# so a long-running agent's thread can be reconstructed after compaction.
#
# CRITICAL: This script MUST always exit 0. A non-zero exit from PreCompact would
# block the compaction itself, defeating compaction-api-opt-in.md. This is an
# observational hook only -- catch all internal errors and fall through to exit 0.
#
# Register in /workspace/.claude/settings.json under hooks.PreCompact with
# "matcher": "" so every compaction event is captured.
#
# Snapshot fields:
#   original_task       - contents of in_messages/in_message.txt (if present)
#   pipeline_stage      - contents of team/current/progress.json (if present)
#   recent_hook_events  - last 5 lines of team/current/hook_events.jsonl
#   timestamp           - ISO-8601 UTC at snapshot time
#
# Requires Claude Code v2.1.169+ (PreCompact lifecycle hook). Older CLI versions
# never fire this hook (it is a no-op, not an error). See precompact-context-guard.md.
#
# Source: vinicius91carvalho/.claude (community hook collection) +
#   anthropics/claude-code issues #43946 / #43733 --
#   https://github.com/anthropics/claude-code/issues/43946

{
    INPUT="$(cat 2>/dev/null)" || INPUT=""

    OUT_DIR="/workspace/.klodTalk/team/current"
    mkdir -p "${OUT_DIR}" 2>/dev/null || true

    TIMESTAMP="$(date -u +"%Y-%m-%dT%H:%M:%S.%3NZ" 2>/dev/null)" \
        || TIMESTAMP="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

    # Filesystem-safe timestamp for the filename (no ':' which is invalid on some FS).
    FS_TS="$(printf '%s' "${TIMESTAMP}" | tr ':' '-')"
    SNAP_FILE="${OUT_DIR}/compaction_snapshot_${FS_TS}.json"

    ORIG_TASK_FILE="/workspace/.klodTalk/in_messages/in_message.txt"
    PROGRESS_FILE="${OUT_DIR}/progress.json"
    EVENTS_FILE="${OUT_DIR}/hook_events.jsonl"

    ORIG_TASK=""
    [ -f "${ORIG_TASK_FILE}" ] && ORIG_TASK="$(cat "${ORIG_TASK_FILE}" 2>/dev/null)" || ORIG_TASK=""

    PIPELINE_STAGE=""
    [ -f "${PROGRESS_FILE}" ] && PIPELINE_STAGE="$(cat "${PROGRESS_FILE}" 2>/dev/null)" || PIPELINE_STAGE=""

    RECENT_EVENTS=""
    [ -f "${EVENTS_FILE}" ] && RECENT_EVENTS="$(tail -n 5 "${EVENTS_FILE}" 2>/dev/null)" || RECENT_EVENTS=""

    if command -v jq >/dev/null 2>&1; then
        # recent_hook_events: split the tail into an array of trimmed lines.
        SNAP="$(jq -nc \
            --arg ts "${TIMESTAMP}" \
            --arg task "${ORIG_TASK}" \
            --arg stage "${PIPELINE_STAGE}" \
            --arg events "${RECENT_EVENTS}" \
            '{
                timestamp: $ts,
                original_task: $task,
                pipeline_stage: $stage,
                recent_hook_events: ($events | split("\n") | map(select(length > 0)))
            }' 2>/dev/null)" || SNAP=""
        [ -n "${SNAP}" ] && printf '%s\n' "${SNAP}" > "${SNAP_FILE}" 2>/dev/null || true
    else
        # No-jq fallback: hand-build JSON with jq -Rs-style escaping unavailable, so
        # encode each field via a python helper if present, else emit a minimal record
        # that never contains unescaped quotes (only the timestamp, which is safe).
        if command -v python3 >/dev/null 2>&1; then
            python3 - "${SNAP_FILE}" "${TIMESTAMP}" "${ORIG_TASK_FILE}" "${PROGRESS_FILE}" "${EVENTS_FILE}" <<'PY' 2>/dev/null || true
import json, os, sys
snap_file, ts, task_f, prog_f, ev_f = sys.argv[1:6]
def read(p):
    try:
        with open(p) as fh:
            return fh.read()
    except Exception:
        return ""
events = read(ev_f).splitlines()[-5:]
rec = {
    "timestamp": ts,
    "original_task": read(task_f),
    "pipeline_stage": read(prog_f),
    "recent_hook_events": [e for e in events if e],
}
try:
    with open(snap_file, "w") as fh:
        json.dump(rec, fh)
        fh.write("\n")
except Exception:
    pass
PY
        else
            # Last-resort minimal record -- only the (safe) timestamp is interpolated.
            printf '{"timestamp":"%s","original_task":"","pipeline_stage":"","recent_hook_events":[]}\n' \
                "${TIMESTAMP}" > "${SNAP_FILE}" 2>/dev/null || true
        fi
    fi
} 2>/dev/null

# ALWAYS exit 0 -- a non-zero exit would block the compaction pass.
exit 0
