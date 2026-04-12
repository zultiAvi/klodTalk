# KlodTalk

A voice-first system for talking to AI agents. You speak into your phone (or browser), the speech is transcribed to text, sent over WebSocket to a server on your computer, which routes it to a Docker-containerized agent (Claude Code CLI). The agent's response flows back to you.

The core idea: **voice in, text out, agents do the work**. No typing, no switching windows. You talk to your agents from anywhere on your local network.

## Architecture

```
Phone / Browser
     │  (speech → text)
     │
     ▼
WebSocket (wss://computer:9000)
     │
     ▼
Server (Python asyncio)
     │
     ├── Authenticates user (users.json)
     ├── Appends text to project folder (in_messages/in_message.txt)
     ├── "read back"    → runs Claude in confirm mode → returns understanding
     ├── "start working" → runs Claude in execute mode → returns result
     ├── Polls for project output (out_messages/)
     └── Pushes response back to all connected users of that project
```

## Key Design Decisions

- **File-based project I/O** (`in_message.txt` / `out_message.txt`): Projects are decoupled from the server. Any agent — Claude, a custom script, anything — just reads a file and writes a file. No API integration needed inside the server.
- **Docker isolation**: Each agent runs in its own container with its workspace mounted. Agents can't interfere with each other or the host system beyond their folder.
- **Multi-user, multi-project**: Users are authenticated independently. Agents have a list of allowed users. Multiple users can share an agent, or have private ones.
- **Web-based Claude auth**: No API keys needed. The server authenticates Claude Code CLI via browser OAuth at startup and mounts the session into containers.
- **Two clients, same protocol**: Android app and web client speak the exact same WebSocket JSON protocol. Either can be used interchangeably.
- **Git workflow**: Before executing, Claude merges the configured `base_branch` into the current branch. Claude does not commit or push — that is left to the human.

## Voice Trigger Phrases

| Phrase | Effect |
|--------|--------|
| `read back` | Claude summarises what it understood — no code changes. Useful for confirming garbled voice input. |
| `start working` | Claude executes the accumulated request. |

**Typical flow:**
1. Say your request (one or more messages).
2. Say "read back" — Claude replies with what it understood.
3. Say "start working" to proceed, or correct yourself and say "read back" again.

## Folder Guide

- **[server/](server/CLAUDE.md)** — The WebSocket server and Docker agent runtime: message broker, container management, Claude authentication, utility abstractions.
- **[clients/](clients/CLAUDE.md)** — Client applications: Android (Kotlin), web browser (HTML), iOS (placeholder).
- **[teams/](teams/CLAUDE.md)** — Multi-agent team pipelines: team definitions (`.md`), role prompts, orchestration scripts.
- **[config/](config/CLAUDE.md)** — Runtime configuration: server settings, user/project definitions.
- **[helpers/](helpers/CLAUDE.md)** — CLI tools for managing users, projects, building the APK, and running the server.
- **[docs/](docs/)** — Installation guide, architecture overview, development guide, team creation guide.
- **[tests/](tests/)** — Unit tests for server components and utility abstractions.

## Message Protocol (JSON over WebSocket)

| Direction | Type | Fields |
|-----------|------|--------|
| Client → Server | `hello` | `name`, `password_hash` |
| Server → Client | `projects` | `projects` (list of `{name, description}`) |
| Client → Server | `text` | `project`, `content` |
| Server → Client | `response` | `project`, `content` |
