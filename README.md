# KlodTalk - My favorite way to talk to Claude.

A multi-agent system built on Claude Code CLI. Define teams of Claude agents with different roles (Planner, Coder, Reviewer, etc.), assign them to projects, and let them collaborate on tasks — all running inside Docker containers on your local machine.

## Why KlodTalk?

- **Configurable teams** — define pipelines in Markdown files. Swap roles, models, and review loops without touching code.
- **Docker-isolated** — every session runs in its own container. Each task gets a dedicated git branch. Your host system stays clean.
- **Multi-user, multi-session** — multiple people can use the system concurrently, each with their own projects and sessions.
- **Confirm vs. execute modes** — ask Claude to confirm what it understood before it starts coding, or go straight to execution.
- **Full work logging** — every team step is logged with plans, code changes, reviews, and progress updates. Easy to inspect and audit.
- **Web and Android clients** — connect from a browser or the native Android app. iOS contributions welcome.
- **HTTP/HTTPS and WS/WSS** — supports both plain and TLS-encrypted connections.
- **Speech-to-text option** — both clients support voice input for hands-free interaction.
- **Linux and Windows** — installers and helper scripts for both. macOS contributions welcome.

## How It Works

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
     ├── Starts a Docker container for the session
     ├── Runs the team pipeline (or single agent) inside the container
     ├── Streams progress updates back to the client
     └── Returns the final result
     │
     ▼
Docker Container
     │
     ├── Claude Code CLI (with your team pipeline)
     ├── Git branch per task
     └── Logged output at every step
```

## Installation

### Prerequisites

- **Docker** — agent containers run here
- **Python 3.9+** — the server runtime
- **Git** — workspace management
- **Claude Code CLI** — the AI agent engine (see [Claude Code setup](#claude-code-setup) below)

### Quick Install

## Ask Claude to do it...

**Linux:**

```bash
git clone <repo-url> klodTalk
cd klodTalk
bash helpers/linux/install.sh
```

**Windows** (run as Administrator):

```
git clone <repo-url> klodTalk
cd klodTalk
helpers\windows\install.bat
```

Both installers handle Docker installation, Python venv setup, example config copying, and Docker image build. They are idempotent — safe to re-run.

### Manual Setup (alternative)

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r server/requirements.txt
cp config/projects.json.example config/projects.json
cp config/users.json.example config/users.json
```

### Claude Code Setup

KlodTalk uses Claude Code CLI as the AI engine inside Docker containers. You need it authenticated on the host machine — the server mounts the session into containers.

1. **Install Claude Code CLI:**

```bash
npm install -g @anthropic-ai/claude-code
```

2. **Authenticate** (two options):

   - **OAuth session** (default) — run `claude` once on the host, complete the browser login, then close it. The session token is stored in `~/.claude/` and mounted into containers automatically.

   - **API key** — set the `ANTHROPIC_API_KEY` environment variable and change `config/server_config.yaml`:

```yaml
claude:
  auth_method: "api_key"
```

The server checks for a valid Claude session on startup and re-authenticates if needed.

## Configuration

### Users (`config/users.json`)

Users authenticate to the server with a username and password hash. Manage users with the CLI helper:

```bash
# Add a user (prompts for password)
python helpers/add_user.py add alice

# List users
python helpers/add_user.py list

# Interactive mode
python helpers/add_user.py
```

Passwords are SHA-256 hashed client-side before transmission. The server stores and compares hashes, never plaintext.

### Projects (`config/projects.json`)

Each project maps to a workspace folder on your machine. A project defines who can access it, which team pipeline to use, and what branch to base work on.

```bash
# Add a project
python helpers/add_project.py add my_project \
    --users alice \
    --description "Backend API work" \
    --folder /home/alice/projects/backend

# Add a shared project for multiple users
python helpers/add_project.py add shared_project \
    --users alice bob \
    --description "Shared frontend project" \
    --folder /home/alice/projects/frontend
```

Key project fields in `config/projects.json`:

