---
skill_name: session-data-path-propagation
triggers:
  - Changing `server.session_data_path` in `config/server_config.yaml`
  - Modifying `TEMP_BASE`/`LOG_BASE` resolution in `session_manager.py`/`session_log.py`
  - Diagnosing why sessions still use `/tmp/klodTalk` after a config change
  - Touching `create_system_session` or persisted records in `.klodTalk/state/sessions.json`
summary: `session_data_path` is read once at import; persisted session records (especially `system_routine`) bake `workspace_path` and must be revalidated against current `TEMP_BASE` on startup or they stick to the old path forever.
---

# Skill: session_data_path Propagation and Stale Persisted Paths

## Quick Reference
- Config: `server.session_data_path` in `config/server_config.yaml` (default fallback `/tmp/klodTalk`).
- `TEMP_BASE` (server/session_manager.py ~line 56) and `LOG_BASE` (server/session_log.py ~line 61) read it ONCE at module import. A fresh server restart picks up changes.
- BUT: persisted records in `.klodTalk/state/sessions.json` bake the absolute `workspace_path` per session. Changing `session_data_path` does NOT migrate existing records.
- Only the system session (`system_routine`, fixed ID) is auto-revalidated on every startup via `create_system_session`. Regular user sessions are not migrated — they stay on the old path until closed and recreated.

## When to Use
When a user reports "I changed `session_data_path` but the routine / a session still uses `/tmp/...`", when modifying `create_system_session`, or when adding new persisted session-state fields that include absolute paths derived from `TEMP_BASE`/`LOG_BASE`.

## How `create_system_session` Handles Stale Records
On startup, if `_sessions[SYSTEM_SESSION_ID]` already exists:
1. Check `workspace_path` exists on disk AND its parent equals current `TEMP_BASE`.
2. If either fails: log a warning, `stop_container()` to free the docker name, drop the entry from `_sessions`, fall through to recreate.
3. Otherwise: just refresh the users list (existing behavior).

If you add new path-bearing fields to a persisted session record, mirror this validate-or-rebuild pattern instead of trusting the stored value.

## Related
- `server/session_manager.py` — `TEMP_BASE`, `_start_session_container`, `create_system_session`.
- `server/session_log.py` — `LOG_BASE`.
- `server/server.py` ~line 3243-3260 — system-session startup wiring; calls `reopen_session` then `create_system_session`.
- `.klodTalk/state/sessions.json` — persisted records.
