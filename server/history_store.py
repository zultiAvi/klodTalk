#!/usr/bin/env python3
"""Session history log read/write. Uses JSON Lines format."""

import json
import logging
import os
from datetime import datetime
from typing import Optional

log = logging.getLogger("klodtalk.history")


class HistoryStore:
    """Read and write session message history."""

    HISTORY_FILE = "session.jsonl"

    def _history_path(self, workspace: str) -> str:
        return os.path.join(workspace, ".klodTalk", "history", self.HISTORY_FILE)

    def append(self, session_id: str, workspace: str, role: str, content: str, model: str = ""):
        """Append a message to the session history."""
        try:
            history_dir = os.path.join(workspace, ".klodTalk", "history")
            os.makedirs(history_dir, exist_ok=True)
            path = self._history_path(workspace)
            entry = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "role": role,
                "content": content,
                "session_id": session_id,
            }
            if model:
                entry["model"] = model
            with open(path, "a") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            log.error("Failed to append history (session=%s): %s", session_id, e)

    def read_session(self, session_id: str, workspace: str) -> list[dict]:
        """Read all messages for a session from a workspace path."""
        path = self._history_path(workspace)
        if not os.path.isfile(path):
            return []
        messages = []
        try:
            with open(path) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        msg = json.loads(line)
                        messages.append(msg)
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            log.error("Failed to read history (session=%s): %s", session_id, e)
        return messages
