# server/

The WebSocket server and Docker agent runtime. This is the brain of the system — it brokers messages between clients and projects.

## Architecture

**The server is a message broker, not an AI runtime.** It receives text from clients, writes it to a file in the project's folder, and polls for output. Agents can be anything: Claude Code CLI, a custom script, a bash pipeline.

**File-based I/O.** Message files live under `.klodTalk/` in each workspace. The server writes `in_messages/in_message.txt` and reads from `out_messages/` and `pr_messages/`.

**Docker containers for isolation.** Each project's folder is mounted into a container that stays alive (idle) waiting for `docker exec` calls.

**Three modes:** "Read Back" (confirm/summarize), "Start Working" (execute), and "BTW" (side-channel message to a running agent).

## Files

- **server.py** — WebSocket message broker, client auth, project orchestration, Claude session management
- **run_agent.py** — Agent executor (runs inside container via `docker exec`)
- **run_agent.sh** — Shell-based agent executor (legacy, still supported)
- **session_manager.py** — Session lifecycle: workspace copy, branch creation, container management
- **history_store.py** — Session history in JSONL format
- **session_log.py** — Durable per-session log directory at `/tmp/klodTalk/<session_id>.klodTalk/`, populated by every server event (user/BTW messages, progress/planner/coder/review/idea broadcasts, agent stdout/stderr, lifecycle events, errors). Survives `delete_session` so closed/deleted sessions still show their history. Read on reopen via `session_replay`. Hook events from `post_tool_use_logger.sh` are tailed by the watcher and written to a sibling file `hook_events.jsonl` inside the same per-session directory via `append_hook_event`. They are intentionally **not** written to `events.jsonl` / `log.txt` so they don't pollute the user-visible chat replay. The "Logs" button in the UI (`get_agent_logs`) reads from Claude's own JSONL archives and is unrelated to this sink.
- **token_store.py** — Cumulative token usage tracking
- **unread_state.py** — Per-user unread message tracking
- **copy_tree.py** — Git-aware directory copy utility
- **Dockerfile.agent** — Agent container image (Ubuntu + CUDA + Node.js + Claude CLI)
- **agent_entrypoint.sh** — Container entrypoint (idles waiting for tasks)

## utils/

Shared utilities, both bash libraries (sourced by team scripts) and Python abstraction packages.

### Bash utilities (used by team scripts)
- `file_utils.sh` — File path constants and read/write helpers
- `git_utils.sh` — Git operations (commit, branch, changed files)
- `history_utils.sh` — Structured logging
- `progress_utils.sh` — Progress message broadcasting
- `token_utils.sh` — Token tracking helpers

### Python utilities (server-side equivalents)
- `file_utils.py` — File path constants and read/write helpers
- `git_utils.py` — Git operations
- `history_utils.py` — Structured logging
- `progress_utils.py` — Progress message broadcasting

### Python abstraction packages
- `claude_auth/` — Claude authentication: `session` (OAuth) or `api_key`. Factory: `get_claude_auth()`
- `os/` — OS utilities: Linux implementation. Factory: `get_os_utils()`
- `git/` — Git protocol: SSH (working) or HTTPS (stub). Factory: `get_git_utils()`
- `docker/` — Docker operations: local CLI. Factory: `get_docker_utils()`

Each package follows the pattern: `base.py` (abstract), `<impl>.py` (concrete), `__init__.py` (factory).
