#!/usr/bin/env python3
"""Session lifecycle management for KlodTalk."""

import json
import logging
import os
import platform
import re
import shutil
import subprocess
import tempfile
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Optional

from copy_tree import copy_git_tracked
from utils.docker import get_docker_utils

log = logging.getLogger("klodtalk.sessions")

BASE_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
CONFIG_DIR = os.path.join(BASE_DIR, "config")
STATE_DIR = os.path.join(BASE_DIR, ".klodTalk", "state")
os.makedirs(STATE_DIR, exist_ok=True)
SESSIONS_PATH = os.path.join(STATE_DIR, "sessions.json")
COUNTERS_PATH = os.path.join(STATE_DIR, "session_counters.json")
TEMP_BASE = os.path.join(tempfile.gettempdir(), "klodtalk")

DOCKER_IMAGE_NAME = "klodtalk-agent"
CONTAINER_PREFIX = "klodtalk_session_"

_IS_WINDOWS = platform.system() == "Windows"
HOST_UID = None if _IS_WINDOWS else os.getuid()
HOST_GID = None if _IS_WINDOWS else os.getgid()
CONTAINER_HOME = "/home/agent"


def sanitize_image_name(project_name: str) -> str:
    """Convert project name to a valid Docker image name.

    Lowercase, replace non-alphanumeric/underscore with underscore,
    collapse runs of underscores, strip leading/trailing underscores.
    """
    name = project_name.lower()
    name = re.sub(r'[^a-z0-9_]', '_', name)
    name = re.sub(r'_+', '_', name)
    name = name.strip('_')
    return f"klodtalk_{name}"

def _normalize_external_paths(raw_list):
    """Normalize allowed_external_paths entries to [{"path": str, "writable": bool, "results": bool}, ...]."""
    result = []
    for entry in raw_list:
        if isinstance(entry, str):
            result.append({"path": entry, "writable": False, "results": False})
        elif isinstance(entry, dict) and "path" in entry:
            is_results = bool(entry.get("results", False))
            is_writable = bool(entry.get("writable", False)) or is_results
            result.append({"path": entry["path"], "writable": is_writable, "results": is_results})
        else:
            log.warning("Invalid allowed_external_paths entry, skipping: %s", entry)
    return result


def get_results_folder(project_config):
    """Return the path of the first results-designated external folder, or None."""
    for entry in _normalize_external_paths(project_config.get("allowed_external_paths", [])):
        if entry.get("results"):
            return entry["path"]
    return None


@dataclass
class Session:
    session_id: str
    project_name: str
    user_name: str
    git_branch: str
    workspace_path: str
    container_name: str
    status: str  # "active" | "closed"
    created_at: str
    closed_at: Optional[str] = None
    project_folder: str = ""  # original project folder
    docker_commit: bool = True
    docker_socket: bool = True


