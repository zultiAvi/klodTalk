#!/usr/bin/env python3
"""Git utility functions for KlodTalk pipeline scripts."""

import subprocess
import os


def git_run(args: list[str], cwd: str = "/workspace") -> subprocess.CompletedProcess:
    return subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True)


def get_current_branch(cwd: str = "/workspace") -> str:
    r = git_run(["rev-parse", "--abbrev-ref", "HEAD"], cwd)
    return r.stdout.strip() if r.returncode == 0 else "(unknown)"


def configure_identity(name: str = "Claude Bot", email: str = "claude@bot.local", cwd: str = "/workspace"):
    git_run(["config", "user.name", name], cwd)
    git_run(["config", "user.email", email], cwd)


def commit_all(message: str, cwd: str = "/workspace") -> bool:
    git_run(["add", "-A"], cwd)
    r = git_run(["commit", "-m", message], cwd)
    return r.returncode == 0


def has_repo(path: str = "/workspace") -> bool:
    r = subprocess.run(
        ["git", "-C", path, "rev-parse", "--git-dir"],
        capture_output=True
    )
    return r.returncode == 0


def get_changed_files(base_branch: str, current_branch: str, cwd: str = "/workspace") -> list[str]:
    r = git_run(["diff", "--name-only", f"origin/{base_branch}...{current_branch}"], cwd)
    if r.returncode != 0:
        return []
    return [f.strip() for f in r.stdout.splitlines() if f.strip()]


def create_session_worktree(session_id: str, base_branch: str, cwd: str = "/workspace") -> str:
    """Create a per-session git worktree on its own branch.

    Path convention: <cwd>/.worktrees/<session_id>; branch: session/<session_id>.
    Idempotent: reuses an existing path/branch instead of failing. Returns the
    worktree path on success; raises RuntimeError on failure.
    NOTE: wiring this into session_manager.py is a separate manual follow-up.
    """
    if not session_id or not base_branch:
        raise ValueError("session_id and base_branch are required")
    wt_path = os.path.join(cwd, ".worktrees", session_id)
    branch = f"session/{session_id}"
    if os.path.exists(wt_path):
        return wt_path
    os.makedirs(os.path.join(cwd, ".worktrees"), exist_ok=True)
    branch_exists = git_run(["show-ref", "--verify", "--quiet", f"refs/heads/{branch}"], cwd)
    if branch_exists.returncode == 0:
        r = git_run(["worktree", "add", wt_path, branch], cwd)
    else:
        r = git_run(["worktree", "add", wt_path, "-b", branch, f"origin/{base_branch}"], cwd)
    if r.returncode != 0:
        raise RuntimeError(f"git worktree add failed: {r.stderr.strip()}")
    return wt_path


def remove_session_worktree(session_id: str, cwd: str = "/workspace") -> None:
    """Remove a per-session git worktree (force) and prune stale metadata."""
    if not session_id:
        raise ValueError("session_id is required")
    wt_path = os.path.join(cwd, ".worktrees", session_id)
    if os.path.exists(wt_path):
        git_run(["worktree", "remove", "--force", wt_path], cwd)
    git_run(["worktree", "prune"], cwd)
