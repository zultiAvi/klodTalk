#!/bin/bash
# File I/O utility functions for KlodTalk team pipeline.
# Centralises all paths so they can be updated in one place.

IN_FILE="/workspace/.klodTalk/in_messages/in_message.txt"
OUT_FILE="/workspace/.klodTalk/out_messages/out_message.txt"
CHANGED_FILES_FILE="/workspace/.klodTalk/changed_files.txt"
PLANNER_MESSAGE_FILE="/workspace/.klodTalk/out_messages/planner_message.txt"
CODER_MESSAGE_FILE="/workspace/.klodTalk/out_messages/coder_message.txt"

TEAM_DIR="/workspace/.klodTalk/team/current"
PLAN_MD="${TEAM_DIR}/plan.md"
PLAN_META="${TEAM_DIR}/plan_meta.txt"
CODER_OUTPUT="${TEAM_DIR}/coder_output.txt"
REVIEWER_OUTPUT="${TEAM_DIR}/reviewer_output.txt"
TOKEN_FILE="${TEAM_DIR}/token_usage.json"

# External file sharing
REQUESTS_DIR="/workspace/.klodTalk/requests"
FILE_REQUEST_PATH="${REQUESTS_DIR}/file_request.txt"
FILE_FULFILLED_PATH="${REQUESTS_DIR}/file_fulfilled.txt"
SHARED_FILES_DIR="/workspace/.klodTalk/shared_files"

_file_ensure_team_dir() {
    mkdir -p "${TEAM_DIR}"
}

# ── Security helpers ──────────────────────────────────────────────────────────

# Sanitize a username: strip non-printable characters and limit to 64 chars.
# Used by all team scripts to prevent prompt injection via a crafted username.
# Usage: sanitize_user_name <raw_name>
sanitize_user_name() {
    # Use LC_ALL=C so tr operates on bytes, matching the Python sanitizer
    # which strips characters outside the printable ASCII range \x20-\x7E.
    printf '%s' "${1}" | LC_ALL=C tr -cd '\040-\176' | cut -c1-64
}

# ── Input ─────────────────────────────────────────────────────────────────────

# Print the user's accumulated request from in_message.txt.
file_read_request() {
    [[ -f "${IN_FILE}" ]] && cat "${IN_FILE}" || echo ""
}

# ── Final output ──────────────────────────────────────────────────────────────

# Write the final task summary to out_message.txt.
# The server reads this, broadcasts it to users, and clears in_message.txt.
# Usage: file_write_output <message>
file_write_output() {
    mkdir -p "$(dirname "${OUT_FILE}")"
    printf "%s\n" "$1" > "${OUT_FILE}"
}

# ── Plan files ────────────────────────────────────────────────────────────────

# Usage: file_write_plan <content>
file_write_plan() {
    _file_ensure_team_dir
    printf "%s\n" "$1" > "${PLAN_MD}"
}

file_read_plan() {
    [[ -f "${PLAN_MD}" ]] && cat "${PLAN_MD}" || echo ""
}

# Write planner metadata.
# Usage: file_write_plan_meta <is_simple> <review_iterations> <complexity>
# Uses printf (not a heredoc) so that values containing backticks or $(...) are
# written literally without shell expansion.
file_write_plan_meta() {
    _file_ensure_team_dir
    local needs_exec="${4:-}"
    if [[ -n "$needs_exec" ]]; then
        printf 'IS_SIMPLE=%s\nREVIEW_ITERATIONS=%s\nCOMPLEXITY=%s\nNEEDS_EXECUTION=%s\n' "$1" "$2" "$3" "$4" > "${PLAN_META}"
    else
        printf 'IS_SIMPLE=%s\nREVIEW_ITERATIONS=%s\nCOMPLEXITY=%s\n' "$1" "$2" "$3" > "${PLAN_META}"
    fi
}

# Read a single value from plan_meta.txt.
# Usage: file_read_plan_meta <KEY>  (e.g. IS_SIMPLE, REVIEW_ITERATIONS)
# Uses awk for exact key matching — safe against regex metacharacters in the key name.
file_read_plan_meta() {
    [[ -f "${PLAN_META}" ]] \
        && awk -F= -v key="${1}" '$1 == key { print $2 }' "${PLAN_META}" \
        || echo ""
}

# ── Coder/reviewer exchange files ─────────────────────────────────────────────

# Usage: file_write_coder_output <content>
file_write_coder_output() {
    _file_ensure_team_dir
    printf "%s\n" "$1" > "${CODER_OUTPUT}"
}

file_read_coder_output() {
    [[ -f "${CODER_OUTPUT}" ]] && cat "${CODER_OUTPUT}" || echo ""
}

