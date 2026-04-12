#!/usr/bin/env python3
"""History logging utilities for pipeline scripts."""

import json
import os
from datetime import datetime, timezone


def append_history(workspace: str, session_id: str, role: str, content: str):
    """Append a message to the session history JSONL file."""
    history_dir = os.path.join(workspace, ".klodTalk", "history")
    os.makedirs(history_dir, exist_ok=True)
    path = os.path.join(history_dir, "session.jsonl")
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "role": role,
        "content": content,
        "session_id": session_id,
    }
    with open(path, "a") as f:
        f.write(json.dumps(entry) + "\n")
