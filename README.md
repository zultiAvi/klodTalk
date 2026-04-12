# KlodTalk

### My favorite way to talk to Claude.

You talk. Claude codes. Your entire team of AI agents — Planner, Coder, Reviewer — works together inside isolated Docker containers while you watch the progress from your phone or browser. When they're done, you review the diff, approve or revert changes, and move on.

No terminal. No copy-pasting. Just say what you want built.

---

## What Makes This Different

Most AI coding tools give you one agent in one window. KlodTalk gives you a **team** — a configurable pipeline of specialized Claude agents that plan, implement, review, and even run your code. Everything happens in Docker, on a fresh git branch, so your codebase stays safe.

- **Teams of agents, not just one** — a Planner designs the approach, a Coder writes the code, a Reviewer catches mistakes. You pick the team, or build your own.
- **Easy to configure** — teams and roles are just Markdown files. Add a new team, tweak a role's instructions, or change which model a role uses — no code changes, no restarts.
- **Docker-isolated** — every session runs in its own container with its own git branch. Nothing touches your working tree until you say so.
- **Diff window** — when Claude finishes, you see exactly what changed. Review every hunk, revert what you don't like, keep what you do.
- **Read Back / Start Working / BTW** — tell Claude to summarise what it understood before coding, kick off execution when ready, or send a "BTW" with extra context while it's mid-task.
- **Auto-learning** — KlodTalk automatically reviews its own sessions and writes CLAUDE.md skill files into your project, so Claude gets smarter about your codebase over time.
- **Voice or text** — speak into your phone or type in the browser. Both clients support speech-to-text.
- **Multi-user, multi-project** — your team can share projects or have private ones. Multiple sessions run in parallel.
- **Web and Android clients** — same protocol, same features. iOS contributions welcome.
- **Linux and Windows** — installers for both. macOS contributions welcome.

---

## Getting Started

**The easiest way to learn KlodTalk is to ask Claude.** The entire repo is documented with `CLAUDE.md` files in every directory — Claude already knows how everything works. Once you're set up, just ask it.

### Prerequisites

