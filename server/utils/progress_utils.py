#!/usr/bin/env python3
"""Progress message utilities for team pipeline scripts."""

import os


def write_progress(message: str, workspace: str = "/workspace"):
    """Write a progress message for the server to broadcast."""
    progress_path = os.path.join(workspace, ".klodTalk", "out_messages", "progress_message.txt")
    os.makedirs(os.path.dirname(progress_path), exist_ok=True)
    with open(progress_path, "w") as f:
        f.write(message)


def progress_set(current: int, total: int, label: str, workspace: str = "/workspace"):
    """Write a step-progress message."""
    write_progress(f"[{current}/{total}] {label}", workspace)
