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
