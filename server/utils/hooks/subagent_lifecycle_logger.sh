#!/usr/bin/env bash
# SubagentStart / SubagentStop hook logger
# Reads JSON from stdin, extracts subagent lifecycle fields, appends a JSONL line
# to hook_events.jsonl alongside PostToolUse entries.
#
# CRITICAL: This script MUST always exit 0. A non-zero exit blocks Claude's
# tool/lifecycle pipeline. This is an observational hook only.
#
# Register in .claude/settings.json under hooks.SubagentStart and hooks.SubagentStop,
# each with "matcher": "" so every subagent event is captured.
#
# Event fields written per line:
#   timestamp        - hook fire time, ISO-8601 UTC with millis
#   event_type       - "SubagentStart" or "SubagentStop"
#   agent_id         - the subagent's own id
#   parent_agent_id  - the spawning agent's id
#   subagent_type    - role tag (e.g. coder/planner/reviewer) when provided
#   description      - free-form Task description when provided
#   background_tasks - count of pending background tasks at Stop time (Stop only)
#   session_crons    - list of scheduled cron entries at Stop time (Stop only)
#
# Source: anthropics/claude-code v2.1.145-v2.1.147 release notes
# (https://github.com/anthropics/claude-code/releases)

{
    INPUT="$(cat 2>/dev/null)" || INPUT=""

    LOG_DIR="/workspace/.klodTalk/team/current"
    LOG_FILE="${LOG_DIR}/hook_events.jsonl"
    mkdir -p "${LOG_DIR}" 2>/dev/null || true

    # event_type is passed as $1 by the settings.json command wrapper
    EVENT_TYPE="${1:-SubagentEvent}"

    TIMESTAMP="$(date -u +"%Y-%m-%dT%H:%M:%S.%3NZ" 2>/dev/null)" \
        || TIMESTAMP="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

    if command -v jq &>/dev/null && [ -n "${INPUT}" ]; then
        LOG_ENTRY="$(echo "${INPUT}" | jq -c \
            --arg ts "${TIMESTAMP}" \
            --arg ev "${EVENT_TYPE}" \
            '{
                timestamp: $ts,
                event_type: $ev,
                agent_id: (.agent_id // null),
                parent_agent_id: (.parent_agent_id // null),
                subagent_type: (.subagent_type // null),
                description: (.description // null),
                background_tasks: (.background_tasks // null),
                session_crons: (.session_crons // null)
            }' 2>/dev/null)" || LOG_ENTRY=""

        if [ -n "${LOG_ENTRY}" ]; then
            echo "${LOG_ENTRY}" >> "${LOG_FILE}" 2>/dev/null || true
        fi
    elif [ -n "${INPUT}" ]; then
        # Fallback: log raw payload with timestamp and event type
        echo "{\"timestamp\":\"${TIMESTAMP}\",\"event_type\":\"${EVENT_TYPE}\",\"raw\":true,\"data\":$(echo "${INPUT}" | head -c 4096 | jq -Rs . 2>/dev/null || echo '""')}" >> "${LOG_FILE}" 2>/dev/null || true
    fi
} 2>/dev/null

# ALWAYS exit 0 - observational hook, must not block the pipeline
exit 0