| Field | Description |
|-------|-------------|
| `name` | Project identifier |
| `users` | List of usernames allowed to use this project |
| `folder` | Absolute path to the project workspace on the host |
| `base_branch` | Branch merged before each task (default: `"main"`) |
| `team` | Team pipeline name (e.g. `"plan-code-review"`) or `null` for single-agent mode |
| `docker_commit` | Whether to auto-commit inside the container |
| `docker_socket` | Whether to mount the Docker socket into the container |
| `allowed_external_paths` | Additional host paths to mount into the container (read-only or read-write) |

See `config/projects.json.example` for a full example.

## Starting the Server

**Linux:**

```bash
./helpers/linux/run_server.sh
```

**Windows:**

```
helpers\windows\run_server.bat
```

The server binds to `0.0.0.0:3174` by default (configurable in `config/server_config.yaml`).

## Connecting Clients

**Web client** — open `clients/web/index.html` in a browser on the same network, or serve it with any static file server. Enter the server IP, port, username, and password.

**Android app** — build the APK and install it:

```bash
./helpers/linux/compile_apk.sh        # debug APK → build/
```

Open the app, enter your server connection details, and tap Connect.

## Team Pipelines

Teams are the core of KlodTalk. A team is a Markdown file that defines a pipeline of Claude agents with different roles.

### Available Teams

| Team | Description |
|------|-------------|
| `plan-code-review` | Default balanced pipeline: Planner → Coder → Reviewer (with optional execution, validation, and security review) |
| `plan-code` | Fast two-role path: Planner → Coder, no review step |
| `plan-code-review-execute` | Five-role pipeline with execution and validation after review |
| `tdd` | Test-driven development with red-green-refactor methodology |
| `unit-test` | Write unit tests for existing code without modifying implementation |
| `refactor` | Two-phase refactoring: refactor code, then validate with tests |
| `security` | Security-focused — uses Opus throughout for deeper threat analysis |
| `optimizer` | Iterative optimization loop for tuning configuration or code against a metric |
| `super-planner` | Ideation-only team that generates and refines plans without writing code |

### Creating a Custom Team

Create a Markdown file in `teams/teams/`:

# Team: My Team

A description of what this team does.

## Members

| Name     | Role     | Model | Optional |
|----------|----------|-------|----------|
| coder    | coder    | opus  |          |
| reviewer | reviewer | haiku |          |
| runner   | executor | opus  | yes      |

## Pipeline

1. **coder**: Implements the plan.
2. **reviewer**: Reviews the implementation.
   - Review loop: fix_role=coder, max_iterations=2
3. **runner**: Execute the implementation if orchestrator thinks it is needed.

Assign it to a project by setting `"team": "my-team"` in `config/projects.json`. See `docs/add_team.md` for the full guide.

**You can always change the team for each message in the client's interface.**
### Available Models

- **`opus`** (claude-opus-4-6) — most capable, highest cost
- **`sonnet`** (claude-sonnet-4-6) — balanced capability and speed
- **`haiku`** (claude-haiku-4-5-20251001) — fastest and cheapest

## Confirm vs. Execute Modes

KlodTalk has two interaction modes to prevent premature execution:

| Mode | What Happens |
|------|-------------|
| **Confirm** | Claude reads the accumulated messages and summarises what it understood. No code changes. |
| **Execute** | Claude runs the full team pipeline (or single agent) on the request. |

## Work Logging

Every team pipeline run produces detailed logs:

- **Progress updates** — real-time step-by-step progress (e.g. "Step 2/4: Coder implementing...") pushed to the client as the pipeline runs.
- **Plan** — the planner's full implementation plan, visible before coding starts.
- **Coder output** — summary of what was implemented and which files changed.
- **Review results** — the reviewer's findings, displayed in a separate Reviews tab.
- **Orchestrator log** — full verbatim output from every sub-agent, written to `.klodTalk/history/orchestrator_log.md` in the workspace.
- **Changed files** — list of all modified files, written to `.klodTalk/changed_files.txt`.

