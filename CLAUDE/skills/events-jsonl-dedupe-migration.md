---
skill_name: events-jsonl-dedupe-migration
triggers:
  - Fixing a write-path bug that has already polluted `events.jsonl` rows on disk
  - User reports duplicated/corrupt messages persisting after a server restart
  - Designing any one-shot healing migration over per-session JSONL log files
summary: A forward-only write-path fix does NOT heal historical rows in `<log_base>/<sid>.klodTalk/events.jsonl`; ship a `server/tools/dedupe_events_jsonl.py`-style migration (dry-run default, .bak-<utc-iso> backup, atomic .tmp+os.replace, hook rows passed through).
---

# Skill: events.jsonl Healing Migration Pattern

## Quick Reference
- Reference tool: `server/tools/dedupe_events_jsonl.py`.
- Dry-run is the DEFAULT; live writes require an explicit `--apply` flag.
- Per-file flow: read all rows -> build dedupe key -> write to `events.jsonl.tmp` -> rename original to `events.jsonl.bak-<utc-iso>` -> `os.replace(tmp, events.jsonl)`.
- Always PRESERVE `role == "hook"` rows verbatim (intentionally bursty; not user-visible per `broadcast-log-event-single-write`).
- Resolve `log_base` via `session_log.LOG_BASE` so `KLODTALK_LOG_BASE` env override and `server_config.yaml` precedence are honoured.

## When to Use
- Any write-path bug that has been live long enough to have written bad rows to disk. The KlodTalk pattern: `_broadcast_to_session_users(..., log_to_session=True)` paired with a peer `session_log.log_event(...)` for the same content. Once the bug is patched at the source, every previously-affected `events.jsonl` still replays on reconnect via `_session_to_dict` -> `read_events` -> client.
- The same recipe applies to any future per-session JSONL store under `<log_base>/<sid>.klodTalk/` (e.g., per-tool logs).

## Producer Checklist
1. Source fix lands FIRST. The migration assumes the write path no longer adds duplicates.
2. Dedupe key includes enough fields to be content-precise but not over-broad. For `events.jsonl`, the canonical tuple is `(timestamp, role, content, extra.get("type"))`. First occurrence wins.
3. Hook rows (`role == "hook"`) pass through untouched — they may legitimately repeat and the client never sees them anyway.
4. Backup naming must collide-safely: `events.jsonl.bak-<utc-iso>` and on collision append `.1`, `.2`, ... Same-second reruns must not silently overwrite a prior backup.
5. Atomic replacement: write to `events.jsonl.tmp`, then `os.replace` over the original. Never write in place.
6. Per-file summary line: `<sid> kept=N dropped=M`. Aggregate at the end.

## Operator Flow
```
# Stop the server first (open file handles + concurrent appends = bad).
# Inspect what would change:
python3 -m server.tools.dedupe_events_jsonl
# Apply for real once the dry-run output looks right:
python3 -m server.tools.dedupe_events_jsonl --apply
# Restart the server. Reconnect a client and confirm each message renders once.
```

## What NOT to Do
- Do not edit `events.jsonl` in place — a crash mid-write leaves a half-rewritten file.
- Do not skip the backup step even on a "trivial" run — operators expect rollback to exist.
- Do not dedupe across sessions — keys are file-local.
- Do not assume the migration was run — keep the source-side regression test (`test_broadcast_does_not_double_write_when_log_to_session_false`, etc.) authoritative.

## Related
- `broadcast-log-event-single-write.md` — the write-path contract this migration heals against.
- `selective-git-staging-nightly.md` — companion discipline for any code change that touches gitignored tracked files like `.klodTalk/instincts.md`.

## Source
Direct outcome of KlodTalk commit b701a77 (2026-06-03), which fixed message duplication that persisted across server restarts despite the forward-only fix in 948323d.
