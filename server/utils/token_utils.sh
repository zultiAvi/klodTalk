#!/bin/bash
# Token-aware Claude runner for KlodTalk team pipeline.
# Requires file_utils.sh to be sourced first (for TOKEN_FILE, file_append_tokens).

# Run claude with --output-format json, capture token usage, and accumulate
# into TOKEN_FILE.  Returns claude's exit code unchanged.
#
# Usage: claude_run_with_tokens <timeout_secs> <prompt> [claude_flag ...]
#
# Examples:
#   claude_run_with_tokens 1800 "${TASK_PROMPT}" --dangerously-skip-permissions
#   claude_run_with_tokens 1800 "${TASK_PROMPT}" --allowedTools "Read,Write,Edit"
claude_run_with_tokens() {
    local timeout_secs="$1"
    local prompt="$2"
    shift 2
    # remaining args are extra claude flags

    local tmp_out
    tmp_out=$(mktemp)

    timeout "${timeout_secs}" claude "$@" --output-format json -p "${prompt}" > "${tmp_out}"
    local exit_code=$?

    # Parse JSON output and accumulate token counts
    if [[ -s "${tmp_out}" ]]; then
        TOKEN_FILE_PATH="${TOKEN_FILE}" TMP_OUT="${tmp_out}" python3 -c "
import json, os, sys

tmp = os.environ['TMP_OUT']
f   = os.environ['TOKEN_FILE_PATH']

try:
    with open(tmp) as fh:
        data = json.load(fh)
    usage = data.get('usage', {})
    inp   = usage.get('input_tokens', 0)
    out   = usage.get('output_tokens', 0)
    cache = usage.get('cache_read_input_tokens', 0)
    cost  = float(data.get('total_cost_usd', 0) or 0)
except Exception:
    sys.exit(0)

if not inp and not out:
    sys.exit(0)

try:
    with open(f) as fh:
        acc = json.load(fh)
except Exception:
    acc = {'input_tokens': 0, 'output_tokens': 0, 'cache_tokens': 0, 'total_cost_usd': 0.0}

acc['input_tokens']   += inp
acc['output_tokens']  += out
acc['cache_tokens']   += cache
acc['total_cost_usd'] += cost

os.makedirs(os.path.dirname(f), exist_ok=True)
with open(f, 'w') as fh:
    json.dump(acc, fh)
" 2>/dev/null || true
    fi

    rm -f "${tmp_out}"
    return "${exit_code}"
}
