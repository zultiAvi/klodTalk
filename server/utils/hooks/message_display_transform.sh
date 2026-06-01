#!/bin/bash
# MessageDisplay hook -- transforms assistant messages before they reach the
# user/WebSocket client.
#
# Pipeline:
#   1. Read MessageDisplay JSON payload from stdin.
#   2. Strip ANSI escape sequences (CSI color/format codes).
#   3. If the transformed message exceeds 64 KB, truncate to the cap and spill
#      the FULL original (post-ANSI-strip) body to
#         /workspace/.klodTalk/team/current/message_overflow_<UTC-ts>.txt
#      The kept tail is replaced with:
#         ... [truncated, see message_overflow_<ts>.txt]
#   4. Emit:
#         {"hookSpecificOutput":{"hookEventName":"MessageDisplay","updatedMessage":"<text>"}}
#      when a change was made, or `{}` for pass-through.
#
# CRITICAL: This script MUST always `exit 0`. A non-zero exit would block the
# response stream and the client would see nothing. All internal errors fall
# through to `{}` (pass-through).
#
# Companion: server/utils/hooks/sanitize_bash_output.sh handles the inbound
# (PostToolUse) side. This hook is the outbound (MessageDisplay) counterpart.
#
# Source: Claude Code v2.1.152 release notes --
#   https://github.com/anthropics/claude-code/releases
# See CLAUDE/skills/message-display-hook.md for the full pattern.

{
    INPUT="$(cat 2>/dev/null)" || INPUT=""

    if [ -z "${INPUT}" ] || ! command -v jq >/dev/null 2>&1 \
        || ! command -v python3 >/dev/null 2>&1; then
        printf '%s' '{}'
        exit 0
    fi

    # Extract the message body. The MessageDisplay payload field name is
    # `message` per the v2.1.152 release notes; fall back to common
    # alternatives defensively.
    ORIGINAL="$(printf '%s' "${INPUT}" | jq -r '
        .message
        // .updatedMessage
        // .content
        // ""
    ' 2>/dev/null)" || ORIGINAL=""

    if [ -z "${ORIGINAL}" ]; then
        printf '%s' '{}'
        exit 0
    fi

    OVERFLOW_DIR="/workspace/.klodTalk/team/current"
    mkdir -p "${OVERFLOW_DIR}" 2>/dev/null || true

    TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ 2>/dev/null)" \
        || TIMESTAMP="unknown"

    TRANSFORMED="$(
        ORIGINAL_TEXT="${ORIGINAL}" \
        OVERFLOW_DIR="${OVERFLOW_DIR}" \
        TIMESTAMP="${TIMESTAMP}" \
        python3 - <<'PY' 2>/dev/null
import json
import os
import re
import sys

original = os.environ.get("ORIGINAL_TEXT", "")
overflow_dir = os.environ.get("OVERFLOW_DIR", "")
ts = os.environ.get("TIMESTAMP", "unknown")

# Strip ANSI CSI escape sequences (color/format). Mirrors the sed pattern in
# sanitize_bash_output.sh: sed 's/\x1b\[[0-9;]*m//g'. We extend slightly to
# cover the broader CSI family while remaining conservative.
ansi_csi = re.compile(r"\x1b\[[0-9;]*m")
stripped = ansi_csi.sub("", original)

ansi_changed = stripped != original

# 64 KB cap measured on the post-strip UTF-8 byte length.
CAP = 64 * 1024
encoded = stripped.encode("utf-8", errors="replace")
truncated = False
final_text = stripped

if len(encoded) > CAP:
    overflow_name = "message_overflow_{}.txt".format(ts)
    overflow_path = os.path.join(overflow_dir, overflow_name)
    try:
        with open(overflow_path, "w", encoding="utf-8", errors="replace") as fh:
            fh.write(stripped)
    except Exception:
        # If we cannot spill, fall through to pass-through.
        sys.stdout.write("{}")
        sys.exit(0)
    # Reserve room for the trailer and cut at a safe byte boundary.
    trailer = "\n... [truncated, see {}]".format(overflow_name)
    trailer_b = trailer.encode("utf-8")
    keep = encoded[: max(0, CAP - len(trailer_b))]
    # Decode safely on byte boundary.
    final_text = keep.decode("utf-8", errors="ignore") + trailer
    truncated = True

if not ansi_changed and not truncated:
    sys.stdout.write("{}")
    sys.exit(0)

payload = {
    "hookSpecificOutput": {
        "hookEventName": "MessageDisplay",
        "updatedMessage": final_text,
    }
}
sys.stdout.write(json.dumps(payload))
PY
    )" || TRANSFORMED=""

    if [ -n "${TRANSFORMED}" ]; then
        printf '%s' "${TRANSFORMED}"
        exit 0
    fi

    printf '%s' '{}'
    exit 0
} 2>/dev/null

# Defensive: in case the block above somehow exits non-zero.
printf '%s' '{}'
exit 0