# Usage: file_write_reviewer_output <content>
file_write_reviewer_output() {
    _file_ensure_team_dir
    printf "%s\n" "$1" > "${REVIEWER_OUTPUT}"
}

file_read_reviewer_output() {
    [[ -f "${REVIEWER_OUTPUT}" ]] && cat "${REVIEWER_OUTPUT}" || echo ""
}

# ── Changed files list ────────────────────────────────────────────────────────

file_write_changed_files() {
    printf "%s\n" "$1" > "${CHANGED_FILES_FILE}"
}

file_read_changed_files() {
    [[ -f "${CHANGED_FILES_FILE}" ]] && cat "${CHANGED_FILES_FILE}" || echo ""
}

# ── Pipeline phase broadcast messages ────────────────────────────────────────

# Write planner summary to planner_message.txt (atomic write).
# Server polls this file, broadcasts as role "planner", then deletes it.
# Usage: file_write_planner_message <content>
file_write_planner_message() {
    local dest="${PLANNER_MESSAGE_FILE}"
    local tmp="${dest}.tmp"
    mkdir -p "$(dirname "${dest}")"
    printf "%s\n" "$1" > "${tmp}"
    mv "${tmp}" "${dest}"
}

# Write coder summary to coder_message.txt (atomic write).
# Server polls this file, broadcasts as role "coder", then deletes it.
# Usage: file_write_coder_message <content>
file_write_coder_message() {
    local dest="${CODER_MESSAGE_FILE}"
    local tmp="${dest}.tmp"
    mkdir -p "$(dirname "${dest}")"
    printf "%s\n" "$1" > "${tmp}"
    mv "${tmp}" "${dest}"
}

# ── Token tracking ────────────────────────────────────────────────────────────

# Accumulate token counts into TOKEN_FILE (JSON).
# Usage: file_append_tokens <input> <output> <cache> <cost_usd>
file_append_tokens() {
    local inp="${1:-0}"
    local out="${2:-0}"
    local cache="${3:-0}"
    local cost="${4:-0}"
    TOKEN_FILE_PATH="${TOKEN_FILE}" \
    _TOK_INP="${inp}" _TOK_OUT="${out}" _TOK_CACHE="${cache}" _TOK_COST="${cost}" \
    python3 -c "
import json, os
f = os.environ['TOKEN_FILE_PATH']
try:
    with open(f) as fh:
        acc = json.load(fh)
except Exception:
    acc = {'input_tokens': 0, 'output_tokens': 0, 'cache_tokens': 0, 'total_cost_usd': 0.0}
acc['input_tokens']   += int(os.environ.get('_TOK_INP',   '0') or 0)
acc['output_tokens']  += int(os.environ.get('_TOK_OUT',   '0') or 0)
acc['cache_tokens']   += int(os.environ.get('_TOK_CACHE', '0') or 0)
acc['total_cost_usd'] += float(os.environ.get('_TOK_COST','0') or 0)
os.makedirs(os.path.dirname(f), exist_ok=True)
with open(f, 'w') as fh:
    json.dump(acc, fh)
" 2>/dev/null || true
}

# Read accumulated token totals and return a formatted summary string.
# Prints nothing if no data is available.
file_read_token_summary() {
    [[ ! -f "${TOKEN_FILE}" ]] && return
    TOKEN_FILE_PATH="${TOKEN_FILE}" python3 -c "
import json, os, sys
f = os.environ['TOKEN_FILE_PATH']
try:
    with open(f) as fh:
        data = json.load(fh)
except Exception:
    sys.exit(0)
inp   = data.get('input_tokens', 0)
out   = data.get('output_tokens', 0)
cache = data.get('cache_tokens', 0)
cost  = data.get('total_cost_usd', 0)
if not inp and not out:
    sys.exit(0)
cache_part = f' ({cache:,} cached)' if cache else ''
token_part = f'[Tokens: {inp:,} in{cache_part} / {out:,} out'
if cost:
    print(f'{token_part} | Cost: \${cost:.4f}]')
else:
    print(f'{token_part}]')
" 2>/dev/null || true
}

# ── Session reset ─────────────────────────────────────────────────────────────

# DESTRUCTIVE: removes the entire team session directory (rm -rf) and recreates
# it empty.  Call only at the very start of a new pipeline run (run_planner.sh).
# Renamed from file_clear_team_session to make the destructive intent visible.
file_reset_team_session() {
    rm -rf "${TEAM_DIR}"
    rm -f "${CHANGED_FILES_FILE}"
    _file_ensure_team_dir
}
