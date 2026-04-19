#!/usr/bin/env python3
"""KlodTalk WebSocket server — session-based rewrite.

New protocol supports per-session Docker containers, persistent history,
per-user unread markers, and explicit send-mode buttons (no trigger phrases).
"""

import asyncio
import hmac
import json
import logging
import os
import re
import socket
import shutil
import ssl as ssl_module
import subprocess
import sys
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path

import websockets
import yaml

from session_manager import HOST_GID, HOST_UID, SessionManager, _normalize_external_paths, get_results_folder
from history_store import HistoryStore
from unread_state import UnreadState
from token_store import TokenStore
from jsonl_reader import (
    discover_archived_sessions, read_session_jsonl, read_subagent_jsonl,
    aggregate_session_tokens,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("klodtalk")


class _SuppressHandshakeNoise(logging.Filter):
    """Drop ERROR-level 'opening handshake failed' records from the websockets
    library.  These fire whenever a non-WebSocket client (e.g. an RTSP scanner)
    hits the port — they are harmless and just clutter the log."""

    def filter(self, record: logging.LogRecord) -> bool:
        return not (record.levelno >= logging.ERROR and "opening handshake failed" in record.getMessage())


logging.getLogger("websockets.server").addFilter(_SuppressHandshakeNoise())

BASE_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
CONFIG_PATH = os.path.join(BASE_DIR, "config", "server_config.yaml")
USERS_PATH = os.path.join(BASE_DIR, "config", "users.json")
PROJECTS_PATH = os.path.join(BASE_DIR, "config", "projects.json")
TEAMS_DIR = os.path.join(BASE_DIR, "teams", "teams")
DOCKERFILE_PATH = os.path.join(BASE_DIR, "server", "Dockerfile.agent")

POLL_INTERVAL_SECONDS = 5
CLAUDE_SESSION_CHECK_SECONDS = 3600
DOCKER_IMAGE_NAME = "klodtalk-agent"
KLODTALK_DIR = ".klodTalk"
MAX_REVIEW_ITERATIONS = 3
SYSTEM_SESSION_ID = "system_routine"  # Fixed ID for the system session
_OUT_MESSAGE_EXCLUDED = {"confirm_message.txt", "progress_message.txt", "planner_message.txt", "coder_message.txt", "idea_message.txt", "idea_review_message.txt", "final_plan_message.txt", "idea_history_message.txt", "btw_response.txt"}

# On Windows, npm global installs create `claude.cmd`, not a bare `claude` binary.
_CLAUDE_CMD = "claude.cmd" if sys.platform == "win32" else "claude"

# HOST_UID / HOST_GID from session_manager (None on Windows — no os.getuid/getgid there)

# username → websocket
connected_clients: dict[str, websockets.WebSocketServerProtocol] = {}
# session_id → username (who triggered current run)
session_triggered_by: dict[str, str] = {}
# session_id → review iteration count
review_iterations: dict[str, int] = {}
# session_ids currently executing
running_sessions: set[str] = set()
# session_id -> asyncio.subprocess.Process (the docker exec process)
session_processes: dict[str, asyncio.subprocess.Process] = {}

# session_ids that have received a confirm (read-back) response and are waiting for the next message
pending_confirm: set[str] = set()
# session_id → {"planner": "Sonnet", "coder": "Opus", "review": "Haiku"}
_session_team_models: dict[str, dict] = {}
# session_id → team name override (from client per-message selection)
_session_team_override: dict[str, str] = {}
# session_id → set of file paths that have been reverted (for targeted commit)
_session_reverted_files: dict[str, set[str]] = {}


def _short_model_name(model_id: str) -> str:
    """Extract short display name from model ID. e.g. 'claude-sonnet-4-6' → 'Sonnet'"""
    if not model_id:
        return ""
    m = re.match(r'claude-([a-z]+)', model_id, re.I)
    return m.group(1).capitalize() if m else model_id

# Singletons
session_manager = SessionManager()
history_store = HistoryStore()
unread_state = UnreadState()
token_store = TokenStore()

# ── Token extraction ──────────────────────────────────────────────────────────
_TOKEN_RE = re.compile(r'\[Tokens:\s*([\d,]+)\s*in.*?/\s*([\d,]+)\s*out\s*\|\s*Cost:\s*\$([\d.]+)\]')


def _extract_tokens(content: str):
    m = _TOKEN_RE.search(content)
    if not m:
        return None
    return {
        'input_tokens': int(m.group(1).replace(',', '')),
        'output_tokens': int(m.group(2).replace(',', '')),
        'cost_usd': float(m.group(3)),
    }


# ── Claude authentication ─────────────────────────────────────────────────────

def check_claude_auth() -> bool:
    try:
        result = subprocess.run(
            [_CLAUDE_CMD, "-p", "reply with OK", "--max-turns", "1"],
            capture_output=True, text=True, timeout=60,
        )
        return result.returncode == 0
    except FileNotFoundError:
        log.error("Claude CLI not found — install with: npm install -g @anthropic-ai/claude-code")
        return False
    except subprocess.TimeoutExpired:
        log.warning("Claude auth check timed out")
        return False


def authenticate_claude() -> bool:
    log.info("Opening Claude for web authentication — please complete login in your browser...")
    try:
        result = subprocess.run([_CLAUDE_CMD], stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr)
        return result.returncode == 0
    except FileNotFoundError:
        log.error("Claude CLI not found")
        return False


def ensure_claude_auth() -> bool:
    log.info("Checking Claude session...")
    if check_claude_auth():
        log.info("Claude session is valid")
        return True
    log.warning("No valid Claude session, starting authentication...")
    if authenticate_claude() and check_claude_auth():
        log.info("Claude authentication successful")
        return True
    log.error("Claude authentication failed")
    return False


async def watch_claude_session():
    while True:
        await asyncio.sleep(CLAUDE_SESSION_CHECK_SECONDS)
        log.info("Periodic Claude session check...")
        loop = asyncio.get_event_loop()
        valid = await loop.run_in_executor(None, check_claude_auth)
        if not valid:
            log.warning("Claude session expired — attempting re-authentication...")
            await loop.run_in_executor(None, authenticate_claude)


# ── Auto-update watcher ──────────────────────────────────────────────────────

async def _broadcast_all(payload: dict):
    """Send a JSON message to every connected client, ignoring closed sockets."""
    msg = json.dumps(payload)
    for ws in list(connected_clients.values()):
        try:
            await ws.send(msg)
        except Exception:
            pass


async def watch_remote_changes(auto_update_cfg: dict):
    """Periodically check origin/<branch> for new commits; pull + rebuild + restart if found."""
    if not auto_update_cfg.get("enabled", False):
        return

    interval = int(auto_update_cfg.get("check_interval_minutes", 5)) * 60
    branch = auto_update_cfg.get("branch", "main")
    repo_root = BASE_DIR
    docker_script = os.path.join(repo_root, "helpers", "linux", "docker_build.sh")

    while True:
        await asyncio.sleep(interval)
        try:
            loop = asyncio.get_event_loop()

            # Fetch without modifying working tree
            fetch_result = await loop.run_in_executor(
                None,
                lambda: subprocess.run(
                    ["git", "fetch", "origin", branch],
                    cwd=repo_root, capture_output=True, timeout=30
                )
            )
            if fetch_result.returncode != 0:
                log.warning("[auto-update] git fetch failed (exit %d)", fetch_result.returncode)
                continue

            # Compare local HEAD vs remote tip
            loop = asyncio.get_event_loop()

            local = await loop.run_in_executor(
                None,
                lambda: subprocess.run(
                    ["git", "rev-parse", "HEAD"],
                    cwd=repo_root, capture_output=True, text=True
                ).stdout.strip()
            )

            remote = await loop.run_in_executor(
                None,
                lambda: subprocess.run(
                    ["git", "rev-parse", f"origin/{branch}"],
                    cwd=repo_root, capture_output=True, text=True
                ).stdout.strip()
            )

            if local == remote:
                continue

            log.info("[auto-update] New commits on origin/%s (local=%s remote=%s). Updating...",
                     branch, local[:8], remote[:8])

            # Notify connected clients
            await _broadcast_all({
                "type": "response",
                "project": "_server",
                "content": "Server update detected. Pulling changes and restarting..."
            })

            # Pull (merge)
            pull = await loop.run_in_executor(
                None,
                lambda: subprocess.run(
                    ["git", "merge", f"origin/{branch}"],
                    cwd=repo_root, capture_output=True, text=True, timeout=60
                )
            )
            if pull.returncode != 0:
                log.error("[auto-update] git merge failed:\n%s", pull.stderr)
                continue

            log.info("[auto-update] Merge successful. Rebuilding Docker image...")

            # Rebuild Docker image
            docker_build = await loop.run_in_executor(
                None,
                lambda: subprocess.run(
                    ["bash", docker_script],
                    cwd=repo_root, capture_output=True, text=True, timeout=600
                )
            )
            if docker_build.returncode != 0:
                log.error("[auto-update] Docker build failed:\n%s", docker_build.stderr)
            else:
                log.info("[auto-update] Docker image rebuilt successfully.")

            # Restart server by replacing the current process
            log.info("[auto-update] Restarting server...")
            os.execv(sys.executable, [sys.executable] + sys.argv)

        except Exception as e:
            log.error("[auto-update] Error during update check: %s", e)


# ── Config / data loading ─────────────────────────────────────────────────────

def load_config() -> dict:
    try:
        with open(CONFIG_PATH) as f:
            cfg = yaml.safe_load(f)
        return cfg.get("server", {})
    except FileNotFoundError:
        return {}


def load_users() -> dict:
    try:
        with open(USERS_PATH) as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def load_projects() -> list:
    try:
        with open(PROJECTS_PATH) as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def load_team(team_name: str) -> dict:
    team_path = os.path.join(TEAMS_DIR, f"{team_name}.md")
    if not os.path.isfile(team_path):
        log.warning("Team file not found: %s", team_path)
        return {}
    try:
        with open(team_path) as f:
            content = f.read()
        name = team_name
        description = ""
        lines = content.splitlines()
        for i, line in enumerate(lines):
            if line.startswith("# Team:"):
                name = line.replace("# Team:", "").strip()
            elif line.startswith("# ") and i == 0:
                name = line.lstrip("# ").strip()
            if i > 0 and line.strip() and not line.startswith("#") and not line.startswith("---"):
                description = line.strip()
                break
        return {"name": team_name, "display_name": name, "description": description}
    except Exception as e:
        log.error("Failed to load team '%s': %s", team_name, e)
        return {}


def get_available_teams() -> list:
    """Return list of {name, description} for all team .md files in teams/teams/."""
    teams = []
    if not os.path.isdir(TEAMS_DIR):
        return teams
    for f in sorted(os.listdir(TEAMS_DIR)):
        if f.endswith(".md"):
            team_name = f[:-3]
            data = load_team(team_name)
            if data:
                teams.append({"name": data["name"], "description": data.get("description", "")})
    return teams


def get_projects_for_user(username: str) -> list:
    teams = get_available_teams()
    return [
        {"name": p["name"], "description": p.get("description", ""), "team": p.get("team", ""), "available_teams": teams}
        for p in load_projects()
        if username in p.get("users", [])
    ]


def get_project_record(project_name: str) -> dict | None:
    for p in load_projects():
        if p["name"] == project_name:
            return p
    return None


def verify_password(stored_hash: str, received_hash: str) -> bool:
    return hmac.compare_digest(stored_hash, received_hash)


# ── Message file helpers ──────────────────────────────────────────────────────

def klodtalk_path(workspace: str, *parts: str) -> str:
    return os.path.join(workspace, KLODTALK_DIR, *parts)


def ensure_klodtalk_dir(workspace: str):
    for subdir in ("in_messages", "out_messages", "pr_messages", "history", "team/current", "requests"):
        os.makedirs(klodtalk_path(workspace, subdir), exist_ok=True)
    gitignore = os.path.join(workspace, ".gitignore")
    entry = f"/{KLODTALK_DIR}/\n"
    try:
        existing = open(gitignore).read() if os.path.isfile(gitignore) else ""
        if KLODTALK_DIR not in existing:
            with open(gitignore, "a") as f:
                f.write(("\n" if existing and not existing.endswith("\n") else "") + entry)
    except Exception:
        pass


def append_in_message(workspace: str, content: str) -> str:
    msg_folder = klodtalk_path(workspace, "in_messages")
    os.makedirs(msg_folder, exist_ok=True)
    path = os.path.join(msg_folder, "in_message.txt")
    existing = open(path).read() if os.path.isfile(path) else ""
    separator = "\n" if existing and not existing.endswith("\n") else ""
    new_content = existing + separator + content
    with open(path, "w") as f:
        f.write(new_content)
    return new_content


# ── Docker image management ───────────────────────────────────────────────────

def docker_image_exists() -> bool:
    result = subprocess.run(
        ["docker", "image", "inspect", DOCKER_IMAGE_NAME],
        capture_output=True,
    )
    return result.returncode == 0


def build_docker_image():
    log.info("Building Docker image '%s'...", DOCKER_IMAGE_NAME)
    result = subprocess.run(
        ["docker", "build", "-f", DOCKERFILE_PATH, "-t", DOCKER_IMAGE_NAME,
         BASE_DIR],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        log.error("Docker build failed:\n%s", result.stderr)
        return False
    log.info("Docker image '%s' built successfully", DOCKER_IMAGE_NAME)
    return True


def is_container_running(cname: str) -> bool:
    result = subprocess.run(
        ["docker", "inspect", "--format", "{{.State.Running}}", cname],
        capture_output=True, text=True,
    )
    return result.returncode == 0 and result.stdout.strip() == "true"


# ── Git helpers ───────────────────────────────────────────────────────────────

def _git(args: list[str], cwd: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True)


def _merge_single_repo(path: str, base_branch: str) -> str:
    """Fetch + merge base branch into current branch in a single repo."""
    if not os.path.isdir(os.path.join(path, ".git")):
        return "ok"
    _git(["config", "user.name", "Claude Bot"], path)
    _git(["config", "user.email", "claude@bot.local"], path)
    fetch = _git(["fetch", "origin", base_branch], path)
    if fetch.returncode != 0:
        log.warning("git fetch failed in '%s': %s", path, fetch.stderr.strip())
        return "ok"
    merge = _git(["merge", f"origin/{base_branch}", "--no-edit"], path)
    if merge.returncode != 0:
        log.warning("Merge conflicts in '%s': %s", path, merge.stderr.strip())
        return "conflicts"
    return "ok"


def git_prepare_workspace(workspace: str, project_config: dict) -> str:
    """Fetch + merge base branch(es) into the session workspace."""
    repos = project_config.get("repos")
    if repos:
        statuses = []
        for repo in repos:
            repo_path = os.path.join(workspace, repo["path"])
            branch = repo.get("base_branch", project_config.get("base_branch", "main"))
            statuses.append(_merge_single_repo(repo_path, branch))
        return "conflicts" if "conflicts" in statuses else "ok"
    else:
        return _merge_single_repo(workspace, project_config.get("base_branch", "main"))


def git_push_workspace(workspace: str, project_config: dict = None):
    repos = project_config.get("repos") if project_config else None
    if repos:
        for repo in repos:
            repo_path = os.path.join(workspace, repo["path"])
            if not os.path.isdir(os.path.join(repo_path, ".git")):
                continue
            result = _git(["push", "origin", "HEAD"], repo_path)
            if result.returncode != 0:
                log.error("git push failed in '%s': %s", repo_path, result.stderr.strip())
            else:
                log.info("git push OK in '%s'", repo_path)
    else:
        if not os.path.isdir(os.path.join(workspace, ".git")):
            return
        result = _git(["push", "origin", "HEAD"], workspace)
        if result.returncode != 0:
            log.error("git push failed in '%s': %s", workspace, result.stderr.strip())
        else:
            log.info("git push OK in '%s'", workspace)


# ── Copy team/utils files into container ─────────────────────────────────────

async def _copy_files_to_container(container_name: str) -> None:
    """Copy team files and utils into the running container before each exec.

    This allows modifying teams, members, operations, and python utils on the
    host without rebuilding the Docker image.
    """
    copies = [
        (os.path.join(BASE_DIR, "teams"), "/agent/claude_team"),
        (os.path.join(BASE_DIR, "server", "utils"), "/agent/utils"),
    ]
    dst_dirs = []
    for src, dst in copies:
        if not os.path.isdir(src):
            log.warning("Source directory %s not found, skipping copy", src)
            continue
        dst_dirs.append(dst)
        # docker cp src/. container:dst copies CONTENTS of src into dst
        proc = await asyncio.create_subprocess_exec(
            "docker", "cp", f"{src}/.", f"{container_name}:{dst}",
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        _, err = await proc.communicate()
        if proc.returncode != 0:
            log.error("docker cp %s -> %s:%s failed: %s", src, container_name, dst, err.decode())

    if not dst_dirs:
        return

    # Fix ownership and permissions inside the container (must run as root)
    dirs_str = " ".join(dst_dirs)
    fix_cmd = (
        f"chown -R 1000:1000 {dirs_str} 2>/dev/null; "
        f"find {dirs_str} -name '*.sh' -exec chmod +x {{}} \\; 2>/dev/null; "
        f"find {dirs_str} \\( -name '*.sh' -o -name '*.py' \\) -exec sed -i 's/\\r$//' {{}} \\; 2>/dev/null; "
        "true"
    )
    proc = await asyncio.create_subprocess_exec(
        "docker", "exec", "--user", "root", container_name, "bash", "-c", fix_cmd,
        stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL
    )
    await proc.wait()


# ── Agent triggering ──────────────────────────────────────────────────────────

async def trigger_session(session_id: str, mode: str, triggering_user: str):
    """Run the agent script for a session via docker exec."""
    if session_id in running_sessions:
        log.warning("Session '%s' is already running, skipping", session_id)
        return

    session = session_manager.get_session(session_id)
    if not session:
        log.error("Session '%s' not found", session_id)
        return

    if not is_container_running(session.container_name):
        log.error("Container '%s' for session '%s' is not running", session.container_name, session_id)
        await _notify_session_error(session_id, f"Agent container is not running for session {session_id}")
        return

    project = get_project_record(session.project_name)
    running_sessions.add(session_id)
    session_triggered_by[session_id] = triggering_user
    log.info("Triggering session '%s' (project=%s, mode=%s)", session_id, session.project_name, mode)

    await _broadcast_to_session_users(session_id, {
        "type": "session_working",
        "session_id": session_id,
        "working": True,
    })

    try:
        merge_status = "ok"
        if mode == "execute" and project:
            loop = asyncio.get_event_loop()
            merge_status = await loop.run_in_executor(
                None, lambda: git_prepare_workspace(session.workspace_path, project)
            )

        user_name = re.sub(r'[^\x20-\x7E]', '', triggering_user)[:64] or "unknown"
        team_name = _session_team_override.get(session_id) or (project.get("team") if project else None)
        is_team_mode = bool(team_name)
        repos_json = json.dumps(project.get("repos", []) if project else [])
        if team_name:
            results_folder = get_results_folder(project) if project else None
            team_data = {"name": team_name, "results_folder": results_folder or ""}

            team_json_dir = os.path.join(session.workspace_path, KLODTALK_DIR, "team")
            os.makedirs(team_json_dir, exist_ok=True)
            team_json_path = os.path.join(team_json_dir, "team.json")
            with open(team_json_path, "w") as tf:
                json.dump(team_data, tf, indent=2)
            if HOST_UID is not None and HOST_GID is not None:
                os.chown(team_json_dir, HOST_UID, HOST_GID)
                os.chown(team_json_path, HOST_UID, HOST_GID)

        # Copy fresh team/utils files into the container before every exec
        await _copy_files_to_container(session.container_name)

        # Prefer run_agent.py over run_agent.sh
        agent_script = "/agent/run_agent.py"
        check = subprocess.run(
            ["docker", "exec", session.container_name, "test", "-f", agent_script],
            capture_output=True
        )
        if check.returncode != 0:
            agent_script = "/agent/run_agent.sh"

        # Linux: map container user to host uid:gid for file ownership. Windows: 1000:1000.
        if HOST_UID is not None and HOST_GID is not None:
            host_uid = HOST_UID
            host_gid = HOST_GID
        else:
            host_uid = 1000
            host_gid = 1000

        proc = await asyncio.create_subprocess_exec(
            "docker", "exec",
            "--user", f"{host_uid}:{host_gid}",
            "-e", f"MODE={mode}",
            "-e", f"MERGE_STATUS={merge_status}",
            "-e", f"USER_NAME={user_name}",
            "-e", f"SESSION_ID={session_id}",
            "-e", f"TEAM_MODE={'true' if is_team_mode else 'false'}",
            "-e", f"REPOS_JSON={repos_json}",
            "-e", f"TEAM_NAME={team_name or ''}",
            session.container_name, agent_script,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        session_processes[session_id] = proc
        stdout, stderr = await proc.communicate()

        stdout_text = stdout.decode(errors="replace") if stdout else ""
        stderr_text = stderr.decode(errors="replace") if stderr else ""

        if stdout_text:
            log.info("Session '%s' stdout:\n%s", session_id, stdout_text)
        if stderr_text:
            log.warning("Session '%s' stderr:\n%s", session_id, stderr_text)

        if proc.returncode == 0:
            log.info("Session '%s' agent completed successfully", session_id)
            if mode == "execute" and project:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, lambda: git_push_workspace(session.workspace_path, project))
                if project.get("code_review"):
                    log.info("Scheduling code review for session '%s'", session_id)
                    asyncio.create_task(trigger_session(session_id, "review", triggering_user))
        else:
            error_detail = stderr_text.strip() or stdout_text.strip() or "(no output)"
            msg = f"Agent failed (exit code {proc.returncode}): {error_detail[-500:]}"
            log.error("Session '%s': %s", session_id, msg)
            await _notify_session_error(session_id, msg)
    except Exception as e:
        msg = f"Agent encountered an unexpected error: {e}"
        log.error("Session '%s': %s", session_id, msg)
        await _notify_session_error(session_id, msg)
    finally:
        session_processes.pop(session_id, None)
        running_sessions.discard(session_id)
        await _broadcast_to_session_users(session_id, {
            "type": "session_working",
            "session_id": session_id,
            "working": False,
        })


async def _notify_session_error(session_id: str, message: str):
    session = session_manager.get_session(session_id)
    if not session:
        return
    payload = json.dumps({
        "type": "error",
        "session_id": session_id,
        "project": session.project_name,
        "message": message
    })
    for user in session.users:
        ws = connected_clients.get(user)
        if ws:
            try:
                await ws.send(payload)
            except Exception:
                pass


async def _broadcast_to_session_users(session_id: str, payload: dict):
    """Send a message to all users registered on the session."""
    session = session_manager.get_session(session_id)
    if not session:
        return
    msg = json.dumps(payload)
    sent_to: set[str] = set()
    for user in session.users:
        if user in sent_to:
            continue
        ws = connected_clients.get(user)
        if ws:
            try:
                await ws.send(msg)
                sent_to.add(user)
            except Exception as e:
                log.error("Failed to send to '%s': %s", user, e)


# ── Output file watcher ───────────────────────────────────────────────────────

async def watch_out_messages():
    """Poll session workspaces for output files and push to clients."""
    log.info("Session watcher started (polling every %ds)", POLL_INTERVAL_SECONDS)
    while True:
        await asyncio.sleep(POLL_INTERVAL_SECONDS)
        try:
            for session in session_manager.get_active_sessions():
                session_id = session.session_id
                workspace = session.workspace_path

                if not os.path.isdir(workspace):
                    continue

                message_folder = klodtalk_path(workspace, "out_messages")
                os.makedirs(message_folder, exist_ok=True)

                # pr_message: code review
                pr_folder = klodtalk_path(workspace, "pr_messages")
                os.makedirs(pr_folder, exist_ok=True)
                pr_path = os.path.join(pr_folder, "pr_message.txt")
                if os.path.isfile(pr_path):
                    try:
                        content = open(pr_path).read()
                        os.remove(pr_path)
                        log.info("Session '%s' review message: %s...", session_id, content[:80])
                    except Exception as e:
                        log.error("Error reading pr_message for session '%s': %s", session_id, e)
                        content = None

                    if content:
                        _models = _session_team_models.get(session_id, {})
                        history_store.append(session_id, workspace, "review", content, model=_models.get("review", ""))
                        _mark_unread_for_others(session_id, session_triggered_by.get(session_id, ""))

                        _team_r = _session_team_override.get(session_id, "")
                        if not _team_r:
                            _p_r = get_project_record(session.project_name)
                            _team_r = _p_r.get("team", "") if _p_r else ""
                        await _broadcast_to_session_users(session_id, {
                            "type": "new_message",
                            "session_id": session_id,
                            "project": session.project_name,
                            "role": "review",
                            "content": content,
                            "timestamp": datetime.utcnow().isoformat() + "Z",
                            "model": _models.get("review", ""),
                            "team": _team_r,
                        })

                        # Auto-fix loop
                        project = get_project_record(session.project_name)
                        if project and project.get("code_review"):
                            iteration = review_iterations.get(session_id, 0)
                            review_iterations[session_id] = iteration + 1
                            user = session_triggered_by.get(session_id, "")
                            if iteration < MAX_REVIEW_ITERATIONS:
                                fix_request = (
                                    f"Code review findings (round {iteration + 1}/{MAX_REVIEW_ITERATIONS}):\n\n"
                                    f"{content}\n\n"
                                    "Please address all findings above and fix every issue mentioned."
                                )
                                in_path = klodtalk_path(workspace, "in_messages", "in_message.txt")
                                if os.path.isfile(in_path):
                                    os.remove(in_path)
                                append_in_message(workspace, fix_request)
                                asyncio.create_task(trigger_session(session_id, "execute", user))
                            else:
                                log.info("Review cap reached for session '%s'", session_id)

                # --- External file request fulfillment ---
                request_file = Path(workspace) / ".klodTalk" / "requests" / "file_request.txt"
                fulfilled_file = Path(workspace) / ".klodTalk" / "requests" / "file_fulfilled.txt"
                shared_dir = Path(workspace) / ".klodTalk" / "shared_files"

                if request_file.exists() and not fulfilled_file.exists():
                    project = get_project_record(session.project_name)
                    raw_paths = project.get("allowed_external_paths", []) if project else []
                    allowed_paths = [e["path"] for e in _normalize_external_paths(raw_paths)]
                    shared_dir.mkdir(parents=True, exist_ok=True)
                    lines = []
                    try:
                        for raw_path in request_file.read_text().splitlines():
                            raw_path = raw_path.strip()
                            if not raw_path:
                                continue
                            p = Path(raw_path)
                            if not p.is_absolute():
                                log.warning(
                                    "External file request rejected (relative path not allowed): %s", raw_path
                                )
                                continue
                            p_resolved = p.resolve()
                            if any(
                                p_resolved == Path(a).resolve()
                                or (Path(a).is_dir() and p_resolved.is_relative_to(Path(a).resolve()))
                                for a in allowed_paths
                            ):
                                if p_resolved.exists() and p_resolved.is_file():
                                    dest = shared_dir / p_resolved.name
                                    if dest.exists():
                                        stem, suffix = p_resolved.stem, p_resolved.suffix
                                        i = 1
                                        while dest.exists():
                                            dest = shared_dir / f"{stem}_{i}{suffix}"
                                            i += 1
                                    shutil.copy2(p_resolved, dest)
                                    lines.append(f"{raw_path}:{dest}")
                                    log.info("Shared external file: %s → %s", raw_path, dest)
                                else:
                                    log.warning("External file not found: %s", raw_path)
                            else:
                                log.warning(
                                    "External file request rejected (not in allowlist): %s", raw_path
                                )
                        fulfilled_file.write_text("\n".join(lines) + "\n")
                        request_file.unlink()
                    except Exception as e:
                        log.error("Error handling file request for session '%s': %s", session_id, e)

                # progress_message
                progress_path = os.path.join(message_folder, "progress_message.txt")
                if os.path.isfile(progress_path):
                    try:
                        content = open(progress_path).read()
                        os.remove(progress_path)
                    except Exception as e:
                        log.error("Error reading progress_message for session '%s': %s", session_id, e)
                        content = None

                    if content:
                        history_store.append(session_id, workspace, "progress", content)
                        await _broadcast_to_session_users(session_id, {
                            "type": "new_message",
                            "session_id": session_id,
                            "project": session.project_name,
                            "role": "progress",
                            "content": content,
                            "timestamp": datetime.utcnow().isoformat() + "Z",
                        })

                # planner_message
                planner_path = os.path.join(message_folder, "planner_message.txt")
                if os.path.isfile(planner_path):
                    try:
                        content = open(planner_path).read()
                        os.remove(planner_path)
                    except Exception as e:
                        log.error("Error reading planner_message for session '%s': %s", session_id, e)
                        content = None

                    if content:
                        _models = _session_team_models.get(session_id, {})
                        _team_p = _session_team_override.get(session_id, "")
                        if not _team_p:
                            _p_p = get_project_record(session.project_name)
                            _team_p = _p_p.get("team", "") if _p_p else ""
                        history_store.append(session_id, workspace, "planner", content, model=_models.get("planner", ""))
                        await _broadcast_to_session_users(session_id, {
                            "type": "new_message",
                            "session_id": session_id,
                            "project": session.project_name,
                            "role": "planner",
                            "content": content,
                            "timestamp": datetime.utcnow().isoformat() + "Z",
                            "model": _models.get("planner", ""),
                            "team": _team_p,
                        })

                # coder_message
                coder_msg_path = os.path.join(message_folder, "coder_message.txt")
                if os.path.isfile(coder_msg_path):
                    try:
                        content = open(coder_msg_path).read()
                        os.remove(coder_msg_path)
                    except Exception as e:
                        log.error("Error reading coder_message for session '%s': %s", session_id, e)
                        content = None

                    if content:
                        _models = _session_team_models.get(session_id, {})
                        _team_c = _session_team_override.get(session_id, "")
                        if not _team_c:
                            _p_c = get_project_record(session.project_name)
                            _team_c = _p_c.get("team", "") if _p_c else ""
                        history_store.append(session_id, workspace, "coder", content, model=_models.get("coder", ""))
                        await _broadcast_to_session_users(session_id, {
                            "type": "new_message",
                            "session_id": session_id,
                            "project": session.project_name,
                            "role": "coder",
                            "content": content,
                            "timestamp": datetime.utcnow().isoformat() + "Z",
                            "model": _models.get("coder", ""),
                            "team": _team_c,
                        })

                # idea_message
                idea_path = os.path.join(message_folder, "idea_message.txt")
                if os.path.isfile(idea_path):
                    try:
                        content = open(idea_path).read()
                        os.remove(idea_path)
                    except Exception as e:
                        log.error("Error reading idea_message for session '%s': %s", session_id, e)
                        content = None

                    if content:
                        _models = _session_team_models.get(session_id, {})
                        _team_i = _session_team_override.get(session_id, "")
                        if not _team_i:
                            _p_i = get_project_record(session.project_name)
                            _team_i = _p_i.get("team", "") if _p_i else ""
                        history_store.append(session_id, workspace, "idea", content, model=_models.get("idea", ""))
                        await _broadcast_to_session_users(session_id, {
                            "type": "new_message",
                            "session_id": session_id,
                            "project": session.project_name,
                            "role": "idea",
                            "content": content,
                            "timestamp": datetime.utcnow().isoformat() + "Z",
                            "model": _models.get("idea", ""),
                            "team": _team_i,
                        })

                # idea_review_message
                idea_review_path = os.path.join(message_folder, "idea_review_message.txt")
                if os.path.isfile(idea_review_path):
                    try:
                        content = open(idea_review_path).read()
                        os.remove(idea_review_path)
                    except Exception as e:
                        log.error("Error reading idea_review_message for session '%s': %s", session_id, e)
                        content = None

                    if content:
                        _models = _session_team_models.get(session_id, {})
                        _team_ir = _session_team_override.get(session_id, "")
                        if not _team_ir:
                            _p_ir = get_project_record(session.project_name)
                            _team_ir = _p_ir.get("team", "") if _p_ir else ""
                        history_store.append(session_id, workspace, "idea_review", content, model=_models.get("idea_review", ""))
                        await _broadcast_to_session_users(session_id, {
                            "type": "new_message",
                            "session_id": session_id,
                            "project": session.project_name,
                            "role": "idea_review",
                            "content": content,
                            "timestamp": datetime.utcnow().isoformat() + "Z",
                            "model": _models.get("idea_review", ""),
                            "team": _team_ir,
                        })

                # final_plan_message
                final_plan_path = os.path.join(message_folder, "final_plan_message.txt")
                if os.path.isfile(final_plan_path):
                    try:
                        content = open(final_plan_path).read()
                        os.remove(final_plan_path)
                    except Exception as e:
                        log.error("Error reading final_plan_message for session '%s': %s", session_id, e)
                        content = None

                    if content:
                        _models = _session_team_models.get(session_id, {})
                        _team_fp = _session_team_override.get(session_id, "")
                        if not _team_fp:
                            _p_fp = get_project_record(session.project_name)
                            _team_fp = _p_fp.get("team", "") if _p_fp else ""
                        history_store.append(session_id, workspace, "final_plan", content, model=_models.get("final_plan", ""))
                        await _broadcast_to_session_users(session_id, {
                            "type": "new_message",
                            "session_id": session_id,
                            "project": session.project_name,
                            "role": "final_plan",
                            "content": content,
                            "timestamp": datetime.utcnow().isoformat() + "Z",
                            "model": _models.get("final_plan", ""),
                            "team": _team_fp,
                        })

                # idea_history_message
                idea_history_path = os.path.join(message_folder, "idea_history_message.txt")
                if os.path.isfile(idea_history_path):
                    try:
                        content = open(idea_history_path).read()
                        os.remove(idea_history_path)
                    except Exception as e:
                        log.error("Error reading idea_history_message for session '%s': %s", session_id, e)
                        content = None

                    if content:
                        _models = _session_team_models.get(session_id, {})
                        _team_ih = _session_team_override.get(session_id, "")
                        if not _team_ih:
                            _p_ih = get_project_record(session.project_name)
                            _team_ih = _p_ih.get("team", "") if _p_ih else ""
                        history_store.append(session_id, workspace, "idea_history", content, model=_models.get("idea_history", ""))
                        await _broadcast_to_session_users(session_id, {
                            "type": "new_message",
                            "session_id": session_id,
                            "project": session.project_name,
                            "role": "idea_history",
                            "content": content,
                            "timestamp": datetime.utcnow().isoformat() + "Z",
                            "model": _models.get("idea_history", ""),
                            "team": _team_ih,
                        })

                # btw_response
                btw_response_path = os.path.join(message_folder, "btw_response.txt")
                if os.path.isfile(btw_response_path):
                    try:
                        content = open(btw_response_path).read()
                        os.remove(btw_response_path)
                    except Exception as e:
                        log.error("Error reading btw_response for session '%s': %s", session_id, e)
                        content = None
                    if content:
                        history_store.append(session_id, workspace, "agent", content)
                        await _broadcast_to_session_users(session_id, {
                            "type": "new_message",
                            "session_id": session_id,
                            "project": session.project_name,
                            "role": "agent",
                            "content": content,
                            "timestamp": datetime.utcnow().isoformat() + "Z",
                        })
                        user = session_triggered_by.get(session_id, "")
                        if user:
                            t = _extract_tokens(content)
                            if t:
                                token_store.add_tokens(user, t['input_tokens'], t['output_tokens'], t['cost_usd'])
                                await _broadcast_usage_summary()

                # confirm_message
                confirm_path = os.path.join(message_folder, "confirm_message.txt")
                if os.path.isfile(confirm_path):
                    try:
                        content = open(confirm_path).read()
                        os.remove(confirm_path)
                        log.info("Session '%s' confirm: %s...", session_id, content[:80])
                    except Exception as e:
                        log.error("Error reading confirm_message for session '%s': %s", session_id, e)
                        content = None

                    if content:
                        history_store.append(session_id, workspace, "agent", content)
                        _mark_unread_for_others(session_id, session_triggered_by.get(session_id, ""))
                        await _broadcast_to_session_users(session_id, {
                            "type": "new_message",
                            "session_id": session_id,
                            "project": session.project_name,
                            "role": "agent",
                            "content": content,
                            "timestamp": datetime.utcnow().isoformat() + "Z",
                        })
                        # Mark session so the next new message knows a confirm response was sent
                        pending_confirm.add(session_id)
                        user = session_triggered_by.get(session_id, "")
                        if user:
                            t = _extract_tokens(content)
                            if t:
                                token_store.add_tokens(user, t['input_tokens'], t['output_tokens'], t['cost_usd'])
                                await _broadcast_usage_summary()

                # out_message: task complete
                out_files = [
                    f for f in os.listdir(message_folder)
                    if f.endswith(".txt") and f not in _OUT_MESSAGE_EXCLUDED
                ]
                if out_files:
                    out_path = os.path.join(message_folder, out_files[0])
                    try:
                        content = open(out_path).read()
                        os.remove(out_path)
                        in_msg_path = klodtalk_path(workspace, "in_messages", "in_message.txt")
                        if os.path.isfile(in_msg_path):
                            os.remove(in_msg_path)
                        log.info("Session '%s' out_message: %s...", session_id, content[:80])
                    except Exception as e:
                        log.error("Error reading out_message for session '%s': %s", session_id, e)
                        content = None

                    if content:
                        history_store.append(session_id, workspace, "agent", content)
                        _mark_unread_for_others(session_id, session_triggered_by.get(session_id, ""))
                        _team = _session_team_override.get(session_id, "")
                        if not _team:
                            _p = get_project_record(session.project_name)
                            _team = _p.get("team", "") if _p else ""
                        await _broadcast_to_session_users(session_id, {
                            "type": "new_message",
                            "session_id": session_id,
                            "project": session.project_name,
                            "role": "agent",
                            "content": content,
                            "timestamp": datetime.utcnow().isoformat() + "Z",
                            "team": _team,
                        })
                        # Also send legacy "response" for backward compat
                        await _broadcast_to_session_users(session_id, {
                            "type": "response",
                            "project": session.project_name,
                            "content": content,
                            "session_id": session_id,
                        })
                        user = session_triggered_by.get(session_id, "")
                        if user:
                            t = _extract_tokens(content)
                            if t:
                                token_store.add_tokens(user, t['input_tokens'], t['output_tokens'], t['cost_usd'])
                                await _broadcast_usage_summary()

        except Exception as e:
            log.error("Watcher error: %s", e)


def _mark_unread_for_others(session_id: str, triggering_user: str):
    """Mark session unread for all registered session users except the triggerer."""
    session = session_manager.get_session(session_id)
    if not session:
        return
    others = [u for u in session.users if u != triggering_user]
    if others:
        unread_state.mark_unread(session_id, others)


async def _broadcast_usage_summary():
    """Broadcast updated token usage summary to all connected clients."""
    summary = token_store.get_summary()
    payload = json.dumps({"type": "usage_summary", **summary})
    for ws in list(connected_clients.values()):
        try:
            await ws.send(payload)
        except Exception:
            pass


# ── Session history helper ────────────────────────────────────────────────────

def _session_to_dict(session, include_messages: bool = False, workspace_override: str = None) -> dict:
    d = {
        "session_id": session.session_id,
        "project": session.project_name,
        "branch": session.git_branch,
        "status": session.status,
        "created_at": session.created_at,
        "closed_at": session.closed_at,
        "user_name": session.user_name,
        "users": session.users,
        "working": session.session_id in running_sessions,
        "system": getattr(session, 'system', False),
    }
    if include_messages:
        if session.status == "closed":
            archive = session_manager.get_archive_path(session)
            # Archive stores session.jsonl directly in archive dir (not in .klodTalk/history/)
            archive_file = os.path.join(archive, "session.jsonl") if archive else ""
            if archive_file and os.path.isfile(archive_file):
                messages = []
                try:
                    with open(archive_file) as f:
                        for line in f:
                            line = line.strip()
                            if not line:
                                continue
                            try:
                                messages.append(json.loads(line))
                            except json.JSONDecodeError:
                                continue
                except Exception as e:
                    log.error("Failed to read archive history for session %s: %s", session.session_id, e)
                d["messages"] = messages
            else:
                d["messages"] = []
        else:
            d["messages"] = history_store.read_session(session.session_id, session.workspace_path)
    return d


# ── WebSocket handlers ────────────────────────────────────────────────────────


async def handle_stop(ws, user_name: str, data: dict):
    """Kill the running agent process for a session."""
    session_id = data.get("session_id", "")
    session = session_manager.get_session(session_id)
    if not session:
        await ws.send(json.dumps({"type": "error", "message": "Session not found"}))
        return
    if getattr(session, 'system', False):
        await ws.send(json.dumps({"type": "error", "reason": "system_session",
                                  "message": "System sessions cannot be stopped by users"}))
        return
    if user_name not in session.users:
        await ws.send(json.dumps({"type": "error", "message": "Forbidden"}))
        return
    if session_id not in running_sessions:
        await ws.send(json.dumps({"type": "error", "message": "Session is not running"}))
        return
    proc = session_processes.get(session_id)
    if proc:
        log.info("Stopping session '%s' (killing docker exec process)", session_id)
        try:
            proc.kill()
        except ProcessLookupError:
            pass
        # Also kill any Claude processes inside the container
        kill_cmd = "pkill -f 'claude' || true"
        try:
            pkill_proc = await asyncio.create_subprocess_exec(
                "docker", "exec", session.container_name, "bash", "-c", kill_cmd,
                stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL,
            )
            await pkill_proc.communicate()
        except Exception:
            pass
    # Write a stop message to history
    history_store.append(session_id, session.workspace_path, "system", "Session stopped by user.")
    await _broadcast_to_session_users(session_id, {
        "type": "new_message",
        "session_id": session_id,
        "project": session.project_name,
        "role": "system",
        "content": "Stopped by user.",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    })


async def handle_btw(ws, user_name: str, data: dict):
    """Send a BTW side-channel message to a running agent."""
    session_id = data.get("session_id", "")
    content = data.get("content", "").strip()
    if not content:
        await ws.send(json.dumps({"type": "error", "message": "BTW content is empty"}))
        return
    session = session_manager.get_session(session_id)
    if not session:
        await ws.send(json.dumps({"type": "error", "message": "Session not found"}))
        return
    if getattr(session, 'system', False):
        await ws.send(json.dumps({"type": "error", "reason": "system_session",
                                  "message": "System sessions do not accept user messages"}))
        return
    if user_name not in session.users:
        await ws.send(json.dumps({"type": "error", "message": "Forbidden"}))
        return
    if session_id not in running_sessions:
        await ws.send(json.dumps({"type": "error", "message": "Session is not running"}))
        return

    # Log BTW message to history
    history_store.append(session_id, session.workspace_path, "user", f"[BTW] {content}")
    await _broadcast_to_session_users(session_id, {
        "type": "new_message",
        "session_id": session_id,
        "project": session.project_name,
        "role": "user",
        "content": f"[BTW] {content}",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    })

    # Write BTW file for the agent
    btw_path = klodtalk_path(session.workspace_path, "in_messages", "btw_message.txt")
    with open(btw_path, "w") as f:
        f.write(content)

    # Run a lightweight parallel Claude call inside the container
    host_uid = HOST_UID if HOST_UID is not None else 1000
    host_gid = HOST_GID if HOST_GID is not None else 1000
    asyncio.create_task(_run_btw_agent(session_id, session, host_uid, host_gid))

    await ws.send(json.dumps({
        "type": "ack",
        "session_id": session_id,
        "content": "BTW message sent to agent.",
    }))


async def _run_btw_agent(session_id: str, session, host_uid: int, host_gid: int):
    """Run a lightweight BTW call in the container."""
    try:
        # Copy fresh files before exec (same as trigger_session_agent)
        await _copy_files_to_container(session.container_name)

        agent_script = "/agent/run_agent.py"
        check = subprocess.run(
            ["docker", "exec", session.container_name, "test", "-f", agent_script],
            capture_output=True
        )
        if check.returncode != 0:
            log.error("BTW: run_agent.py not found in container '%s'", session.container_name)
            return

        proc = await asyncio.create_subprocess_exec(
            "docker", "exec",
            "--user", f"{host_uid}:{host_gid}",
            "-e", "MODE=btw",
            session.container_name, agent_script,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if stdout:
            log.info("BTW agent stdout for '%s': %s", session_id, stdout.decode(errors="replace")[:200])
        if stderr:
            log.warning("BTW agent stderr for '%s': %s", session_id, stderr.decode(errors="replace")[:200])
    except Exception as e:
        log.error("BTW agent call failed for session '%s': %s", session_id, e)


async def handle_new_session(ws, user_name: str, data: dict):
    project_name = data.get("project", "")
    project = get_project_record(project_name)
    if not project:
        await ws.send(json.dumps({"type": "error", "reason": "unknown_project", "message": f"No project named '{project_name}'"}))
        return
    if user_name not in project.get("users", []):
        await ws.send(json.dumps({"type": "error", "reason": "forbidden", "message": f"You don't have access to project '{project_name}'"}))
        return

    if not docker_image_exists():
        log.info("Docker image not found, building...")
        if not build_docker_image():
            await ws.send(json.dumps({"type": "error", "reason": "docker_build_failed", "message": "Could not build Docker image"}))
            return

    log.info("User '%s' creating session for project '%s'", user_name, project_name)

    temp_id = str(uuid.uuid4())[:8]
    await ws.send(json.dumps({
        "type": "session_preparing",
        "temp_id": temp_id,
        "project": project_name,
    }))

    loop = asyncio.get_event_loop()
    session = await loop.run_in_executor(
        None, lambda: session_manager.create_session(project_name, user_name, project)
    )

    if not session:
        await ws.send(json.dumps({"type": "error", "reason": "session_create_failed", "message": "Failed to create session"}))
        return

    await ws.send(json.dumps({
        "type": "session_created",
        "temp_id": temp_id,
        "session_id": session.session_id,
        "project": session.project_name,
        "branch": session.git_branch,
        "created_at": session.created_at,
        "status": "active",
    }))
    log.info("Session '%s' created for user '%s'", session.session_id, user_name)


async def handle_close_session(ws, user_name: str, data: dict):
    session_id = data.get("session_id", "")
    session = session_manager.get_session(session_id)
    if not session:
        await ws.send(json.dumps({"type": "error", "reason": "unknown_session", "message": f"Session '{session_id}' not found"}))
        return

    if getattr(session, 'system', False):
        await ws.send(json.dumps({"type": "error", "reason": "system_session",
                                  "message": "System sessions cannot be closed"}))
        return

    if user_name != session.user_name:
        await ws.send(json.dumps({"type": "error", "reason": "forbidden", "message": "Only the session owner can close this session"}))
        return

    await ws.send(json.dumps({"type": "session_closing", "session_id": session_id}))

    loop = asyncio.get_event_loop()
    ok = await loop.run_in_executor(None, lambda: session_manager.close_session(session_id))

    if ok:
        await ws.send(json.dumps({"type": "session_closed", "session_id": session_id}))
        log.info("Session '%s' closed by '%s'", session_id, user_name)
    else:
        await ws.send(json.dumps({"type": "error", "reason": "close_failed", "session_id": session_id, "message": "Failed to close session"}))


async def handle_delete_session(ws, user_name: str, data: dict):
    session_id = data.get("session_id", "")
    session = session_manager.get_session(session_id)
    if not session:
        await ws.send(json.dumps({"type": "error", "reason": "unknown_session", "message": f"Session '{session_id}' not found"}))
        return

    if getattr(session, 'system', False):
        await ws.send(json.dumps({"type": "error", "reason": "system_session",
                                  "message": "System sessions cannot be deleted"}))
        return

    if session.status != "closed":
        await ws.send(json.dumps({"type": "error", "reason": "session_active",
                                  "message": "Cannot delete an active session; close it first"}))
        return

    if user_name != session.user_name:
        await ws.send(json.dumps({"type": "error", "reason": "forbidden", "message": "Only the session owner can delete this session"}))
        return

    ok = session_manager.delete_session(session_id)
    if ok:
        await ws.send(json.dumps({"type": "session_deleted", "session_id": session_id}))
        log.info("Session '%s' deleted by '%s'", session_id, user_name)
    else:
        await ws.send(json.dumps({"type": "error", "reason": "delete_failed", "message": "Failed to delete session"}))


async def handle_reopen_session(ws, user_name: str, data: dict):
    session_id = data.get("session_id", "")
    session = session_manager.get_session(session_id)
    if not session:
        await ws.send(json.dumps({"type": "error", "reason": "unknown_session", "message": f"Session '{session_id}' not found"}))
        return

    if getattr(session, 'system', False):
        await ws.send(json.dumps({"type": "error", "reason": "system_session",
                                  "message": "System sessions cannot be reopened"}))
        return

    if session.status == "active":
        await ws.send(json.dumps({"type": "error", "reason": "session_active",
                                  "message": "Session is already active"}))
        return

    if not os.path.isdir(session.workspace_path):
        await ws.send(json.dumps({"type": "error", "reason": "workspace_missing",
                                  "session_id": session_id,
                                  "message": "Session workspace no longer exists. Cannot reopen."}))
        return

    if user_name != session.user_name:
        await ws.send(json.dumps({"type": "error", "reason": "forbidden", "message": "Only the session owner can reopen this session"}))
        return

    project = get_project_record(session.project_name)
    if not project:
        await ws.send(json.dumps({"type": "error", "reason": "unknown_project", "message": f"Project '{session.project_name}' no longer configured"}))
        return

    if not docker_image_exists():
        log.info("Docker image not found, building...")
        if not build_docker_image():
            await ws.send(json.dumps({"type": "error", "reason": "docker_build_failed", "message": "Could not build Docker image"}))
            return

    await ws.send(json.dumps({"type": "session_reopening", "session_id": session_id}))

    loop = asyncio.get_event_loop()
    ok = await loop.run_in_executor(None, lambda: session_manager.reopen_session(session_id, project))

    if ok:
        await ws.send(json.dumps({"type": "session_reopened", "session_id": session_id, "status": "active"}))
        log.info("Session '%s' reopened by '%s'", session_id, user_name)
    else:
        await ws.send(json.dumps({"type": "error", "reason": "reopen_failed",
                                  "session_id": session_id,
                                  "message": "Failed to reopen session"}))


async def handle_text(ws, user_name: str, data: dict):
    session_id = data.get("session_id", "")
    mode = data.get("mode", "")
    content = data.get("content", "")
    team_override = data.get("team", "")

    if mode not in ("execute", "confirm"):
        await ws.send(json.dumps({"type": "error", "reason": "invalid_mode", "message": "mode must be 'execute' or 'confirm'"}))
        return

    if not content.strip():
        await ws.send(json.dumps({"type": "error", "reason": "empty_content", "message": "content must not be empty"}))
        return

    session = session_manager.get_session(session_id)
    if not session:
        await ws.send(json.dumps({"type": "error", "reason": "unknown_session", "message": f"Session '{session_id}' not found"}))
        return

    if getattr(session, 'system', False) and mode != "confirm":
        await ws.send(json.dumps({"type": "error", "reason": "system_session",
                                  "message": "System sessions only accept read-back (confirm) mode"}))
        return

    if session.status != "active":
        await ws.send(json.dumps({"type": "error", "reason": "session_closed", "message": "Session is closed"}))
        return

    if user_name not in session.users:
        await ws.send(json.dumps({"type": "error", "reason": "forbidden", "message": "You don't have access to this session"}))
        return

    if getattr(session, 'system', False) and session_id in running_sessions:
        await ws.send(json.dumps({"type": "error", "reason": "session_busy",
                                  "message": "System session is currently running. Please wait until it finishes."}))
        return

    # If a confirm (read-back) was already sent for this session, clear the accumulated
    # in_message.txt when the user starts a new request (confirm mode = new question).
    # For execute mode we keep the existing content so the confirmed task can still run.
    if session_id in pending_confirm:
        pending_confirm.discard(session_id)
        if mode == "confirm":
            in_msg_path = klodtalk_path(session.workspace_path, "in_messages", "in_message.txt")
            if os.path.isfile(in_msg_path):
                os.remove(in_msg_path)

    # Append to workspace in_message.txt
    append_in_message(session.workspace_path, content)

    # Log user message to history
    history_store.append(session_id, session.workspace_path, "user", content)

    ts = datetime.now().strftime("%H:%M:%S")
    log.info("[%s] %s → session %s (mode=%s): %s", ts, user_name, session_id, mode, content)

    # Broadcast user message to all session users
    await _broadcast_to_session_users(session_id, {
        "type": "new_message",
        "session_id": session_id,
        "project": session.project_name,
        "role": "user",
        "content": content,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    })

    # Store or clear team override for this session
    if team_override:
        _session_team_override[session_id] = team_override
    elif session_id in _session_team_override:
        del _session_team_override[session_id]

    if mode == "execute":
        review_iterations[session_id] = 0
        ack = json.dumps({"type": "ack", "session_id": session_id, "content": "Got it — working on it now."})
        await ws.send(ack)

    asyncio.create_task(trigger_session(session_id, mode, user_name))


async def handle_scout_now(ws, user_name: str, data: dict):
    """Trigger the nightly scouting routine on demand."""
    session_id = SYSTEM_SESSION_ID
    session = session_manager.get_session(session_id)
    if not session:
        await ws.send(json.dumps({"type": "error", "reason": "no_system_session",
                                  "message": "System session not found. Is the routine enabled in config?"}))
        return

    if user_name not in session.users:
        await ws.send(json.dumps({"type": "error", "reason": "forbidden",
                                  "message": "You don't have access to the system session"}))
        return

    if session_id in running_sessions:
        await ws.send(json.dumps({"type": "error", "reason": "session_busy",
                                  "message": "Scout is already running"}))
        return

    # Load routine config
    try:
        with open(CONFIG_PATH) as f:
            full_cfg = yaml.safe_load(f) or {}
    except FileNotFoundError:
        full_cfg = {}
    routine_cfg = full_cfg.get("routine", {})
    if not routine_cfg.get("project"):
        await ws.send(json.dumps({"type": "error", "reason": "routine_disabled",
                                  "message": "Routine project is not configured in server config"}))
        return

    # Send ack before starting
    await ws.send(json.dumps({"type": "ack", "session_id": session_id,
                              "content": "Starting scout now..."}))

    # Trigger the routine (reuse existing run_nightly_routine)
    asyncio.create_task(run_nightly_routine(routine_cfg))


async def handle_get_history(ws, user_name: str):
    projects = load_projects()
    sessions = session_manager.get_user_sessions(user_name)
    unread = unread_state.get_unread(user_name)

    history = []
    for s in sessions:
        history.append(_session_to_dict(s, include_messages=True))

    await ws.send(json.dumps({
        "type": "history",
        "sessions": history,
        "unread": unread,
    }))
    log.info("Sent history (%d sessions) to '%s'", len(history), user_name)


async def handle_mark_read(ws, user_name: str, data: dict):
    session_id = data.get("session_id", "")
    session = session_manager.get_session(session_id)
    if not session or user_name not in session.users:
        await ws.send(json.dumps({"type": "error", "message": "Forbidden"}))
        return
    unread_state.mark_read(session_id, user_name)
    await ws.send(json.dumps({"type": "read_ack", "session_id": session_id}))


async def handle_get_usage_summary(ws, user_name: str):
    summary = token_store.get_summary()
    await ws.send(json.dumps({"type": "usage_summary", **summary}))


async def handle_add_user_to_session(ws, user_name: str, data: dict):
    """Add another user to a session. Only the session owner (creator) can do this."""
    session_id = data.get("session_id", "")
    target_user = data.get("target_user", "").strip()
    if not target_user:
        await ws.send(json.dumps({"type": "error", "message": "target_user is required"}))
        return

    session = session_manager.get_session(session_id)
    if not session:
        await ws.send(json.dumps({"type": "error", "message": "Session not found"}))
        return

    if getattr(session, 'system', False):
        await ws.send(json.dumps({"type": "error", "reason": "system_session",
                                  "message": "System session user list cannot be modified"}))
        return

    # Only the session owner can add users
    if user_name != session.user_name:
        await ws.send(json.dumps({"type": "error", "message": "Only the session owner can add users"}))
        return

    # Validate target user exists
    users = load_users()
    if target_user not in users:
        await ws.send(json.dumps({"type": "error", "message": f"User '{target_user}' does not exist"}))
        return

    # Validate target user has access to the project
    project = get_project_record(session.project_name)
    if project and target_user not in project.get("users", []):
        await ws.send(json.dumps({"type": "error", "message": f"User '{target_user}' does not have access to project '{session.project_name}'"}))
        return

    session_manager.add_user_to_session(session_id, target_user)

    # Notify the caller
    await ws.send(json.dumps({
        "type": "session_user_added",
        "session_id": session_id,
        "target_user": target_user,
        "users": session.users,
    }))
    log.info("User '%s' added '%s' to session '%s'", user_name, target_user, session_id)

    # Notify the target user if connected
    target_ws = connected_clients.get(target_user)
    if target_ws and target_ws != ws:
        try:
            await target_ws.send(json.dumps({
                "type": "session_user_added",
                "session_id": session_id,
                "target_user": target_user,
                "users": session.users,
            }))
        except Exception:
            pass


async def handle_remove_user_from_session(ws, user_name: str, data: dict):
    """Remove a user from a session.

    Permissions:
    - The session owner can remove any other user, but not themselves.
    - Non-owner users can remove themselves (leave), but no one else.
    """
    session_id = data.get("session_id", "")
    target_user = data.get("target_user", "").strip()
    if not target_user:
        await ws.send(json.dumps({"type": "error", "message": "target_user is required"}))
        return

    session = session_manager.get_session(session_id)
    if not session:
        await ws.send(json.dumps({"type": "error", "message": "Session not found"}))
        return

    if getattr(session, 'system', False):
        await ws.send(json.dumps({"type": "error", "reason": "system_session",
                                  "message": "System session user list cannot be modified"}))
        return

    # Owner cannot be removed (neither by themselves nor by others)
    if target_user == session.user_name:
        await ws.send(json.dumps({"type": "error", "message": "Cannot remove the session owner"}))
        return

    is_owner = user_name == session.user_name
    is_self_removal = target_user == user_name

    # Non-owners can only remove themselves
    if not is_owner and not is_self_removal:
        await ws.send(json.dumps({"type": "error", "message": "Only the session owner can remove other users"}))
        return

    if target_user not in session.users:
        await ws.send(json.dumps({"type": "error", "message": f"User '{target_user}' is not in this session"}))
        return

    session_manager.remove_user_from_session(session_id, target_user)

    # Notify the caller
    await ws.send(json.dumps({
        "type": "session_user_removed",
        "session_id": session_id,
        "target_user": target_user,
        "users": session.users,
    }))
    log.info("User '%s' removed '%s' from session '%s'", user_name, target_user, session_id)

    # Notify the target user if connected (omit users list for the evicted user)
    target_ws = connected_clients.get(target_user)
    if target_ws and target_ws != ws:
        try:
            await target_ws.send(json.dumps({
                "type": "session_user_removed",
                "session_id": session_id,
                "target_user": target_user,
            }))
        except Exception:
            pass


# ── Agent logs, token breakdown, session analysis ────────────────────────────

async def handle_get_agent_logs(ws, user_name: str, data: dict):
    """Return enriched JSONL events for a session's Claude logs."""
    session_id = data.get("session_id", "")
    session = session_manager.get_session(session_id)
    if not session:
        await ws.send(json.dumps({"type": "error", "message": "Session not found"}))
        return
    if user_name not in session.users:
        await ws.send(json.dumps({"type": "error", "message": "Forbidden"}))
        return

    # Find claude_logs in archive (closed sessions)
    logs_dir = ""
    tmp_dir = None
    if session.project_folder:
        archive_dir = os.path.join(
            session.project_folder, ".klodTalk", "sessions", session_id, "claude_logs"
        )
        if os.path.isdir(archive_dir):
            logs_dir = archive_dir

    # For active sessions, fetch live logs from the running container
    if not logs_dir:
        tmp_dir = session_manager.get_live_claude_logs(session_id)
        if tmp_dir:
            logs_dir = tmp_dir

    if not logs_dir:
        await ws.send(json.dumps({
            "type": "agent_logs",
            "session_id": session_id,
            "sessions": [],
            "message": "No Claude JSONL logs found for this session."
        }))
        return

    try:
        discovered = discover_archived_sessions(logs_dir)
        result_sessions = []
        for disc in discovered:
            events = read_session_jsonl(disc["path"])
            tokens = aggregate_session_tokens(events)
            result_sessions.append({
                "claude_session_id": disc["session_id"],
                "event_count": len(events),
                "tokens": tokens,
                "subagent_ids": disc["subagent_ids"],
                "events": events,
            })

        await ws.send(json.dumps({
            "type": "agent_logs",
            "session_id": session_id,
            "sessions": result_sessions,
        }))
    finally:
        if tmp_dir:
            shutil.rmtree(tmp_dir, ignore_errors=True)


async def handle_get_subagent_logs(ws, user_name: str, data: dict):
    """Return enriched JSONL events for a specific sub-agent."""
    session_id = data.get("session_id", "")
    parent_session_id = data.get("parent_session_id", "")
    agent_id = data.get("agent_id", "")

    # Validate IDs contain only hex characters to prevent path traversal
    _HEX_RE = re.compile(r'^[a-f0-9]+$')
    if parent_session_id and not _HEX_RE.match(parent_session_id):
        await ws.send(json.dumps({"type": "error", "message": "Invalid parent_session_id"}))
        return
    if agent_id and not _HEX_RE.match(agent_id):
        await ws.send(json.dumps({"type": "error", "message": "Invalid agent_id"}))
        return

    session = session_manager.get_session(session_id)
    if not session:
        await ws.send(json.dumps({"type": "error", "message": "Session not found"}))
        return
    if user_name not in session.users:
        await ws.send(json.dumps({"type": "error", "message": "Forbidden"}))
        return

    logs_dir = ""
    tmp_dir = None
    if session.project_folder:
        archive_dir = os.path.join(
            session.project_folder, ".klodTalk", "sessions", session_id, "claude_logs"
        )
        if os.path.isdir(archive_dir):
            logs_dir = archive_dir

    # For active sessions, fetch live logs from the running container
    if not logs_dir:
        tmp_dir = session_manager.get_live_claude_logs(session_id)
        if tmp_dir:
            logs_dir = tmp_dir

    try:
        events = []
        if logs_dir:
            events = read_subagent_jsonl(logs_dir, parent_session_id, agent_id)

        tokens = aggregate_session_tokens(events) if events else {}
        await ws.send(json.dumps({
            "type": "subagent_logs",
            "session_id": session_id,
            "agent_id": agent_id,
            "events": events,
            "tokens": tokens,
        }))
    finally:
        if tmp_dir:
            shutil.rmtree(tmp_dir, ignore_errors=True)


async def handle_get_session_tokens(ws, user_name: str, data: dict):
    """Return per-step token breakdown for a session."""
    session_id = data.get("session_id", "")
    session = session_manager.get_session(session_id)
    if not session:
        await ws.send(json.dumps({"type": "error", "message": "Session not found"}))
        return
    if user_name not in session.users:
        await ws.send(json.dumps({"type": "error", "message": "Forbidden"}))
        return

    breakdown = token_store.get_session_breakdown(session.user_name, session_id)

    # If no per-role steps exist, compute tokens from JSONL logs directly
    if not breakdown.get("steps"):
        logs_dir = ""
        tmp_dir = None
        if session.project_folder:
            archive_dir = os.path.join(
                session.project_folder, ".klodTalk", "sessions", session_id, "claude_logs"
            )
            if os.path.isdir(archive_dir):
                logs_dir = archive_dir

        # For active sessions, fetch live logs from the running container
        if not logs_dir:
            tmp_dir = session_manager.get_live_claude_logs(session_id)
            if tmp_dir:
                logs_dir = tmp_dir

        if logs_dir:
            try:
                discovered = discover_archived_sessions(logs_dir)
                total_input = 0
                total_output = 0
                total_cache_creation = 0
                total_cache_read = 0
                for disc in discovered:
                    events = read_session_jsonl(disc["path"], filter_noise=False)
                    tokens = aggregate_session_tokens(events)
                    total_input += tokens.get("input", 0)
                    total_output += tokens.get("output", 0)
                    total_cache_creation += tokens.get("cache_creation", 0)
                    total_cache_read += tokens.get("cache_read", 0)

                if total_input or total_output:
                    breakdown = {
                        "steps": {
                            "claude": {
                                "input_tokens": total_input,
                                "output_tokens": total_output,
                                "cache_creation": total_cache_creation,
                                "cache_read": total_cache_read,
                                "cost_usd": 0.0,
                            }
                        },
                        "total_input": total_input,
                        "total_output": total_output,
                        "total_cost": 0.0,
                    }
            finally:
                if tmp_dir:
                    shutil.rmtree(tmp_dir, ignore_errors=True)

    await ws.send(json.dumps({
        "type": "session_tokens",
        "session_id": session_id,
        "breakdown": breakdown,
    }))


# session_id -> analysis result (cached)
_session_analyses: dict[str, dict] = {}
# session_ids with analysis currently running
_session_analysis_running: set[str] = set()


async def handle_analyze_session(ws, user_name: str, data: dict):
    """Trigger Claude analysis of a session's history."""
    session_id = data.get("session_id", "")
    session = session_manager.get_session(session_id)
    if not session:
        await ws.send(json.dumps({"type": "error", "message": "Session not found"}))
        return
    if user_name not in session.users:
        await ws.send(json.dumps({"type": "error", "message": "Forbidden"}))
        return

    # Check if analysis already exists
    if session_id in _session_analyses:
        await ws.send(json.dumps({
            "type": "session_analysis",
            "session_id": session_id,
            "analysis": _session_analyses[session_id],
            "status": "complete",
        }))
        return

    if session_id in _session_analysis_running:
        await ws.send(json.dumps({
            "type": "session_analysis",
            "session_id": session_id,
            "status": "running",
        }))
        return

    # Get session history
    if session.status == "closed":
        archive = session_manager.get_archive_path(session)
        archive_file = os.path.join(archive, "session.jsonl") if archive else ""
        if archive_file and os.path.isfile(archive_file):
            messages = []
            with open(archive_file) as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            messages.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
        else:
            messages = []
    else:
        messages = history_store.read_session(session_id, session.workspace_path)

    if not messages:
        await ws.send(json.dumps({
            "type": "session_analysis",
            "session_id": session_id,
            "status": "error",
            "message": "No session history found to analyze.",
        }))
        return

    _session_analysis_running.add(session_id)
    await ws.send(json.dumps({
        "type": "session_analysis",
        "session_id": session_id,
        "status": "running",
    }))

    asyncio.create_task(_run_session_analysis(session_id, session, messages, user_name))


async def _run_session_analysis(session_id: str, session, messages: list, user_name: str):
    """Run Claude to analyze the session."""
    try:
        prompt_path = os.path.join(BASE_DIR, "server", "prompts", "analyze_session.md")
        with open(prompt_path) as f:
            system_prompt = f.read()

        history_text = ""
        MAX_HISTORY_CHARS = 100_000
        for i, msg in enumerate(messages):
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            ts = msg.get("timestamp", "")
            history_text += f"[{i}] [{role}] ({ts})\n{content}\n\n"
            if len(history_text) > MAX_HISTORY_CHARS:
                history_text = history_text[:MAX_HISTORY_CHARS]
                history_text += "\n\n[... history truncated at 100,000 characters ...]"
                break

        full_prompt = f"{system_prompt}\n\n---\n\n## Session History\n\n{history_text}"

        loop = asyncio.get_event_loop()

        def run_claude():
            result = subprocess.run(
                [_CLAUDE_CMD, "--dangerously-skip-permissions", "--output-format", "json",
                 "-p", full_prompt, "--max-turns", "1"],
                capture_output=True, text=True, timeout=120,
            )
            return result.stdout.strip()

        raw_output = await loop.run_in_executor(None, run_claude)

        # Parse the output
        try:
            output_data = json.loads(raw_output)
            content = output_data.get("result", raw_output)
        except json.JSONDecodeError:
            content = raw_output

        # Try to parse as JSON analysis
        analysis = None
        try:
            json_match = re.search(r'\{[\s\S]*"tasks"[\s\S]*\}', content)
            if json_match:
                analysis = json.loads(json_match.group())
        except (json.JSONDecodeError, AttributeError):
            pass

        if not analysis:
            analysis = {"raw_text": content, "tasks": [], "overall_suggestions": []}

        _session_analyses[session_id] = analysis

        # Save analysis to archive if available
        if session.project_folder:
            analysis_dir = os.path.join(
                session.project_folder, ".klodTalk", "sessions", session_id
            )
            os.makedirs(analysis_dir, exist_ok=True)
            analysis_path = os.path.join(analysis_dir, "analysis.json")
            with open(analysis_path, "w") as f:
                json.dump(analysis, f, indent=2)

        await _broadcast_to_session_users(session_id, {
            "type": "session_analysis",
            "session_id": session_id,
            "analysis": analysis,
            "status": "complete",
        })
    except Exception as e:
        log.error("Session analysis failed for '%s': %s", session_id, e)
        await _broadcast_to_session_users(session_id, {
            "type": "session_analysis",
            "session_id": session_id,
            "status": "error",
            "message": str(e),
        })
    finally:
        _session_analysis_running.discard(session_id)


MAX_DIFF_BYTES = 500_000  # 500 KB cap on diff output


def _parse_diff_into_files(diff_text: str) -> list[dict]:
    """Split a unified diff string into per-file entries."""
    if not diff_text.strip() or diff_text.startswith("("):
        return []
    # Split on 'diff --git' boundaries
    chunks = re.split(r'(?=^diff --git )', diff_text, flags=re.MULTILINE)
    files = []
    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk or not chunk.startswith("diff --git"):
            continue
        # Extract paths from 'diff --git a/... b/...'
        m = re.match(r'diff --git a/(.*?) b/(.*?)$', chunk, re.MULTILINE)
        if m:
            old_path = m.group(1)
            new_path = m.group(2)
        else:
            old_path = new_path = "unknown"
        files.append({"path": new_path, "old_path": old_path, "diff_text": chunk})
    return files


def _git_diff_single(path: str, base_branch: str) -> str:
    """Run git diff origin/<base_branch>...HEAD in a single repo directory."""
    if not os.path.isdir(os.path.join(path, ".git")):
        return ""
    result = _git(["diff", f"origin/{base_branch}...HEAD"], path)
    if result.returncode != 0:
        # Fallback: try plain diff HEAD if three-dot syntax fails (e.g. no remote)
        result = _git(["diff", "HEAD~1"], path)
        if result.returncode != 0:
            return f"(git diff failed in {path}: {result.stderr.strip()})"
    return result.stdout


async def handle_get_diff(ws, user_name: str, data: dict):
    session_id = data.get("session_id", "")
    session = session_manager.get_session(session_id)
    if not session:
        await ws.send(json.dumps({"type": "error", "reason": "unknown_session",
                                  "message": f"Session '{session_id}' not found"}))
        return

    if user_name not in session.users:
        await ws.send(json.dumps({"type": "error", "reason": "forbidden",
                                  "message": "You don't have access to this session"}))
        return

    workspace = session.workspace_path
    if not os.path.isdir(workspace):
        await ws.send(json.dumps({"type": "diff_result", "session_id": session_id,
                                  "diff": "(Workspace no longer exists)"}))
        return

    project = get_project_record(session.project_name)
    loop = asyncio.get_event_loop()

    def compute_diff():
        repos = project.get("repos") if project else None
        if repos:
            parts = []
            for repo in repos:
                repo_path = os.path.join(workspace, repo["path"])
                branch = repo.get("base_branch", project.get("base_branch", "main") if project else "main")
                diff_text = _git_diff_single(repo_path, branch)
                if diff_text:
                    parts.append(f"=== {repo['path']} ===\n{diff_text}")
            return "\n".join(parts) if parts else ""
        else:
            base_branch = project.get("base_branch", "main") if project else "main"
            return _git_diff_single(workspace, base_branch)

    diff_result = await loop.run_in_executor(None, compute_diff)

    # Parse per-repo to avoid separator lines bleeding into file diffs (Issue 2)
    repos = project.get("repos") if project else None
    if repos and isinstance(diff_result, str) and diff_result.strip() and "=== " in diff_result:
        # diff_result contains "=== repo_path ===\n<diff>" blocks
        files = []
        diff_text_parts = []
        for block in re.split(r'(?=^=== .+ ===$)', diff_result, flags=re.MULTILINE):
            block = block.strip()
            if not block:
                continue
            # Extract repo prefix from separator line
            sep_match = re.match(r'^=== (.+) ===$', block, re.MULTILINE)
            if sep_match:
                repo_prefix = sep_match.group(1)
                repo_diff = block[sep_match.end():].strip()
            else:
                repo_prefix = ""
                repo_diff = block
            diff_text_parts.append(block)
            repo_files = _parse_diff_into_files(repo_diff)
            for f in repo_files:
                if repo_prefix:
                    f["path"] = repo_prefix + "/" + f["path"]
                    f["old_path"] = repo_prefix + "/" + f["old_path"]
            files.extend(repo_files)
        diff_text = "\n".join(diff_text_parts) if diff_text_parts else "(No changes found)"
    else:
        diff_text = diff_result if isinstance(diff_result, str) else ""
        if not diff_text.strip():
            diff_text = "(No changes found)"
        files = _parse_diff_into_files(diff_text)

    truncated = False
    if len(diff_text.encode("utf-8", errors="replace")) > MAX_DIFF_BYTES:
        diff_text = diff_text[:MAX_DIFF_BYTES] + "\n\n... (diff truncated — exceeded 500 KB limit)"
        truncated = True

    await ws.send(json.dumps({
        "type": "diff_result",
        "session_id": session_id,
        "diff": diff_text,
        "files": files,
        "truncated": truncated,
    }))
    log.info("Sent diff (%d bytes, %d files) for session '%s' to '%s'",
             len(diff_text), len(files), session_id, user_name)


async def handle_revert_hunk(ws, user_name: str, data: dict):
    """Revert a specific hunk by applying git apply --reverse."""
    import tempfile

    session_id = data.get("session_id", "")
    request_id = data.get("request_id", "")
    file_path = data.get("file_path", "")
    hunk_text = data.get("hunk_text", "")

    # Issue 6: length validation on hunk_text
    if len(hunk_text) > 1_000_000:
        await ws.send(json.dumps({"type": "revert_result", "session_id": session_id,
                                  "request_id": request_id,
                                  "success": False, "error": "Hunk text too large (>1 MB)"}))
        return

    session = session_manager.get_session(session_id)
    if not session:
        await ws.send(json.dumps({"type": "revert_result", "session_id": session_id,
                                  "request_id": request_id,
                                  "success": False, "error": "Session not found"}))
        return

    if user_name not in session.users:
        await ws.send(json.dumps({"type": "revert_result", "session_id": session_id,
                                  "request_id": request_id,
                                  "success": False, "error": "Access denied"}))
        return

    workspace = session.workspace_path
    if not os.path.isdir(workspace):
        await ws.send(json.dumps({"type": "revert_result", "session_id": session_id,
                                  "request_id": request_id,
                                  "success": False, "error": "Workspace not found"}))
        return

    loop = asyncio.get_event_loop()

    def do_revert():
        # Write the patch to a temp file and apply --reverse
        with tempfile.NamedTemporaryFile(mode='w', suffix='.patch', delete=False) as f:
            f.write(hunk_text)
            if not hunk_text.endswith('\n'):
                f.write('\n')
            patch_path = f.name
        try:
            result = subprocess.run(
                ["git", "apply", "--reverse", patch_path],
                cwd=workspace, capture_output=True, text=True,
            )
            return result
        finally:
            os.unlink(patch_path)

    try:
        result = await loop.run_in_executor(None, do_revert)
        if result.returncode == 0:
            # Track reverted file for targeted commit (Issue 3)
            reverted = _session_reverted_files.setdefault(session_id, set())
            reverted.add(file_path)
            await ws.send(json.dumps({"type": "revert_result", "session_id": session_id,
                                      "request_id": request_id,
                                      "success": True, "file_path": file_path}))
            log.info("Reverted hunk in '%s' for session '%s' by '%s'", file_path, session_id, user_name)
        else:
            err = result.stderr.strip() or result.stdout.strip() or "Unknown error"
            await ws.send(json.dumps({"type": "revert_result", "session_id": session_id,
                                      "request_id": request_id,
                                      "success": False, "error": err}))
            log.warning("Revert failed for '%s' in session '%s': %s", file_path, session_id, err)
    except Exception as e:
        await ws.send(json.dumps({"type": "revert_result", "session_id": session_id,
                                  "request_id": request_id,
                                  "success": False, "error": str(e)}))


async def handle_commit_and_push(ws, user_name: str, data: dict):
    """Commit all changes and push to remote."""
    session_id = data.get("session_id", "")
    commit_message = data.get("message", "").strip() or "Manual changes via KlodTalk"

    session = session_manager.get_session(session_id)
    if not session:
        await ws.send(json.dumps({"type": "commit_push_result", "session_id": session_id,
                                  "success": False, "message": "Session not found"}))
        return

    if user_name not in session.users:
        await ws.send(json.dumps({"type": "commit_push_result", "session_id": session_id,
                                  "success": False, "message": "Access denied"}))
        return

    workspace = session.workspace_path
    if not os.path.isdir(workspace):
        await ws.send(json.dumps({"type": "commit_push_result", "session_id": session_id,
                                  "success": False, "message": "Workspace not found"}))
        return

    loop = asyncio.get_event_loop()

    def do_commit_push():
        # Stage only reverted files (Issue 3), not all changes
        reverted_files = _session_reverted_files.get(session_id, set())
        if reverted_files:
            for fpath in reverted_files:
                add_result = _git(["add", "--", fpath], workspace)
                if add_result.returncode != 0:
                    log.warning("git add failed for '%s': %s", fpath, add_result.stderr.strip())
        else:
            # Fallback: stage all if no reverted files tracked (shouldn't happen normally)
            add_result = _git(["add", "-A"], workspace)
            if add_result.returncode != 0:
                return False, f"git add failed: {add_result.stderr.strip()}"

        # Commit
        commit_result = _git(["commit", "-m", commit_message], workspace)
        if commit_result.returncode != 0:
            stderr = commit_result.stderr.strip()
            stdout = commit_result.stdout.strip() if commit_result.stdout else ""
            if "nothing to commit" in stderr or "nothing to commit" in stdout:
                return True, "Nothing to commit — all changes are already committed"
            return False, f"git commit failed: {stderr}"

        # Push
        push_result = _git(["push", "origin", "HEAD"], workspace)
        if push_result.returncode != 0:
            return False, f"Committed but push failed: {push_result.stderr.strip()}"

        return True, "Changes committed and pushed successfully"

    try:
        success, message = await loop.run_in_executor(None, do_commit_push)
        if success:
            _session_reverted_files.pop(session_id, None)
        await ws.send(json.dumps({"type": "commit_push_result", "session_id": session_id,
                                  "success": success, "message": message}))
        log.info("Commit & push for session '%s' by '%s': %s — %s",
                 session_id, user_name, "OK" if success else "FAIL", message)
    except Exception as e:
        await ws.send(json.dumps({"type": "commit_push_result", "session_id": session_id,
                                  "success": False, "message": str(e)}))


async def handle_client(websocket):
    remote = websocket.remote_address
    client_name = None
    authenticated = False
    hello_received = False
    connect_time = time.monotonic()
    log.info("New connection from %s:%s", remote[0], remote[1])

    users = load_users()

    try:
        async for raw in websocket:
            if not hello_received:
                log.debug("First message received from %s:%s", remote[0], remote[1])
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue

            msg_type = msg.get("type")

            if msg_type == "hello":
                hello_received = True
                client_name = msg.get("name", "")
                password_hash = msg.get("password_hash", "")
                user_record = users.get(client_name)

                if user_record and verify_password(user_record["password_hash"], password_hash):
                    authenticated = True
                    connected_clients[client_name] = websocket
                    log.info(
                        "=== CLIENT CONNECTED ===\n  User: %s\n  IP:   %s\n  Time: %s\n========================",
                        client_name, remote[0], datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    )

                    # Send agents list
                    user_projects = get_projects_for_user(client_name)
                    await websocket.send(json.dumps({"type": "projects", "projects": user_projects}))

                    # Send sessions + full history (including closed sessions) + unread
                    await handle_get_history(websocket, client_name)
                    log.info("Sent %d project(s) + full history to %s", len(user_projects), client_name)

                    # Send current token usage summary
                    await handle_get_usage_summary(websocket, client_name)
                else:
                    log.warning("AUTH FAILED for user '%s' from %s", client_name, remote[0])
                    await websocket.close(4001, "Authentication failed")
                    return

            elif not authenticated:
                log.warning("Unauthenticated message from %s, ignoring", remote[0])

            elif msg_type == "new_session":
                await handle_new_session(websocket, client_name, msg)

            elif msg_type == "close_session":
                await handle_close_session(websocket, client_name, msg)

            elif msg_type == "delete_session":
                await handle_delete_session(websocket, client_name, msg)

            elif msg_type == "reopen_session":
                await handle_reopen_session(websocket, client_name, msg)

            elif msg_type == "text":
                await handle_text(websocket, client_name, msg)

            elif msg_type == "get_history":
                await handle_get_history(websocket, client_name)

            elif msg_type == "mark_read":
                await handle_mark_read(websocket, client_name, msg)

            elif msg_type == "get_usage_summary":
                await handle_get_usage_summary(websocket, client_name)

            elif msg_type == "get_diff":
                await handle_get_diff(websocket, client_name, msg)

            elif msg_type == "revert_hunk":
                await handle_revert_hunk(websocket, client_name, msg)

            elif msg_type == "commit_and_push":
                await handle_commit_and_push(websocket, client_name, msg)

            elif msg_type == "stop":
                await handle_stop(websocket, client_name, msg)

            elif msg_type == "btw":
                await handle_btw(websocket, client_name, msg)

            elif msg_type == "scout_now":
                await handle_scout_now(websocket, client_name, msg)

            elif msg_type == "add_user_to_session":
                await handle_add_user_to_session(websocket, client_name, msg)

            elif msg_type == "remove_user_from_session":
                await handle_remove_user_from_session(websocket, client_name, msg)

            elif msg_type == "get_agent_logs":
                await handle_get_agent_logs(websocket, client_name, msg)

            elif msg_type == "get_subagent_logs":
                await handle_get_subagent_logs(websocket, client_name, msg)

            elif msg_type == "get_session_tokens":
                await handle_get_session_tokens(websocket, client_name, msg)

            elif msg_type == "analyze_session":
                await handle_analyze_session(websocket, client_name, msg)

            else:
                log.warning("Unknown message type '%s' from %s", msg_type, remote[0])

    except websockets.exceptions.ConnectionClosed as e:
        duration_ms = int((time.monotonic() - connect_time) * 1000)
        code = e.rcvd.code if e.rcvd else None
        hello_str = "hello received" if hello_received else "no hello received"
        if code == 1006:
            log.warning(
                "Connection from %s closed abnormally (code=1006) after %dms — %s. "
                "rcvd=%s sent=%s. Likely: network drop or client crash before auth.",
                client_name or remote[0], duration_ms, hello_str, e.rcvd, e.sent,
            )
        else:
            log.info(
                "Connection closed by %s (code=%s) after %dms — %s. rcvd=%s sent=%s",
                client_name or remote[0], code, duration_ms, hello_str, e.rcvd, e.sent,
            )
    finally:
        if client_name and client_name in connected_clients:
            del connected_clients[client_name]
            log.info("Removed '%s' from connected clients", client_name)


# ── Nightly Routine ───────────────────────────────────────────────────────────


def _build_team_routine_prompt(tags: list[str], max_ideas: int, project_name: str) -> str:
    """Build a concise prompt for the nightly routine when using a team pipeline."""
    sanitized_tags = [re.sub(r'[^a-zA-Z0-9\s\-]', '', tag.replace('\n', ' ').replace('\r', ' ')) for tag in tags]
    tags_str = ", ".join(sanitized_tags)
    week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    return f"""# Nightly GitHub Scouting Task

Search GitHub for repositories and ideas related to: {tags_str}
Focus on recent activity (last 7 days, since {week_ago}).
Prefer repositories with more stars, but don't exclude promising low-star repos.
Look for: tools, skills, MCP servers, prompt techniques, workflow patterns for Claude Code and multi-agent systems.
Evaluate and implement the top {max_ideas} most impactful and feasible ideas for the {project_name} project.
"""


def _build_routine_prompt(tags: list[str], max_ideas: int, project_name: str) -> str:
    """Build the prompt for the nightly GitHub scouting routine."""
    # Sanitize tags: strip newlines and enforce alphanumeric/hyphen/space allowlist
    sanitized_tags = [re.sub(r'[^a-zA-Z0-9\s\-]', '', tag.replace('\n', ' ').replace('\r', ' ')) for tag in tags]
    tags_str = ", ".join(sanitized_tags)
    today = datetime.now().strftime("%Y-%m-%d")
    week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    return f"""# Nightly Improvement Routine

You are running an automated nightly routine for the {project_name} project (a multi-agent orchestration system built on Claude Code CLI).

## Your Task

### Step 1: Scout GitHub
Search GitHub for public repositories and discussions related to these topics: {tags_str}

Focus on:
- Repositories with recent activity (created or updated in the last 7 days, since {week_ago})
- Tools, skills, MCP servers, prompt techniques, or workflow patterns
- Things that could improve multi-agent orchestration, team definitions, role prompts, or developer workflows
- Claude Code CLI tips, custom slash commands, or automation patterns

Use web search to search GitHub. Example searches:
- `site:github.com claude-code skill created:>{week_ago}`
- `site:github.com anthropic claude agent workflow`
- GitHub trending repositories in the AI/LLM space

### Step 2: Evaluate Ideas
For each interesting finding, evaluate:
- Is it relevant to our codebase? (multi-agent teams, WebSocket server, Docker containers, Claude CLI)
- How hard would it be to implement?
- What would be the impact? (productivity, quality, developer experience)

### Step 3: Implement Top Ideas
Pick the top {max_ideas} most impactful and feasible ideas. For each one:
- Describe what you found and why it's useful
- Implement it in our codebase if possible (new team definitions, improved role prompts, server enhancements, etc.)
- If it requires changes that are too large, describe what needs to be done and create a plan

### Step 4: Report
Write a clear summary report with:
- **Scouted**: What you searched and how many repos/resources you reviewed
- **Found**: The most interesting ideas (even ones you didn't implement)
- **Implemented**: What you actually changed, with file paths
- **Recommended**: Ideas that need human review before implementing

Write this report as your final output. Be specific about what you changed and why.
"""


async def watch_nightly_routine(routine_cfg: dict):
    """Sleep until the configured hour, then run the nightly routine."""
    if not routine_cfg.get("enabled", False):
        log.info("[routine] Nightly routine disabled in config")
        return

    hour = int(routine_cfg.get("schedule_hour", 4))
    minute = int(routine_cfg.get("schedule_minute", 0))
    project_name = routine_cfg.get("project", "")

    if not project_name:
        log.error("[routine] No project configured for nightly routine")
        return

    log.info("[routine] Nightly routine enabled, scheduled for %02d:%02d", hour, minute)

    while True:
        # Calculate seconds until next scheduled time
        now = datetime.now()
        target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if target <= now:
            target += timedelta(days=1)
        wait_seconds = (target - now).total_seconds()

        log.info("[routine] Next run at %s (in %.0f minutes)",
                 target.strftime("%Y-%m-%d %H:%M"), wait_seconds / 60)

        await asyncio.sleep(wait_seconds)

        log.info("[routine] === Nightly routine starting ===")
        try:
            await run_nightly_routine(routine_cfg)
        except Exception as e:
            log.error("[routine] Nightly routine failed: %s", e)

        # Sleep at least 60 seconds to avoid double-triggering
        await asyncio.sleep(60)


async def run_nightly_routine(routine_cfg: dict):
    """Execute the nightly GitHub scouting and implementation routine."""
    project_name = routine_cfg.get("project", "")
    project = get_project_record(project_name)
    if not project:
        log.error("[routine] Project '%s' not found", project_name)
        return

    tags = routine_cfg.get("github_search_tags", ["claude", "claude-code"])
    max_ideas = routine_cfg.get("max_ideas_to_implement", 3)

    # 1. Ensure system session exists
    all_users = list({u for p in load_projects() for u in p.get("users", [])})
    session = session_manager.get_session(SYSTEM_SESSION_ID)

    if not session or session.status != "active":
        if session and session.status == "closed":
            # Reopen it (system sessions shouldn't be closed, but handle gracefully)
            session.system = True
            session_manager.reopen_session(SYSTEM_SESSION_ID, project)
            session = session_manager.get_session(SYSTEM_SESSION_ID)
        else:
            session = session_manager.create_system_session(
                SYSTEM_SESSION_ID, project_name, project, all_users
            )

    if not session:
        log.error("[routine] Failed to create/get system session")
        return

    # Update users list to include everyone
    for u in all_users:
        if u not in session.users:
            session.users.append(u)
    session_manager.save_sessions()

    # 2. Determine team and build prompt
    team_name = routine_cfg.get("team", "github-scout")
    if team_name:
        _session_team_override[SYSTEM_SESSION_ID] = team_name
        routine_prompt = _build_team_routine_prompt(tags, max_ideas, project_name)
    else:
        routine_prompt = _build_routine_prompt(tags, max_ideas, project_name)

    # 3. Write the prompt to the system session's in_message.txt
    workspace = session.workspace_path
    ensure_klodtalk_dir(workspace)
    in_path = klodtalk_path(workspace, "in_messages", "in_message.txt")
    # Clear any previous message
    if os.path.isfile(in_path):
        os.remove(in_path)
    append_in_message(workspace, routine_prompt)

    # 4. Log the routine start to history
    history_store.append(SYSTEM_SESSION_ID, workspace, "system",
                         f"Nightly routine started at {datetime.utcnow().isoformat()}Z")

    # 5. Notify all connected clients
    await _broadcast_to_session_users(SYSTEM_SESSION_ID, {
        "type": "new_message",
        "session_id": SYSTEM_SESSION_ID,
        "project": project_name,
        "role": "system",
        "content": "Nightly routine starting: scanning GitHub for Claude-related improvements...",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    })

    # 6. Trigger the agent in execute mode
    await trigger_session(SYSTEM_SESSION_ID, "execute", "_system")


# ── Main ──────────────────────────────────────────────────────────────────────

async def main():
    cfg = load_config()
    host = cfg.get("host", "0.0.0.0")
    port = cfg.get("port", 9000)

    # Load full YAML for auto_update section (load_config returns only "server")
    try:
        with open(CONFIG_PATH) as f:
            full_cfg = yaml.safe_load(f) or {}
    except FileNotFoundError:
        full_cfg = {}
    auto_update_cfg = full_cfg.get("auto_update", {})

    ensure_claude_auth()

    users = load_users()
    projects = load_projects()
    log.info("Registered users: %s", ", ".join(users.keys()) if users else "(none)")
    log.info("Registered projects: %d", len(projects))
    docker_socket_projects = [p["name"] for p in projects if p.get("docker_socket", True)]
    if docker_socket_projects:
        log.info("Projects with Docker socket access: %s", ", ".join(docker_socket_projects))
    if docker_socket_projects and not os.path.exists("/var/run/docker.sock"):
        log.warning(
            "Docker socket /var/run/docker.sock not found on host. "
            "Projects with docker_socket enabled (%s) will fail to start sessions. "
            "Ensure the Docker daemon is running.",
            ", ".join(docker_socket_projects),
        )

    # Clean up orphaned sessions from previous run
    try:
        session_manager.cleanup_orphaned_sessions()
    except Exception as e:
        log.warning("Session cleanup warning: %s", e)

    # Migrate existing sessions: populate users list for backward compatibility
    session_manager.migrate_sessions_add_users(projects)

    # Initialize system session for nightly routine
    routine_cfg = full_cfg.get("routine", {})
    if routine_cfg.get("enabled", False):
        routine_project = routine_cfg.get("project", "")
        if routine_project:
            rp = get_project_record(routine_project)
            if rp:
                all_users = list({u for p in projects for u in p.get("users", [])})
                sys_session = session_manager.get_session(SYSTEM_SESSION_ID)
                if sys_session and sys_session.status == "closed":
                    session_manager.reopen_session(SYSTEM_SESSION_ID, rp)
                # Always call create_system_session: for new sessions it creates them,
                # for existing sessions it updates the users list.
                session_manager.create_system_session(SYSTEM_SESSION_ID, routine_project, rp, all_users)
                log.info("[routine] System session '%s' ready", SYSTEM_SESSION_ID)
            else:
                log.warning("[routine] Project '%s' not found in config", routine_project)
        else:
            log.warning("[routine] routine.enabled is true but no project configured")

    # TLS / WSS setup
    ssl_cert = cfg.get("ssl_cert", "")
    ssl_key = cfg.get("ssl_key", "")
    ssl_context = None
    if ssl_cert and ssl_key:
        ssl_context = ssl_module.SSLContext(ssl_module.PROTOCOL_TLS_SERVER)
        ssl_context.load_cert_chain(ssl_cert, ssl_key)
        log.info("WSS (TLS) enabled with cert: %s", ssl_cert)
    else:
        log.warning("SSL not configured — running plain ws:// (not recommended for untrusted networks)")

    protocol = "wss" if ssl_context else "ws"
    log.info("Starting KlodTalk server on %s://0.0.0.0:%s", protocol, port)

    asyncio.create_task(watch_out_messages())
    asyncio.create_task(watch_claude_session())
    asyncio.create_task(watch_remote_changes(auto_update_cfg))
    asyncio.create_task(watch_nightly_routine(routine_cfg))

    # Pre-create the socket to avoid getaddrinfo failures on Windows (Winsock errno 10109).
    # Binding directly to (host, port) bypasses getaddrinfo entirely.
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind((host, int(port)))

    async with websockets.serve(handle_client, sock=server_sock, ssl=ssl_context):
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
