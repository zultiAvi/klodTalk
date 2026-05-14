---
skill_name: broadcast-message-file-handler
triggers:
  - Adding a new `*_message.txt` file produced by a role/orchestrator
  - Wiring a team output to the web/Android clients
  - Diagnosing why an out_messages/<file> never reaches the client
summary: New `out_messages/<role>_message.txt` files need BOTH an `_OUT_MESSAGE_EXCLUDED` entry AND a dedicated handler block in `server.py:watch_out_messages` — exclusion alone makes the file silent.
---

# Skill: Add a Dedicated Handler for Each Broadcast Message File

## Quick Reference
- File: `server/server.py` — function `watch_out_messages` (around lines 800-1300).
- Pattern: each named broadcast file (`planner_message.txt`, `coder_message.txt`, `idea_message.txt`, `debugger_message.txt`, ...) has its own explicit `if os.path.isfile(...)` block that reads, removes, logs, and broadcasts.
- `_OUT_MESSAGE_EXCLUDED` (top of `server.py`, ~line 69) lists files that the generic catch-all skips. Naming a file there WITHOUT also adding a handler block means the server reads nothing and broadcasts nothing — the role's output is silent end-to-end.
- The `debugger_message.txt` handler was missing for months before the `interactive-debug` team work caught it; the team's existing `_OUT_MESSAGE_EXCLUDED` entry created a false sense that the wiring was complete.

## When to Use
When introducing any new `out_messages/<something>_message.txt` file, or when diagnosing why a role's message file is written but never appears in the client chat.

## The Pattern (copy this template)

```python
# <role>_message
<role>_msg_path = os.path.join(message_folder, "<role>_message.txt")
if os.path.isfile(<role>_msg_path):
    try:
        content = open(<role>_msg_path).read()
        os.remove(<role>_msg_path)
    except Exception as e:
        log.error("Error reading <role>_message for session '%s': %s", session_id, e)
        content = None
    if content:
        _models = _session_team_models.get(session_id, {})
        _team = _session_team_override.get(session_id, "")
        if not _team:
            _p = get_project_record(session.project_name)
            _team = _p.get("team", "") if _p else ""
        history_store.append(session_id, workspace, "<role>", content, model=_models.get("<role>", ""))
        try:
            session_log.log_event(session_id, "<role>", content, model=_models.get("<role>", ""))
        except Exception:
            pass
        await _broadcast_to_session_users(session_id, {
            "type": "new_message",
            "session_id": session_id,
            "project": session.project_name,
            "role": "<role>",
            "content": content,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "model": _models.get("<role>", ""),
            "team": _team,
        })
```

Place the block immediately after the closest existing sibling (e.g. coder_message comes after planner_message). The `coder_message.txt` block is the canonical template — copy it verbatim, change the filename, log key, and role string.

## Checklist When Adding a New Broadcast File
1. Add the filename to `_OUT_MESSAGE_EXCLUDED` in `server.py`.
2. Add a dedicated handler block (template above) in `watch_out_messages`.
3. If the role string is brand-new (not yet in `clients/web/index.html:TEAM_ROLES_SET` and `clients/android/.../HistoryScreen.kt:TEAM_ROLES`), add it there too — the three-place edit instinct.
4. If you can reuse an existing role (e.g. `debugger`, `planner`), the three-place client edit is zero — strongly prefer reuse.
