#!/usr/bin/env python3
"""Rebuild sessions.json from /tmp/klodtalk directory contents.

Scans /tmp/klodtalk/ subdirectories, inspects each workspace's git branch
and Docker container status, and writes a reconstructed sessions.json.
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, ".."))
STATE_DIR = os.path.join(BASE_DIR, ".klodTalk", "state")
SESSIONS_PATH = os.path.join(STATE_DIR, "sessions.json")
TEMP_BASE = os.path.join("/tmp", "klodtalk")
CONTAINER_PREFIX = "klodtalk_session_"
PROJECTS_PATH = os.path.join(BASE_DIR, "config", "projects.json")


def _load_projects() -> list:
    """Load and return the projects list from config/projects.json."""
    if not os.path.isfile(PROJECTS_PATH):
        print(f"Warning: {PROJECTS_PATH} not found, user assignment unavailable.",
              file=sys.stderr)
        return []
    try:
        with open(PROJECTS_PATH) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        print(f"Warning: failed to load {PROJECTS_PATH}: {exc}", file=sys.stderr)
        return []


def _get_user_for_project(projects: list, project_name: str) -> str:
    """Return the first allowed user for *project_name*, or ``'unknown'``."""
    for proj in projects:
        if proj.get("name") == project_name:
            users = proj.get("users", [])
            if users:
                return users[0]
            break
    return "unknown"


def _get_git_branch(workspace: str) -> str:
    """Return the current git branch for a workspace, or empty string.

    If *workspace* itself is not a git repo, searches one level of
    subdirectories for a git repo and returns its branch.
    """
    # Check workspace root first.
    if os.path.isdir(os.path.join(workspace, ".git")):
        return _git_branch_in(workspace)

    # No .git at root — search one level deep.
    try:
        entries = sorted(os.listdir(workspace))
    except OSError:
        return ""
    for entry in entries:
        subdir = os.path.join(workspace, entry)
        if os.path.isdir(subdir) and os.path.isdir(os.path.join(subdir, ".git")):
            return _git_branch_in(subdir)
    return ""


def _git_branch_in(directory: str) -> str:
    """Run ``git rev-parse`` in *directory* and return the branch name."""
    try:
        r = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=directory, capture_output=True, text=True, timeout=5,
        )
        if r.returncode == 0:
            return r.stdout.strip()
    except Exception:
        pass
    return ""


def _branch_to_project_name(branch: str) -> str:
    """Extract project name from branch name (format: <safe_name>_NNN)."""
    if not branch:
        return "unknown"
    # Strip trailing _NNN (1-3+ digits)
    m = re.match(r"^(.+)_\d{1,}$", branch)
    if m:
        return m.group(1)
    return branch


def _is_container_running(container_name: str) -> bool:
    """Check if a Docker container is running."""
    try:
        r = subprocess.run(
            ["docker", "inspect", "-f", "{{.State.Running}}", container_name],
            capture_output=True, text=True, timeout=5,
        )
        return r.returncode == 0 and r.stdout.strip().lower() == "true"
    except Exception:
        return False


def _dir_mtime_iso(path: str) -> str:
    """Return directory mtime as ISO 8601 with Z suffix."""
    mtime = os.path.getmtime(path)
    dt = datetime.fromtimestamp(mtime, tz=timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def discover_sessions() -> dict:
    """Scan /tmp/klodtalk/ and return a dict of reconstructed session records."""
    if not os.path.isdir(TEMP_BASE):
        print(f"Directory not found: {TEMP_BASE}")
        return {}

    projects = _load_projects()
    sessions = {}
    for entry in sorted(os.listdir(TEMP_BASE)):
        workspace = os.path.join(TEMP_BASE, entry)
        if not os.path.isdir(workspace):
            continue

        session_id = entry
        container_name = f"{CONTAINER_PREFIX}{session_id}"
        git_branch = _get_git_branch(workspace)
        project_name = _branch_to_project_name(git_branch)
        user_name = _get_user_for_project(projects, project_name)
        running = _is_container_running(container_name)
        status = "active" if running else "closed"
        created_at = _dir_mtime_iso(workspace)

        sessions[session_id] = {
            "session_id": session_id,
            "project_name": project_name,
            "user_name": user_name,
            "git_branch": git_branch,
            "workspace_path": workspace,
            "container_name": container_name,
            "status": status,
            "created_at": created_at,
            "closed_at": None if running else created_at,
            "project_folder": "",
            "docker_commit": True,
            "docker_socket": True,
        }

    return sessions


def print_summary(sessions: dict):
    """Print a human-readable summary of discovered sessions."""
    if not sessions:
        print("No sessions found.")
        return
    print(f"Found {len(sessions)} session(s):\n")
    print(f"  {'ID':<12} {'Project':<25} {'User':<15} {'Branch':<30} {'Status':<8}")
    print(f"  {'-'*12} {'-'*25} {'-'*15} {'-'*30} {'-'*8}")
    for sid, s in sessions.items():
        print(f"  {sid:<12} {s['project_name']:<25} {s['user_name']:<15} {s['git_branch']:<30} {s['status']:<8}")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Rebuild sessions.json from /tmp/klodtalk directory contents."
    )
    parser.add_argument(
        "--yes", "-y", action="store_true",
        help="Skip confirmation prompt and overwrite sessions.json.",
    )
    args = parser.parse_args()

    sessions = discover_sessions()
    print_summary(sessions)

    if not sessions:
        return

    print(f"Target: {SESSIONS_PATH}")

    if os.path.isfile(SESSIONS_PATH):
        print(f"WARNING: {SESSIONS_PATH} already exists and will be overwritten.")

    if not args.yes:
        answer = input("Write sessions.json? [y/N] ").strip().lower()
        if answer != "y":
            print("Aborted.")
            sys.exit(0)

    os.makedirs(STATE_DIR, exist_ok=True)
    with open(SESSIONS_PATH, "w") as f:
        json.dump(sessions, f, indent=2)
    print(f"Wrote {len(sessions)} session(s) to {SESSIONS_PATH}")


if __name__ == "__main__":
    main()
