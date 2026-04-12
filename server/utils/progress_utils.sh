#!/bin/bash
# Progress tracking and user-notification utilities for KlodTalk team pipeline.
#
# The server polls .klodTalk/out_messages/progress_message.txt every 5 s.
# When found it broadcasts a "progress" type message to connected clients
# and deletes the file — without clearing in_message.txt.

PROGRESS_FILE="/workspace/.klodTalk/out_messages/progress_message.txt"
PROGRESS_STATE_FILE="/workspace/.klodTalk/team/current/progress.json"

_progress_ensure_dirs() {
    mkdir -p "/workspace/.klodTalk/out_messages"
    mkdir -p "/workspace/.klodTalk/team/current"
}

# Notify the user of the current pipeline step.
# Usage: progress_set <current_step> <total_steps> <message>
progress_set() {
    local step="$1"
    local total="$2"
    local message="$3"
    _progress_ensure_dirs

    # Persist state so other scripts can read current step/total.
    # Escape backslashes and double-quotes in message to produce valid JSON.
    local escaped_message
    escaped_message=$(printf '%s' "${message}" | sed 's/\\/\\\\/g; s/"/\\"/g')
    printf '{"step":%s,"total":%s,"message":"%s"}\n' \
        "${step}" "${total}" "${escaped_message}" > "${PROGRESS_STATE_FILE}"

    # Write for server to broadcast (atomic: write to temp then rename).
    local tmp_file="${PROGRESS_FILE}.tmp"
    printf "Step %s/%s: %s\n" "${step}" "${total}" "${message}" > "${tmp_file}"
    mv -f "${tmp_file}" "${PROGRESS_FILE}"

    echo "[progress] Step ${step}/${total}: ${message}"
}

# Send a freeform notification (no step numbers).
# Usage: progress_notify <message>
progress_notify() {
    local message="$1"
    _progress_ensure_dirs
    local tmp_file="${PROGRESS_FILE}.tmp"
    printf "%s\n" "${message}" > "${tmp_file}"
    mv -f "${tmp_file}" "${PROGRESS_FILE}"
    echo "[progress] ${message}"
}

