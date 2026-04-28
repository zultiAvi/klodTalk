#!/usr/bin/env python3
"""Per-session durable log directory at /tmp/klodTalk/<session_id>.klodTalk/.

This module provides a single, durable, per-session log directory that captures
EVERY event for a session — user messages, BTW messages, broadcast payloads
(progress/planner/coder/reviewer/idea/...), agent stdout/stderr, lifecycle
events, errors, and hook events.

Design goals:
- Logging must NEVER raise into callers. All public functions wrap I/O in
  try/except and degrade silently (writing to the Python logger only).
- The log directory survives session deletion: ``delete_session`` does not
  remove ``/tmp/klodTalk/<id>.klodTalk/`` so users can still read the history.
- Pre-existing sessions that were created before this module are tolerated:
  ``read_events`` returns an empty list when the directory is absent.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from typing import Any, Optional

log = logging.getLogger("klodtalk.session_log")

# Use capital T in the directory name per user request:
#   "/tmp/klodTalk/{id}.klodTalk/"
# Note: this is intentionally distinct from session_manager.TEMP_BASE
# (which uses lowercase "klodtalk" for session workspaces). The log dir
# is a separate path so deleting a workspace does not delete the logs.
LOG_BASE = os.environ.get("KLODTALK_LOG_BASE", "/tmp/klodTalk")

# Truncate human-readable lines after this many bytes (full body still in JSONL).
_HUMAN_LINE_LIMIT = 4096


def _now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


def session_log_dir(session_id: str) -> str:
    """Return the path to the per-session log directory, creating it if needed."""
    path = os.path.join(LOG_BASE, f"{session_id}.klodTalk")
    try:
        os.makedirs(path, mode=0o755, exist_ok=True)
    except Exception as e:
        log.error("Failed to create session log dir %s: %s", path, e)
    return path


def init_session_log(
    session_id: str,
    *,
    project_name: str = "",
    user_name: str = "",
    created_at: Optional[str] = None,
) -> None:
    """Write meta.json once when a session is created.

    Subsequent calls are no-ops if meta.json already exists.
    """
    try:
        d = session_log_dir(session_id)
        meta_path = os.path.join(d, "meta.json")
        if not os.path.isfile(meta_path):
            meta = {
                "session_id": session_id,
                "project_name": project_name,
                "user_name": user_name,
                "created_at": created_at or _now_iso(),
            }
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(meta, f)
                f.write("\n")
    except Exception as e:
        log.error("Failed to init session log for %s: %s", session_id, e)


def log_event(
    session_id: str,
    role: str,
    content: str,
    *,
    model: Optional[str] = None,
    extra: Optional[dict] = None,
) -> None:
    """Append a single event to events.jsonl (full) and log.txt (truncated).

    Never raises. Failures are logged to the Python logger and silently dropped.
    """
    if not session_id:
        return
    try:
        d = session_log_dir(session_id)
        ts = _now_iso()
        entry: dict[str, Any] = {
            "timestamp": ts,
            "role": role,
            "content": content if isinstance(content, str) else str(content),
        }
        if model:
            entry["model"] = model
        if extra:
            entry["extra"] = extra
        # 1. Append to JSONL
        try:
            with open(os.path.join(d, "events.jsonl"), "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception as e:
            log.error("Failed to append events.jsonl for %s: %s", session_id, e)
        # 2. Append to human-readable log.txt
        try:
            body = entry["content"]
            if len(body) > _HUMAN_LINE_LIMIT:
                body = body[:_HUMAN_LINE_LIMIT] + " …[truncated]"
            # Replace embedded newlines so each event is one log line.
            body_one_line = body.replace("\n", " ⏎ ")
            with open(os.path.join(d, "log.txt"), "a", encoding="utf-8") as f:
                f.write(f"[{ts}] [{role}] {body_one_line}\n")
        except Exception as e:
            log.error("Failed to append log.txt for %s: %s", session_id, e)
    except Exception as e:
        log.error("log_event failed for %s: %s", session_id, e)


def append_raw(session_id: str, stream: str, data: str) -> None:
    """Append raw stdout/stderr text to agent_stdout.log / agent_stderr.log.

    Each invocation is preceded by a delimiter line so successive runs are
    visually separated:

        \\n--- exec @ <iso ts> ---\\n
    """
    if not session_id or not data:
        return
    if stream not in ("stdout", "stderr"):
        return
    try:
        d = session_log_dir(session_id)
        path = os.path.join(d, f"agent_{stream}.log")
        with open(path, "a", encoding="utf-8") as f:
            f.write(f"\n--- exec @ {_now_iso()} ---\n")
            f.write(data if data.endswith("\n") else data + "\n")
    except Exception as e:
        log.error("Failed to append agent_%s.log for %s: %s", stream, session_id, e)


def append_hook_event(session_id: str, line: str) -> None:
    """Append a single hook line to /tmp/klodTalk/<id>.klodTalk/hook_events.jsonl.

    Intentionally separate from log_event/events.jsonl: hook output is high
    frequency, low signal, and must never appear in the user-visible chat
    replay. Stored per-session so the Logs view stays clean while the data
    remains available for ad-hoc debugging.

    Never raises.
    """
    if not session_id or not line:
        return
    try:
        d = session_log_dir(session_id)
        with open(os.path.join(d, "hook_events.jsonl"), "a", encoding="utf-8") as f:
            f.write(line if line.endswith("\n") else line + "\n")
    except Exception as e:
        log.error("Failed to append hook_events.jsonl for %s: %s", session_id, e)


def read_events(session_id: str) -> list[dict]:
    """Return all structured events for a session, oldest first.

    Returns an empty list when the directory or the events file is missing,
    or when reading fails. Never raises.
    """
    if not session_id:
        return []
    path = os.path.join(LOG_BASE, f"{session_id}.klodTalk", "events.jsonl")
    if not os.path.isfile(path):
        return []
    events: list[dict] = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except Exception as e:
        log.error("Failed to read events.jsonl for %s: %s", session_id, e)
    return events


def purge(session_id: str) -> bool:
    """Delete the per-session log directory.

    NOT called from ``delete_session``. Provided for explicit administrative
    cleanup only. Returns True if the directory was removed (or absent),
    False on error.
    """
    if not session_id:
        return False
    import shutil
    path = os.path.join(LOG_BASE, f"{session_id}.klodTalk")
    if not os.path.isdir(path):
        return True
    try:
        shutil.rmtree(path, ignore_errors=False)
        return True
    except Exception as e:
        log.error("Failed to purge session log %s: %s", session_id, e)
        return False
