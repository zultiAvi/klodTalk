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

## Code Quality Rules

All code added to this repo must follow these conventions:

1. **Max 1024 lines per file.** Split modules that grow past this — by class, by concern, or by layer.
2. **1–2 classes per file.** Helpers and inner types are fine; multiple top-level public classes are not.
3. **Behaviors in classes.** When functions share state or operate on the same data, wrap them in a class. Use module-level functions only for pure stateless utilities.
4. **Minimize environment variables.** Read env vars at most at startup, inside a single config loader. Application code receives parsed config objects — never reads `os.environ` directly.
5. **Dataclasses over dicts.** Use `@dataclass` (or `pydantic.BaseModel` where present) for structured records with a known shape. Reserve plain dicts for genuinely-dynamic key/value maps.
6. **No `getattr(obj, "field", default)` for known fields.** Declare the field on the dataclass with a default. `getattr` with a default masks missing-field bugs.
7. **Few inline comments.** Names and structure carry intent. Comments explain *why*, never *what*.

See `CLAUDE/skills/dataclass-over-dict-getattr.md` for rules #5 and #6 patterns.

## Message Protocol (JSON over WebSocket)

| Direction | Type | Fields |
|-----------|------|--------|
| Client → Server | `hello` | `name`, `password_hash` |
| Server → Client | `projects` | `projects` (list of `{name, description}`) |
| Client → Server | `text` | `session_id`, `content`, `mode` |
| Server → Client | `response` | `session_id`, `content` |
| Client → Server | `btw` | `session_id`, `content` |