## TLS / WSS Setup (Optional)

KlodTalk supports encrypted connections using self-signed TLS certificates. Both plain (`ws://`, `http://`) and encrypted (`wss://`, `https://`) modes work.

### Generate a Certificate

**Linux:**

```bash
./helpers/linux/generate_cert.sh
# Enter your server's LAN IP when prompted
# Generates server.crt and server.key in ~/.KlodTalk/certs/
```

**Windows:**

```
helpers\windows\generate_cert.bat
```

### Configure the Server

Edit `config/server_config.yaml`:

```yaml
server:
  host: "0.0.0.0"
  port: 3174
  docker: true
  ssl_cert: "/home/youruser/.KlodTalk/certs/server.crt"
  ssl_key: "/home/youruser/.KlodTalk/certs/server.key"
```

### Trust the Certificate on Clients

**Web browser:** navigate to `https://<server-ip>:<port>` and accept the self-signed cert, then switch the web client to `wss://`.

**Android:** install the `server.crt` as a CA certificate on the device (Settings → Security → Install a certificate), then select `wss://` in the app settings.

WSS is recommended if your LAN has untrusted devices, but not required. On a trusted home network, `ws://` works fine.

## Project Structure

```
klodTalk/
├── config/                        # Server config, user/project definitions
│   ├── server_config.yaml
│   ├── projects.json.example
│   └── users.json.example
├── server/                        # WebSocket server & Docker agent runtime
│   ├── server.py                  # Main WebSocket server
│   ├── session_manager.py         # Session lifecycle & container management
│   ├── run_agent.py               # Agent executor (runs inside container)
│   ├── run_agent.sh               # Shell-based agent executor
│   ├── Dockerfile.agent           # Agent container image
│   ├── agent_entrypoint.sh        # Container entrypoint
│   ├── history_store.py           # Session history (JSONL)
│   ├── token_store.py             # Token usage tracking
│   ├── unread_state.py            # Per-user unread markers
│   ├── copy_tree.py               # Git-aware directory copy
│   └── utils/                     # Shared utilities (file, git, docker, etc.)
├── teams/                         # Multi-agent team orchestration
│   ├── orchestrator.md            # Master orchestration instructions
│   ├── run_claude_team.sh         # Entry point (shell → Claude)
│   ├── teams/                     # Team pipeline definitions (Markdown)
│   │   ├── plan-code-review.md
│   │   ├── plan-code.md
│   │   ├── tdd.md
│   │   └── ...
│   └── roles/                     # Role instruction files (Markdown)
│       ├── planner.md
│       ├── coder.md
│       ├── reviewer.md
│       └── ...
├── clients/
│   ├── web/
│   │   └── index.html             # Browser client (vanilla JS, zero deps)
│   ├── android/                   # Android app (Kotlin / Jetpack Compose)
│   └── ios/                       # Placeholder — contributions welcome
├── helpers/
│   ├── add_user.py                # User management CLI
│   ├── add_project.py             # Project management CLI
│   ├── linux/                     # Linux scripts (install, run, build, certs)
│   └── windows/                   # Windows scripts (install, run, build, certs)
├── tests/                         # Unit tests (pytest)
├── docs/                          # Documentation
└── CLAUDE.md
```

## Privacy Policy

KlodTalk runs entirely on your local network. The Android app and web client connect only to your self-hosted server — no data is sent to external services.

- No analytics, tracking, or advertising SDKs.
- No audio is recorded or transmitted. The microphone is used solely for Android's on-device speech recognizer; only the resulting text is sent to your server.
- No crash reporting to external services.
- Connection settings are stored locally on the device and never leave it.

Full privacy policy: `docs/privacy_policy.html`

## Security

KlodTalk is a local-network tool. Do not expose the server port to the internet. See `SECURITY.md` for the full threat model and recommendations.

## Contributing

Contributions welcome — especially macOS support and an iOS client. See `CONTRIBUTING.md` for setup instructions and guidelines.

## License

MIT