- **Docker** — agent containers run here
- **Python 3.9+** — the server runtime
- **Git** — workspace management
- **Claude Code CLI** — the AI engine ([setup instructions below](#claude-code-setup))

### Quick Install

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

Both installers handle Docker, Python venv, config files, and the Docker image. Idempotent — safe to re-run.

### Claude Code Setup

KlodTalk uses Claude Code CLI inside Docker containers. You need it authenticated on the host — the server mounts the session into containers.

1. **Install:**

```bash
npm install -g @anthropic-ai/claude-code
```

2. **Authenticate** (pick one):

   - **OAuth session** (default) — run `claude` once, complete the browser login, close it. Done.
   - **API key** — set `ANTHROPIC_API_KEY` and change `config/server_config.yaml`:

```yaml
claude:
  auth_method: "api_key"
```

### Add Users and Projects

```bash
python helpers/add_user.py add alice

python helpers/add_project.py add my_project \
    --users alice \
    --description "Backend API" \
    --folder /home/alice/projects/backend
```

See `config/projects.json.example` for all available options.

### Start the Server

```bash
./helpers/linux/run_server.sh          # Linux
helpers\windows\run_server.bat         # Windows
```

The server binds to `0.0.0.0:3174` by default (configurable in `config/server_config.yaml`).

### Connect

**Web** — open `clients/web/index.html` in a browser on the same network.

**Android** — build and install the APK:

```bash
./helpers/linux/compile_apk.sh
```

---

## How It Works

```
You (Web / Android)
     │
     ├── Log in to your server
     ├── Open a session for one of your projects
     ├── Pick the right team for your task
     ├── Ask Claude to do some work
     │
     ▼
Server
     │
     ├── Spins up a Docker container
     ├── Clones your repo into /workspace
     ├── Creates a fresh git branch
     ├── Runs the team pipeline (Planner → Coder → Reviewer → ...)
     ├── Streams progress updates back to you
     ├── Commits code changes to the branch
     │
     ▼
You
     │
     ├── Review the diff — approve or revert individual changes
     ├── Send follow-up messages or corrections
     ├── Close the session when done
```

---

## Interaction Modes

| Mode | What Happens |
|------|-------------|
| **Read Back** | Claude summarises what it understood from your messages. No code changes. Use this to verify understanding or ask questions before committing to execution. |
| **Start Working** | Claude runs the full team pipeline on your request. |
| **BTW** | Send a side-channel message while Claude is already working — add context, corrections, or clarifications without interrupting the pipeline. |

**Typical flow:**

1. Send your request (one or more messages, text or voice).
2. Hit **Read Back** — Claude tells you what it understood.
3. If it got it right, hit **Start Working**. If not, correct and Read Back again.
4. While Claude is working, use **BTW** if you forgot something.

---

## Teams

Teams are the heart of KlodTalk. Each team is a simple Markdown file that defines a pipeline of agents.

### Built-in Teams

| Team | What It Does |
|------|-------------|
| `plan-code-review` | The default. Planner → Coder → Reviewer, with optional execution and security review. |
| `plan-code` | Fast path. Planner → Coder, no review. |
| `plan-code-review-execute` | Full pipeline with execution and validation after review. |
| `tdd` | Test-driven development — red, green, refactor. |
| `unit-test` | Writes unit tests for existing code. Doesn't touch implementation. |
| `refactor` | Refactors code, then validates with tests. |
| `security` | Security-focused. Uses Opus throughout for deeper analysis. |
| `optimizer` | Iterative optimization loop against a metric. |
| `super-planner` | Ideation only — generates and refines plans, writes no code. |

You can switch the team for any message in the client interface.

### Create Your Own

Teams and roles are just Markdown files — no code, no config syntax. Want a new team? Drop a `.md` file. Want to change how the Reviewer behaves? Edit `teams/roles/reviewer.md`. Want the Coder to use a cheaper model? Change one word in the Members table. No restarts needed.

# New Team ?

Drop a Markdown file in `teams/teams/`:

## Team: My_Team

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
3. **runner**: Execute the implementation if team's orchestrator thinks it is needed.

Assign it to a project with `"team": "my-team"` in `config/projects.json`. See `docs/add_team.md` for the full format.

### Available Models

- **`opus`** (claude-opus-4-6) — most capable
- **`sonnet`** (claude-sonnet-4-6) — balanced
- **`haiku`** (claude-haiku-4-5-20251001) — fastest and cheapest


# New role ?

Drop a Markdown file in `teams/roles/`:

### Role: New_role

Describe new_role **statement**, **Responsibilities**, **Required Output Files** and process. 

---



## Key Features

### Diff Window

After Claude finishes working, you get a full diff of every file it changed. Review each hunk individually — keep what looks good, revert what doesn't. You stay in control of what actually lands on the branch.

### Auto-Learning

KlodTalk automatically reviews its own sessions and writes `CLAUDE.md` skill files into your project when it identifies useful patterns. Over time, Claude gets better at understanding your codebase, your conventions, and your preferences — without you having to maintain documentation manually.

### Work Logging

Every pipeline run is fully logged:

- **Progress updates** — real-time status pushed to the client as each step runs.
- **Plan** — the planner's implementation plan, visible before coding starts.
- **Coder output** — what was implemented and which files changed.
- **Review results** — the reviewer's findings in a dedicated Reviews tab.
- **Full log** — verbatim sub-agent output in `.klodTalk/history/orchestrator_log.md`.

---

## TLS / WSS (Optional)

KlodTalk supports encrypted connections with self-signed TLS certificates.

```bash
./helpers/linux/generate_cert.sh       # Linux
helpers\windows\generate_cert.bat      # Windows
```

Then configure `ssl_cert` and `ssl_key` in `config/server_config.yaml`. See the [full TLS guide](docs/install.md) for client setup.

---

## Project Structure

```
klodTalk/
├── config/                        # Server config, user/project definitions
├── server/                        # WebSocket server & Docker agent runtime
├── teams/                         # Team pipeline definitions & role prompts
│   ├── teams/                     # One Markdown file per team
│   └── roles/                     # One Markdown file per role
├── clients/
│   ├── web/                       # Browser client (vanilla JS, zero deps)
│   ├── android/                   # Android app (Kotlin / Jetpack Compose)
│   └── ios/                       # Placeholder — contributions welcome
├── helpers/                       # CLI tools & install/run scripts
├── tests/                         # Unit tests (pytest)
├── docs/                          # Documentation
└── CLAUDE.md                      # Start here — Claude knows the rest
```

---

## Privacy

KlodTalk runs entirely on your local network. No data leaves your machine.

- No analytics, tracking, or advertising SDKs.
- No audio recorded or transmitted — only transcribed text.
- No crash reporting to external services.

Full policy: `docs/privacy_policy.html`

## Security

Local-network tool. Do not expose to the internet. See `SECURITY.md` for details.

## Contributing

Contributions welcome — especially macOS and iOS. See `CONTRIBUTING.md`.

## License

MIT
