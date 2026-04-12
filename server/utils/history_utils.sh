#!/bin/bash
# History / logging utility functions for KlodTalk team pipeline.
# Writes to .klodTalk/history/<YYYY-MM-DD>.log, same directory the server uses,
# so pipeline events appear in the unified daily log.

HISTORY_DIR="/workspace/.klodTalk/history"

_history_ensure_dir() {
    mkdir -p "${HISTORY_DIR}"
}

_history_timestamp() {
    date -u "+%Y-%m-%dT%H:%M:%SZ"
}

_history_log_file() {
    echo "${HISTORY_DIR}/$(date -u +%Y-%m-%d).log"
}

# Log a single line entry.
# Usage: history_log <project_name> <user_name> <message>
history_log() {
    local project_name="$1"
    local user_name="$2"
    local message="$3"
    _history_ensure_dir
    printf "[%s] [%s] [%s] %s\n" \
        "$(_history_timestamp)" "${user_name}" "${project_name}" "${message}" \
        >> "$(_history_log_file)"
}

# Log the start of a work session.
# Usage: history_log_session_start <user_name> <project_name> <request>
history_log_session_start() {
    local user_name="$1"
    local project_name="$2"
    local request="$3"
    _history_ensure_dir
    {
        printf "[%s] [%s] [%s] === TEAM SESSION START ===\n" \
            "$(_history_timestamp)" "${user_name}" "${project_name}"
        printf "[%s] [%s] [%s] REQUEST: %s\n" \
            "$(_history_timestamp)" "${user_name}" "${project_name}" "${request}"
    } >> "$(_history_log_file)"
}

# Log a pipeline result (multi-line safe).
# Usage: history_log_result <project_name> <user_name> <result>
history_log_result() {
    local project_name="$1"
    local user_name="$2"
    local result="$3"
    _history_ensure_dir
    {
        printf "[%s] [%s] [%s] --- RESULT ---\n" \
            "$(_history_timestamp)" "${user_name}" "${project_name}"
        echo "${result}" | while IFS= read -r line; do
            printf "[%s] [%s] [%s]   %s\n" \
                "$(_history_timestamp)" "${user_name}" "${project_name}" "${line}"
        done
        printf "[%s] [%s] [%s] --- END RESULT ---\n" \
            "$(_history_timestamp)" "${user_name}" "${project_name}"
    } >> "$(_history_log_file)"
}

# Log the end of a work session.
# Usage: history_log_session_end <user_name> <project_name> <status>
history_log_session_end() {
    local user_name="$1"
    local project_name="$2"
    local status="$3"
    _history_ensure_dir
    printf "[%s] [%s] [%s] === TEAM SESSION END: %s ===\n" \
        "$(_history_timestamp)" "${user_name}" "${project_name}" "${status}" \
        >> "$(_history_log_file)"
}
