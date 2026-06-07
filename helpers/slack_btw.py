#!/usr/bin/env python3
"""Send a BTW side-channel message to a running KlodTalk agent session.

Operator tool — run manually from a terminal, a cron job, or a Slack slash-command
shim. It connects to the KlodTalk WebSocket server, authenticates, then fires a
single `btw` message into a running session and exits. It changes nothing on the
server side and uses only the existing client protocol.

Usage:
    python slack_btw.py "your message here"

Required env vars:
    KLODTALK_WS_URL       WebSocket URL, e.g. ws://localhost:8765
    KLODTALK_USER         KlodTalk username (matches config/users.json)
    KLODTALK_PASS_HASH    SHA-256 hex of the password (users.json format)
    KLODTALK_SESSION_ID   Session ID of the running agent to message

Protocol (verified against server/server.py):
    -> {"type": "hello", "name": <user>, "password_hash": <hash>}
    <- {"type": "projects", "projects": [...]}     (consumed and discarded)
    -> {"type": "btw", "session_id": <id>, "content": <message>}
    <- {"type": "ack", ...}     on success (handle_btw, server.py:1619)
    <- {"type": "error", "message": ...}     on rejection (handle_btw,
       server.py:1508/1512/1516/1519/1522: empty content, session not found,
       system session, user not authorized, session not running)

Exit codes:
    0  the server accepted the BTW (it replied with `ack`, or did not reply
       with an `error` within the recv window)
    1  bad usage, or the server rejected the BTW with an `error` reply
"""
import asyncio
import json
import os
import sys

import websockets


async def send_btw(message: str) -> None:
    url = os.environ["KLODTALK_WS_URL"]
    user = os.environ["KLODTALK_USER"]
    pass_hash = os.environ["KLODTALK_PASS_HASH"]
    session_id = os.environ["KLODTALK_SESSION_ID"]

    async with websockets.connect(url) as ws:
        await ws.send(json.dumps(
            {"type": "hello", "name": user, "password_hash": pass_hash}
        ))
        # Consume the `projects` response the server sends after a valid hello.
        await ws.recv()
        await ws.send(json.dumps(
            {"type": "btw", "session_id": session_id, "content": message}
        ))

        # handle_btw always replies: `ack` on success, `error` on rejection
        # (bad session id, unauthorized user, session not running, etc.).
        # Read that reply and fail loudly on an error so the caller (operator,
        # cron job, Slack shim) does not silently believe a rejected message
        # was delivered. A short timeout treats "no reply" as success to avoid
        # hanging if the server's reply is delayed or dropped.
        try:
            reply = await asyncio.wait_for(ws.recv(), timeout=10.0)
        except asyncio.TimeoutError:
            return
        try:
            parsed = json.loads(reply)
        except (json.JSONDecodeError, TypeError):
            return
        if parsed.get("type") == "error":
            print(
                "BTW rejected by server: "
                + parsed.get("message", parsed.get("reason", "unknown error")),
                file=sys.stderr,
            )
            sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: slack_btw.py <message>", file=sys.stderr)
        sys.exit(1)
    asyncio.run(send_btw(sys.argv[1]))
