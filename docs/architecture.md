# Architecture Overview

## Data Flow

```
Phone / Browser (voice → text)
       │
       ▼
WebSocket (wss://server:port)
       │
       ▼
Server (Python asyncio)
       │
       ├── Authenticates user (config/users.json)
       ├── Manages sessions (Docker containers)
       ├── Writes text to .klodTalk/in_messages/in_message.txt
       ├── Triggers agent via docker exec
       ├── Polls .klodTalk/out_messages/ for responses
       └── Broadcasts response to connected clients
       │
       ▼
Docker Container (agent)
       │
       ├── run_agent.py (confirm/execute/review modes)
       ├── Claude Code CLI
       └── Team pipeline (optional: planner → coder → reviewer)
```

## Directory Layout

| Directory | Purpose |
|-----------|---------|
| `server/` | WebSocket server, agent runtime, Docker config |
| `clients/android/` | Android app (Kotlin/Jetpack Compose) |
| `clients/web/` | Browser client (single HTML file) |
| `clients/ios/` | iOS placeholder |
| `teams/teams/` | Team pipeline definitions (`.md` files) |
| `teams/roles/` | Role instruction files (`<name>.md`) |
| `teams/run_claude_team.sh` | Claude team orchestrator entry point |
| `config/` | Server config, user/project definitions |
| `helpers/` | CLI tools, installers, build scripts |
| `.klodTalk/state/` | Runtime state (gitignored) |

## Key Design Decisions

- **File-based project I/O**: Agents read `in_message.txt` and write `out_message.txt`. Any agent — Claude, a script, anything — just reads and writes files.
- **Docker isolation**: Each session gets its own container with the workspace mounted.
- **Utility abstraction**: OS, Git, Claude auth, and Docker operations are abstracted behind factory patterns in `server/utils/`. Configured via `config/server_config.yaml`.
- **Two modes**: "read back" (confirm/summarize) and "start working" (execute).

## Authentication

Configured in `config/server_config.yaml` under `claude.auth_method`:
- `session` — OAuth via browser (default, uses `~/.claude` tokens)
- `api_key` — `ANTHROPIC_API_KEY` environment variable

## State Management

Runtime state lives in `.klodTalk/state/` (gitignored):
- `sessions.json` — active/closed session records
- `session_counters.json` — branch name counters per project
- `unread_state.json` — per-user unread message tracking
