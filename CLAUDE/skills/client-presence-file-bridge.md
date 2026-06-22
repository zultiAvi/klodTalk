---
skill_name: client-presence-file-bridge
triggers:
  - A user is actively watching a session from the web client but still receives mobile push notifications
  - Wiring CLAUDE_CLIENT_PRESENCE_FILE so the CLI suppresses pushes while a WebSocket client is connected
  - Deciding where to write/delete a per-user presence file in server.py's connect/disconnect lifecycle
summary: "Documents CLAUDE_CLIENT_PRESENCE_FILE (CLI v2.1.181): a non-empty file suppresses mobile push, deleting/truncating it resumes; maps the KlodTalk wiring onto server.py's connected_clients lifecycle and run_agent.py's _claude_env forwarding (core-server edit out of nightly scope)."
---

# Skill: Client Presence File Bridge

## Quick Reference
- Env var: `CLAUDE_CLIENT_PRESENCE_FILE` (Claude Code CLI **v2.1.181+**).
- Contract: file exists **and is non-empty** → mobile push **suppressed**; **delete or truncate** → push **resumes**.
- KlodTalk hook: `server.py` already tracks `connected_clients: dict[str, WebSocketServerProtocol]`.
- Recommended path: `/tmp/klodtalk_presence_<username>.txt` (per-user, `/tmp` so it auto-clears on reboot).
- The actual `server.py` wiring is **OUT OF SCOPE for the nightly coder** (core-server code) — this skill is the doc deliverable so the human dev can wire it.

## When to Use
Apply when a user watching a live session in the **web** client is still getting **mobile** pings for every update. KlodTalk ships both a web client and an Android app; presence-file suppression silences the phone while the web session is active.

## Instructions
The integration points below were verified against the current tree (function names, not line numbers — these drift):

1. **Write on connect.** In `server.py`, `async def handle_client(...)` handles the `hello` message and on successful auth runs `connected_clients[client_name] = websocket`. Alongside that line, write a non-empty presence file:
   ```python
   PRESENCE = f"/tmp/klodtalk_presence_{client_name}.txt"
   with open(PRESENCE, "w") as f:
       f.write("connected\n")   # any non-empty content suppresses push
   ```
2. **Delete on disconnect.** Still in `handle_client`, the close path does `del connected_clients[client_name]`. Remove the presence file there:
   ```python
   try: os.remove(PRESENCE)
   except FileNotFoundError: pass
   ```
3. **Forward into the container.** `run_agent.py` builds the CLI subprocess env in `_claude_env()` (which already forwards `CLAUDE_*` vars like `CLAUDE_CODE_CONTEXT_COMPACTION`). Add `env["CLAUDE_CLIENT_PRESENCE_FILE"] = PRESENCE` there so the in-container CLI reads the same file.

Caveat: this is a real-file presence signal, not a `permissions:`/deny rule — those are NO-OPs in KlodTalk and would not gate notifications.

## Cross-References
- `required-minimum-version-pin.md` — where the CLI version floor (which gates this env var) is tracked.
- `compaction-api-opt-in.md` / `plugin-dir-dispatch.md` — the `_claude_env()` env-var forwarding pattern this mirrors.

## Source Attribution
- Claude Code CLI **v2.1.181** (official Anthropic): https://github.com/anthropics/claude-code/releases — introduced `CLAUDE_CLIENT_PRESENCE_FILE`.
