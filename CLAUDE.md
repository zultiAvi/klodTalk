# KlodTalk

A multi-agent system built on Claude Code CLI. Define teams of Claude agents with different roles (Planner, Coder, Reviewer, etc.), assign them to projects, and let them collaborate on tasks — all running inside Docker containers on your local machine.

## Architecture

```
Client (Web / Android)
     │  text or speech-to-text
     │
     ▼
WebSocket (ws:// or wss://)
     │
     ▼
Server (Python asyncio)
     │
     ├── Authenticates user (users.json)
     ├── Routes message to the correct session
     ├── "Read Back"     → runs Claude in confirm mode → returns understanding
     ├── "Start Working" → runs Claude in execute mode → returns result
     ├── "BTW"           → sends side-channel message to a running agent
     ├── Streams progress updates back to the client
     └── Returns the final result
```

## Key Design Decisions

- **File-based project I/O** (`in_message.txt` / `out_message.txt`): Projects are decoupled from the server. Any agent — Claude, a custom script, anything — just reads a file and writes a file. No API integration needed inside the server.
- **Docker isolation**: Each agent runs in its own container with its workspace mounted. Agents can't interfere with each other or the host system beyond their folder.
- **Multi-user, multi-project**: Users are authenticated independently. Projects have a list of allowed users. Multiple users can share a project, or have private ones.
- **Web-based Claude auth**: No API keys needed. The server authenticates Claude Code CLI via browser OAuth at startup and mounts the session into containers.
- **Two clients, same protocol**: Android app and web client speak the exact same WebSocket JSON protocol. Either can be used interchangeably.
- **Git workflow**: Before executing, Claude merges the configured `base_branch` into the current branch. Claude does not commit or push — that is left to the human.

## Interaction Modes

| Mode | Effect |
|------|--------|
| **Read Back** | Claude summarises what it understood — no code changes. Use to verify understanding or ask questions. |
| **Start Working** | Claude executes the accumulated request using the team pipeline (or single agent). |
| **BTW** | Send a side-channel message to Claude while it's already working. Adds context without interrupting the pipeline. |

**Typical flow:**
1. Send your request (one or more messages).
2. Hit "Read Back" — Claude replies with what it understood.
3. Hit "Start Working" to proceed, or correct yourself and hit "Read Back" again.
4. While Claude is working, use "BTW" to send additional context if needed.

## Folder Guide

- **[server/](server/CLAUDE.md)** — The WebSocket server and Docker agent runtime: message broker, container management, Claude authentication, utility abstractions.
- **[clients/](clients/CLAUDE.md)** — Client applications: Android (Kotlin), web browser (HTML), iOS (placeholder).
- **[teams/](teams/CLAUDE.md)** — Multi-agent team orchestration: team definitions (`.md`), role prompts, orchestration scripts.
- **[config/](config/CLAUDE.md)** — Runtime configuration: server settings, user/project definitions.
- **[helpers/](helpers/CLAUDE.md)** — CLI tools for managing users, projects, building the APK, and running the server.
- **[docs/](docs/)** — Installation guide, architecture overview, development guide, team creation guide.
- **[tests/](tests/)** — Unit tests for server components and utility abstractions.

## Message Protocol (JSON over WebSocket)

| Direction | Type | Fields |
|-----------|------|--------|
| Client → Server | `hello` | `name`, `password_hash` |
| Server → Client | `projects` | `projects` (list of `{name, description}`) |
| Client → Server | `text` | `session_id`, `content`, `mode` |
| Server → Client | `response` | `session_id`, `content` |
| Client → Server | `btw` | `session_id`, `content` |