class SessionManager:
    def __init__(self):
        self._sessions: dict[str, Session] = {}
        self._counters: dict[str, int] = {}
        self._lock_file = os.path.join(STATE_DIR, ".sessions_lock")
        os.makedirs(CONFIG_DIR, exist_ok=True)
        os.makedirs(TEMP_BASE, exist_ok=True)
        self.load_sessions()
        self.load_counters()

    def load_sessions(self):
        if not os.path.isfile(SESSIONS_PATH):
            self._sessions = {}
            return
        try:
            with open(SESSIONS_PATH) as f:
                data = json.load(f)
            self._sessions = {k: Session(**v) for k, v in data.items()}
            log.info("Loaded %d sessions", len(self._sessions))
        except Exception as e:
            log.error("Failed to load sessions: %s", e)
            self._sessions = {}

    def save_sessions(self):
        try:
            with open(SESSIONS_PATH, "w") as f:
                json.dump(
                    {k: asdict(v) for k, v in self._sessions.items()},
                    f, indent=2
                )
        except Exception as e:
            log.error("Failed to save sessions: %s", e)

    def load_counters(self):
        if not os.path.isfile(COUNTERS_PATH):
            self._counters = {}
            return
        try:
            with open(COUNTERS_PATH) as f:
                self._counters = json.load(f)
        except Exception as e:
            log.error("Failed to load counters: %s", e)
            self._counters = {}

    def save_counters(self):
        try:
            with open(COUNTERS_PATH, "w") as f:
                json.dump(self._counters, f, indent=2)
        except Exception as e:
            log.error("Failed to save counters: %s", e)

    def next_branch_name(self, project_name: str) -> str:
        safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', project_name).lower()
        count = self._counters.get(project_name, 0) + 1
        self._counters[project_name] = count
        self.save_counters()
        return f"{safe_name}_{count:03d}"

    def create_session(self, project_name: str, user_name: str, project_config: dict) -> Optional[Session]:
        """Create a new session: copy workspace, create branch, start container."""
        folder = project_config.get("folder", "")
        if not folder:
            log.error("No folder in project config for '%s'", project_name)
            return None

        session_id = uuid.uuid4().hex[:8]
        branch_name = self.next_branch_name(project_name)
        temp_path = os.path.join(TEMP_BASE, session_id)
        cname = f"{CONTAINER_PREFIX}{session_id}"

        log.info("Creating session %s for project '%s' (branch=%s)", session_id, project_name, branch_name)

        repos = project_config.get("repos")

        # 1. Copy workspace
        try:
            os.makedirs(temp_path, exist_ok=True)
            if repos:
                for repo in repos:
                    src = os.path.join(folder.rstrip('/'), repo["path"])
                    dst = os.path.join(temp_path, repo["path"])
                    copy_git_tracked(src, dst)
            else:
                copy_git_tracked(folder, temp_path)
        except Exception as e:
            log.error("Failed to copy workspace: %s", e)
            return None

        # 2. Create and checkout new branch
        try:
            if repos:
                for repo in repos:
                    repo_path = os.path.join(temp_path, repo["path"])
                    if os.path.isdir(os.path.join(repo_path, ".git")):
                        subprocess.run(["git", "config", "user.name", "Claude Bot"], cwd=repo_path, capture_output=True)
                        subprocess.run(["git", "config", "user.email", "claude@bot.local"], cwd=repo_path, capture_output=True)
                        r = subprocess.run(
                            ["git", "checkout", "-b", branch_name],
                            cwd=repo_path, capture_output=True, text=True
                        )
                        if r.returncode != 0:
                            log.error("git checkout -b failed in '%s': %s", repo["path"], r.stderr)
                            # non-fatal, continue
            elif os.path.isdir(os.path.join(temp_path, ".git")):
                subprocess.run(["git", "config", "user.name", "Claude Bot"], cwd=temp_path, capture_output=True)
                subprocess.run(["git", "config", "user.email", "claude@bot.local"], cwd=temp_path, capture_output=True)
                r = subprocess.run(
                    ["git", "checkout", "-b", branch_name],
                    cwd=temp_path, capture_output=True, text=True
                )
                if r.returncode != 0:
                    log.error("git checkout -b failed: %s", r.stderr)
                    # non-fatal, continue without branch
        except Exception as e:
            log.error("git branch creation failed: %s", e)

        # 3. Ensure .klodTalk dirs exist
        for subdir in ("in_messages", "out_messages", "pr_messages", "history", "team/current"):
            os.makedirs(os.path.join(temp_path, ".klodTalk", subdir), exist_ok=True)

        # 4. Start Docker container
        if not self._start_session_container(cname, temp_path, project_config):
            log.error("Failed to start container for session %s", session_id)
            shutil.rmtree(temp_path, ignore_errors=True)
            return None

        session = Session(
            session_id=session_id,
            project_name=project_name,
            user_name=user_name,
            git_branch=branch_name,
            workspace_path=temp_path,
            container_name=cname,
            status="active",
            created_at=datetime.utcnow().isoformat() + "Z",
            project_folder=folder,
            docker_commit=project_config.get("docker_commit", True),
            docker_socket=project_config.get("docker_socket", True),
        )
        self._sessions[session_id] = session
        self.save_sessions()
        log.info("Session %s created (branch=%s, container=%s)", session_id, branch_name, cname)
        return session

    @staticmethod
    def _dp(path: str) -> str:
        """Normalise a host path for Docker volume mounts.

        Docker on Windows requires forward slashes in bind-mount specs.
        On Linux/macOS the path is returned unchanged.
        """
        return path.replace("\\", "/") if _IS_WINDOWS else path

    def _start_session_container(self, cname: str, workspace_path: str, project_config: dict) -> bool:
        """Start a Docker container for this session."""
        docker = get_docker_utils()

        docker_commit = project_config.get("docker_commit", True)
        docker_socket = project_config.get("docker_socket", True)

        # Determine image: use per-project image if docker_commit is enabled and image exists
        project_name = project_config.get("name", "unknown")
        image_to_use = DOCKER_IMAGE_NAME
        if docker_commit:
            per_project_image = sanitize_image_name(project_name)
            if docker.image_exists(per_project_image):
                image_to_use = per_project_image
                log.info("Using per-project image '%s' for project '%s'", per_project_image, project_name)
            else:
                log.info("No per-project image for '%s', using base '%s'", project_name, DOCKER_IMAGE_NAME)

        # Verify chosen image exists (with fallback)
        if not docker.image_exists(image_to_use):
            if image_to_use != DOCKER_IMAGE_NAME and docker.image_exists(DOCKER_IMAGE_NAME):
                log.warning("Per-project image '%s' not found, falling back to base", image_to_use)
                image_to_use = DOCKER_IMAGE_NAME
            else:
                log.error(
                    "Docker image '%s' not found. "
                    "Run the installer (helpers/windows/install.bat or helpers/linux/install.sh) "
                    "to build it.", DOCKER_IMAGE_NAME
                )
                return False
        base_branch = project_config.get("base_branch", "main")

        env_vars = [
            "-e", f"PROJECT_NAME={project_name}",
            "-e", f"BASE_BRANCH={base_branch}",
            # HOST_WORKSPACE_PATH is the real path of /workspace on the host.
            # Sibling containers (started via docker.sock) are launched by the host
            # Docker daemon, which sees the host filesystem — not the container's.
            # Use HOST_WORKSPACE_PATH (not /workspace) in any docker volume mounts.
            "-e", f"HOST_WORKSPACE_PATH={workspace_path}",
        ]
        for key in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY"):
            val = os.environ.get(key)
            if val:
                env_vars += ["-e", f"{key}={val}"]

        volume_mounts = ["-v", f"{self._dp(workspace_path)}:/workspace"]

        claude_config_dir = os.path.expanduser("~/.claude")
        if os.path.isdir(claude_config_dir):
            volume_mounts += ["-v", f"{self._dp(claude_config_dir)}:{CONTAINER_HOME}/.claude"]

        claude_config_file = os.path.expanduser("~/.claude.json")
        if os.path.isfile(claude_config_file):
            volume_mounts += ["-v", f"{self._dp(claude_config_file)}:{CONTAINER_HOME}/.claude.json"]

        ssh_dir = os.path.expanduser("~/.ssh")
        if os.path.isdir(ssh_dir):
            volume_mounts += ["-v", f"{self._dp(ssh_dir)}:{CONTAINER_HOME}/.ssh:ro"]


        for ext_entry in _normalize_external_paths(project_config.get("allowed_external_paths", [])):
            ext_path = ext_entry["path"]
            mount_mode = "rw" if ext_entry["writable"] else "ro"
            if os.path.exists(ext_path):
                if _IS_WINDOWS:
                    # Windows paths (e.g. D:\tmp\Klod) can't be used as Linux container paths.
                    # Mount to /ext/<basename> so the container can still access the files.
                    basename = os.path.basename(ext_path.rstrip("/\\")) or "ext"
                    container_path = f"/ext/{basename}"
                else:
                    container_path = self._dp(ext_path)
                volume_mounts += ["-v", f"{self._dp(ext_path)}:{container_path}:{mount_mode}"]
            else:
                log.warning("allowed_external_paths entry does not exist, skipping mount: %s", ext_path)

        gpu_args = []
        try:
            r = subprocess.run(["nvidia-smi"], capture_output=True)
            if r.returncode == 0:
                gpu_args = ["--gpus", "all"]
        except FileNotFoundError:
            pass

        user_args = [] if _IS_WINDOWS else ["--user", f"{HOST_UID}:{HOST_GID}"]

        if docker_socket:
            docker_sock = "/var/run/docker.sock"
            if os.path.exists(docker_sock):
                volume_mounts += ["-v", f"{docker_sock}:{docker_sock}"]
                try:
                    sock_gid = os.stat(docker_sock).st_gid
                    user_args += ["--group-add", str(sock_gid)]
                    # Pass GID so the entrypoint can register it in /etc/group,
                    # which makes docker CLI group-name resolution work correctly.
                    env_vars += ["-e", f"DOCKER_GID={sock_gid}"]
                except OSError as e:
                    log.warning("Could not stat docker socket: %s", e)
            else:
                log.error(
                    "docker_socket enabled for project '%s' but %s not found on host. "
                    "Ensure the Docker daemon is running on the host machine.",
                    project_config.get("name", "unknown"), docker_sock,
                )
                return False

        # On Linux, share the host network so the container inherits the host's
        # DNS resolver (systemd-resolved / VPN routing).  Without this, Docker
        # generates a broken /etc/resolv.conf that can't reach api.anthropic.com.
        # --network=host is not supported on Windows/macOS Docker Desktop.
        network_args = [] if _IS_WINDOWS else ["--network", "host"]

        success = docker.run_container(
            name=cname,
            image=image_to_use,
            volumes=volume_mounts,
            env_vars=env_vars,
            user_args=user_args,
            gpu_args=gpu_args,
            network_args=network_args,
        )
        if not success:
            log.error("Failed to start container '%s'", cname)
            return False
        log.info("Container '%s' started for session workspace", cname)
        return True

    def close_session(self, session_id: str) -> bool:
        """Close session: archive logs, stop container, remove temp dir."""
        session = self._sessions.get(session_id)
        if not session:
            log.warning("Session %s not found", session_id)
            return False
        if session.status == "closed":
            log.info("Session %s already closed", session_id)
            return True

        log.info("Closing session %s", session_id)

        # 1. Archive history from temp workspace to project folder
        if session.project_folder:
            archive_dir = os.path.join(
                session.project_folder, ".klodTalk", "sessions", session_id
            )
            os.makedirs(archive_dir, exist_ok=True)
            src_history = os.path.join(session.workspace_path, ".klodTalk", "history")
            if os.path.isdir(src_history):
                try:
                    for fname in os.listdir(src_history):
                        shutil.copy2(os.path.join(src_history, fname), os.path.join(archive_dir, fname))
                    log.info("Archived history to %s", archive_dir)
                except Exception as e:
                    log.error("Failed to archive history: %s", e)

        # 2. Docker commit (before container removal)
        docker = get_docker_utils()
        if session.docker_commit:
            per_project_image = sanitize_image_name(session.project_name)
            # Only commit if this is the last active session for this project
            active_for_project = [
                s for s in self._sessions.values()
                if s.project_name == session.project_name
                and s.status == "active"
                and s.session_id != session_id
            ]
            if not active_for_project:
                try:
                    if docker.is_container_running(session.container_name):
                        log.info("Committing container '%s' as '%s'",
                                 session.container_name, per_project_image)
                        if docker.commit_container(session.container_name, per_project_image):
                            size = docker.get_image_size(per_project_image)
                            if size and size > 5 * 1024 * 1024 * 1024:  # 5 GB
                                log.warning(
                                    "Per-project image '%s' is %.1f GB -- consider pruning",
                                    per_project_image, size / (1024 * 1024 * 1024)
                                )
                            else:
                                size_str = f"{size / (1024 * 1024):.0f} MB" if size else "unknown size"
                                log.info("Committed image '%s' (%s)", per_project_image, size_str)
                        else:
                            log.warning("Docker commit failed for '%s' -- non-fatal",
                                        session.container_name)
                    else:
                        log.warning("Container '%s' not running, skipping commit",
                                    session.container_name)
                except Exception as e:
                    log.error("Docker commit error (non-fatal): %s", e)
            else:
                log.info("Skipping commit -- %d other active session(s) for '%s'",
                         len(active_for_project), session.project_name)

        # 3. Stop and remove container
        docker.stop_container(session.container_name)
        log.info("Container '%s' removed", session.container_name)

        # 4. Keep temp workspace (removed on delete, not close)

        # 5. Update session record
        session.status = "closed"
        session.closed_at = datetime.utcnow().isoformat() + "Z"
        self.save_sessions()
        return True

    def get_session(self, session_id: str) -> Optional[Session]:
        return self._sessions.get(session_id)

    def get_active_sessions(self) -> list[Session]:
        return [s for s in self._sessions.values() if s.status == "active"]

    def get_user_sessions(self, user_name: str, project_configs: list[dict]) -> list[Session]:
        """Return all sessions the user can access (own + allowed projects)."""
        # User can see sessions for projects they're allowed on
        allowed_projects: set[str] = set()
        for pc in project_configs:
            if user_name in pc.get("users", []):
                allowed_projects.add(pc["name"])
        return [
            s for s in self._sessions.values()
            if s.project_name in allowed_projects
        ]

    def get_archive_path(self, session: Session) -> str:
        """Return the archived history path for a closed session."""
        if session.project_folder:
            return os.path.join(session.project_folder, ".klodTalk", "sessions", session.session_id)
        return ""

    def reopen_session(self, session_id: str, project_config: dict) -> bool:
        """Reopen a closed session: start a new container with the same workspace."""
        session = self._sessions.get(session_id)
        if not session:
            log.warning("Reopen: session %s not found", session_id)
            return False
        if session.status != "closed":
            log.warning("Reopen: session %s is not closed (status=%s)", session_id, session.status)
            return False
        if not os.path.isdir(session.workspace_path):
            log.error("Reopen: workspace %s no longer exists", session.workspace_path)
            return False

        cname = f"{CONTAINER_PREFIX}{session_id}"
        log.info("Reopening session %s (container=%s)", session_id, cname)

        if not self._start_session_container(cname, session.workspace_path, project_config):
            log.error("Failed to start container for reopened session %s", session_id)
            return False

        session.container_name = cname
        session.status = "active"
        session.closed_at = None
        self.save_sessions()
        log.info("Session %s reopened (container=%s)", session_id, cname)
        return True

    def delete_session(self, session_id: str) -> bool:
        """Permanently remove a session record and its workspace from disk."""
        if session_id not in self._sessions:
            return False
        session = self._sessions[session_id]
        # Remove temp workspace directory
        if session.workspace_path and os.path.isdir(session.workspace_path):
            shutil.rmtree(session.workspace_path, ignore_errors=True)
            log.info("Removed temp workspace %s", session.workspace_path)
        del self._sessions[session_id]
        self.save_sessions()
        return True

    def cleanup_orphaned_sessions(self):
        """On startup, close sessions whose containers are gone."""
        docker = get_docker_utils()
        for session in list(self._sessions.values()):
            if session.status != "active":
                continue
            running = docker.is_container_running(session.container_name)
            if not running:
                log.info("Session %s has no running container — marking closed", session.session_id)
                session.status = "closed"
                session.closed_at = datetime.utcnow().isoformat() + "Z"
                # Keep temp workspace (removed on delete, not close)
        self.save_sessions()
