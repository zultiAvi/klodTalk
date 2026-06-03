#!/usr/bin/env python3
"""Idempotent dedupe-and-heal utility for per-session ``events.jsonl`` files.

Background
----------
Prior to commit 948323d, the server's ``_broadcast_to_session_users`` helper
unconditionally mirrored every broadcast payload into ``events.jsonl`` while
the individual role handlers had already called ``session_log.log_event``
with the same body. The result is that every user-visible message in the
affected sessions is persisted twice. Commit 948323d made the mirror opt-in
(``log_to_session=False`` by default), which stops new duplicates from being
written — but it does not rewrite history. Reconnects therefore continue to
surface every pre-fix message twice in the client.

This tool reads each session's ``events.jsonl`` and rewrites it with
duplicate rows removed. It is intentionally conservative:

* First occurrence of a given ``(timestamp, role, content, extra.type)`` key
  wins; later occurrences are dropped.
* ``role == "hook"`` rows are NEVER considered duplicates — hook entries are
  intentionally bursty and may legitimately repeat. They are passed through
  untouched.
* The original file is backed up to ``events.jsonl.bak-<utc-iso>`` before
  the rewrite. The rewrite itself is atomic: write a sibling ``.tmp`` file
  and ``os.replace`` over the original.
* Default mode is ``--dry-run``. An explicit ``--apply`` flag is required to
  modify any file on disk. This is deliberate: the migration is destructive
  in the sense that it overwrites historical files, and the operator must
  confirm.

Usage
-----
::

    python -m server.tools.dedupe_events_jsonl              # dry run
    python -m server.tools.dedupe_events_jsonl --apply      # rewrite in place
    python -m server.tools.dedupe_events_jsonl --base /custom/logs --apply

Output is one summary line per file: ``<sid> kept=<N> dropped=<M>``.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import sys
from datetime import datetime
from typing import Iterable, Optional, Tuple

# Allow ``python -m server.tools.dedupe_events_jsonl`` even when the caller
# does not have ``server/`` on sys.path: insert the parent of this file's
# directory so ``import session_log`` resolves to ``server/session_log.py``.
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_SERVER_DIR = os.path.dirname(_THIS_DIR)
if _SERVER_DIR not in sys.path:
    sys.path.insert(0, _SERVER_DIR)

import session_log  # noqa: E402  (sys.path adjusted above)


DedupeKey = Tuple[str, str, str, str]


def _extra_type(entry: dict) -> str:
    """Return the ``extra.type`` field as a string, or '' when absent."""
    extra = entry.get("extra")
    if isinstance(extra, dict):
        t = extra.get("type")
        if isinstance(t, str):
            return t
    return ""


def _dedupe_key(entry: dict) -> DedupeKey:
    """Compute the dedupe key for a single events.jsonl entry."""
    return (
        str(entry.get("timestamp", "")),
        str(entry.get("role", "")),
        str(entry.get("content", "")),
        _extra_type(entry),
    )


def dedupe_lines(lines: Iterable[str]) -> Tuple[list[str], int, int]:
    """Return ``(kept_lines, kept_count, dropped_count)`` for the given lines.

    Lines that fail JSON parsing are kept verbatim (we never discard data we
    cannot understand). ``role == "hook"`` rows are also kept unconditionally.
    """
    seen: set[DedupeKey] = set()
    kept: list[str] = []
    dropped = 0
    for raw in lines:
        stripped = raw.strip()
        if not stripped:
            # Preserve blank lines? No — blank lines are noise, drop silently
            # without counting them as duplicates.
            continue
        try:
            entry = json.loads(stripped)
        except json.JSONDecodeError:
            # Unparseable: keep verbatim so the operator can inspect later.
            kept.append(stripped + "\n")
            continue
        if not isinstance(entry, dict):
            kept.append(stripped + "\n")
            continue
        if entry.get("role") == "hook":
            kept.append(stripped + "\n")
            continue
        key = _dedupe_key(entry)
        if key in seen:
            dropped += 1
            continue
        seen.add(key)
        kept.append(stripped + "\n")
    return kept, len(kept), dropped


def _resolve_base(override: Optional[str]) -> str:
    """Resolve the log base directory, mirroring ``session_log._resolve_log_base``."""
    if override:
        return override
    # session_log.LOG_BASE is computed at import time via _resolve_log_base().
    return session_log.LOG_BASE


def _iter_event_files(base: str) -> list[str]:
    """Return sorted paths to every ``<sid>.klodTalk/events.jsonl`` under ``base``."""
    pattern = os.path.join(base, "*.klodTalk", "events.jsonl")
    return sorted(glob.glob(pattern))


def _session_id_from_path(path: str) -> str:
    """Extract ``<sid>`` from ``.../logs/<sid>.klodTalk/events.jsonl``."""
    parent = os.path.basename(os.path.dirname(path))
    if parent.endswith(".klodTalk"):
        return parent[: -len(".klodTalk")]
    return parent


def _backup_path(events_path: str) -> str:
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    return f"{events_path}.bak-{ts}"


def process_file(events_path: str, *, apply: bool) -> Tuple[int, int]:
    """Dedupe a single events.jsonl. Returns ``(kept, dropped)``.

    When ``apply`` is False, no changes are made to disk.
    """
    with open(events_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    kept_lines, kept, dropped = dedupe_lines(lines)
    if apply and dropped > 0:
        backup = _backup_path(events_path)
        # 1. Back up the original. If backup already exists (same second twice),
        # append a counter rather than overwrite.
        if os.path.exists(backup):
            i = 1
            while os.path.exists(f"{backup}.{i}"):
                i += 1
            backup = f"{backup}.{i}"
        os.replace(events_path, backup)
        # 2. Write to .tmp then atomic rename into place.
        tmp_path = events_path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.writelines(kept_lines)
        os.replace(tmp_path, events_path)
    return kept, dropped


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="dedupe_events_jsonl",
        description="Dedupe duplicate rows in per-session events.jsonl files.",
    )
    parser.add_argument(
        "--base",
        default=None,
        help="Override the log base directory (defaults to session_log.LOG_BASE).",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually rewrite files on disk. Without this flag the run is a dry-run.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Force dry-run (default). Present for explicitness; mutually exclusive with --apply.",
    )
    args = parser.parse_args(argv)

    if args.apply and args.dry_run:
        parser.error("--apply and --dry-run are mutually exclusive")
    apply = bool(args.apply)
    base = _resolve_base(args.base)
    if not os.path.isdir(base):
        print(f"[dedupe] log base not found: {base}", file=sys.stderr)
        return 2

    files = _iter_event_files(base)
    if not files:
        print(f"[dedupe] no events.jsonl files under {base}")
        return 0

    mode = "APPLY" if apply else "DRY-RUN"
    print(f"[dedupe] mode={mode} base={base} files={len(files)}")
    total_kept = 0
    total_dropped = 0
    for path in files:
        sid = _session_id_from_path(path)
        try:
            kept, dropped = process_file(path, apply=apply)
        except Exception as e:
            print(f"{sid} ERROR {e}")
            continue
        total_kept += kept
        total_dropped += dropped
        print(f"{sid} kept={kept} dropped={dropped}")
    print(f"[dedupe] total kept={total_kept} dropped={total_dropped} mode={mode}")
    if not apply and total_dropped > 0:
        print("[dedupe] re-run with --apply to rewrite the files above.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
