---
skill_name: slack-btw-bridge
triggers:
  - Injecting a BTW side-channel message into a running KlodTalk agent from outside the Web/Android clients
  - Wiring a Slack slash command to fire a KlodTalk BTW message
  - Sending BTW context from a cron job, CI webhook, or another script
summary: "helpers/slack_btw.py connects to the KlodTalk WebSocket, sends hello then a btw message into a running session; wire it to a Slack slash command via a minimal separate webhook endpoint (NOT the KlodTalk server) that validates SLACK_SIGNING_SECRET before shelling out."
---

# Skill: Slack BTW Bridge

## Quick Reference
- Helper: `helpers/slack_btw.py` — stdlib + `websockets`, ~40 lines, no server changes.
- Invocation: `python helpers/slack_btw.py "message"`.
- Server contract (verified): `hello {name, password_hash}` → `projects` response → `btw {session_id, content}`; handled by `server/server.py` `handle_btw` (dispatch under `elif msg_type == "btw"`).
- The Slack shim is a **separate** one-file webhook endpoint, NOT part of the KlodTalk server.
- Security: the shim MUST validate `SLACK_SIGNING_SECRET` before acting on any payload.

## When to Use
BTW mode is one of KlodTalk's most powerful features but is otherwise reachable only from the Web/Android clients. Use this bridge to fire a BTW message from any device with Slack, a terminal, a cron job, or a CI webhook into a running agent session.

## Instructions

### Required Env Vars
Set these before running `slack_btw.py`:
- `KLODTALK_WS_URL` — e.g. `ws://localhost:8765` (or `wss://` when TLS is on).
- `KLODTALK_USER` — KlodTalk username (must match `config/users.json` and be in the session's allowed users).
- `KLODTALK_PASS_HASH` — SHA-256 hex of the password (same format `helpers/add_user.py` writes to `users.json`).
- `KLODTALK_SESSION_ID` — the session id of the running agent to message.

### Invocation
```bash
export KLODTALK_WS_URL=ws://localhost:8765
export KLODTALK_USER=zulti
export KLODTALK_PASS_HASH=<sha256-hex>
export KLODTALK_SESSION_ID=<running-session-id>
python helpers/slack_btw.py "remember to keep the rear-camera gate at conf>=0.90"
```
The server rejects the BTW if the session is not running, the user is not in `session.users`, the session is a system session, or the content is empty. The helper reads the server's reply: it exits **1** and prints the server's error message to stderr on any such rejection, and exits **0** only when the BTW was accepted (server `ack`). A Slack shim can therefore rely on the exit code to report delivery success or failure back to the user.

### Wiring a Slack Slash Command
1. Create a Slack app and add a slash command, e.g. `/klodtalk`.
2. Point its **Request URL** at a minimal webhook endpoint **you run separately** (one-file Flask/FastAPI), NOT at the KlodTalk WebSocket server.
3. The endpoint reads the Slack form payload, extracts the message text, and shells out to `slack_btw.py` (with the env vars above set in the endpoint's environment).

Minimal sketch (separate process):
```python
# slack_shim.py — NOT part of the KlodTalk server
import hashlib, hmac, os, subprocess, time
from flask import Flask, request, abort

app = Flask(__name__)
SIGNING_SECRET = os.environ["SLACK_SIGNING_SECRET"].encode()

def verify(req):
    ts = req.headers.get("X-Slack-Request-Timestamp", "")
    if abs(time.time() - int(ts or 0)) > 60 * 5:
        abort(400)  # stale -> replay attack
    basestring = f"v0:{ts}:{req.get_data(as_text=True)}".encode()
    expected = "v0=" + hmac.new(SIGNING_SECRET, basestring, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, req.headers.get("X-Slack-Signature", "")):
        abort(401)

@app.route("/klodtalk", methods=["POST"])
def klodtalk():
    verify(request)  # MUST run before anything else
    text = request.form.get("text", "")
    subprocess.run(["python", "helpers/slack_btw.py", text], check=False)
    return "BTW sent.", 200
```

### Security Note
Always validate `SLACK_SIGNING_SECRET` (HMAC over the raw body + timestamp, with a freshness window) **before** acting on a Slack payload. Without it, anyone who learns the Request URL can inject BTW messages into running agents. Keep the shim and its env vars off the public KlodTalk surface.

## Cross-References
- `server/server.py` `handle_btw` — the server-side BTW contract this script targets.
- KlodTalk message protocol (`CLAUDE.md`) — `hello` / `projects` / `btw` field shapes.
- `helpers/add_user.py` — how `password_hash` values are generated for `users.json`.

## Source Attribution
- `erkandogan/oh-my-team` (community): https://github.com/erkandogan/oh-my-team — multi-agent orchestration with Slack/Telegram remote control; stars not confirmed; active June 2026.
