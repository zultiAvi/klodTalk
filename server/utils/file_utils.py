#!/usr/bin/env python3
"""File path constants and I/O helpers for KlodTalk pipeline scripts."""

import os


WORKSPACE = "/workspace"
KLODTALK_DIR = os.path.join(WORKSPACE, ".klodTalk")
IN_MESSAGES_DIR = os.path.join(KLODTALK_DIR, "in_messages")
OUT_MESSAGES_DIR = os.path.join(KLODTALK_DIR, "out_messages")
PR_MESSAGES_DIR = os.path.join(KLODTALK_DIR, "pr_messages")
TEAM_DIR = os.path.join(KLODTALK_DIR, "team", "current")

IN_FILE = os.path.join(IN_MESSAGES_DIR, "in_message.txt")
OUT_FILE = os.path.join(OUT_MESSAGES_DIR, "out_message.txt")
CONFIRM_FILE = os.path.join(OUT_MESSAGES_DIR, "confirm_message.txt")
PROGRESS_FILE = os.path.join(OUT_MESSAGES_DIR, "progress_message.txt")
PR_FILE = os.path.join(PR_MESSAGES_DIR, "pr_message.txt")
CHANGED_FILES = os.path.join(KLODTALK_DIR, "changed_files.txt")


def read_file(path: str) -> str:
    if not os.path.isfile(path):
        return ""
    with open(path) as f:
        return f.read()


def write_file(path: str, content: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)


def read_request() -> str:
    return read_file(IN_FILE)


def write_output(content: str):
    write_file(OUT_FILE, content)


def write_progress(content: str):
    write_file(PROGRESS_FILE, content)


def read_plan() -> str:
    return read_file(os.path.join(TEAM_DIR, "plan.md"))


def write_plan(content: str):
    write_file(os.path.join(TEAM_DIR, "plan.md"), content)


def read_coder_output() -> str:
    return read_file(os.path.join(TEAM_DIR, "coder_output.txt"))


def write_coder_output(content: str):
    write_file(os.path.join(TEAM_DIR, "coder_output.txt"), content)


def read_reviewer_output() -> str:
    return read_file(os.path.join(TEAM_DIR, "reviewer_output.txt"))


def write_reviewer_output(content: str):
    write_file(os.path.join(TEAM_DIR, "reviewer_output.txt"), content)
