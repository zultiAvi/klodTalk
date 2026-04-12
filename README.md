# KlodTalk

A voice-first system for talking to AI agents. Speak into your phone (or browser), and your words are transcribed, sent over WebSocket to a server on your computer, and routed to a Docker-containerized Claude Code agent. The agent's response flows back to you.

**Voice in, text out, agents do the work.** No typing, no switching windows. Talk to your agents from anywhere on your local network.

## How It Works

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
     ├── "read back"    → Claude confirms what it understood
     ├── "start working" → Claude executes the request
     ├── Polls for project output (out_messages/)
     └── Pushes response back to all connected clients
```

- **File-based agent I/O**: Agents are decoupled from the server. An agent just reads `in_message.txt` and writes `out_message.txt` — no API integration needed.
- **Docker isolation**: Each agent runs in its own container with only its workspace mounted.
- **Multi-user, multi-project**: Users authenticate independently. Projects list their allowed users. Multiple users can share a project.
- **Web-based Claude auth**: No API keys — the server authenticates Claude Code CLI via browser OAuth at startup and mounts the session into containers.
- **Two clients, same protocol**: The Android app and web client speak the exact same WebSocket JSON protocol.
- **Team pipelines**: Optionally run a multi-role pipeline (Planner → Coder → Reviewer) instead of a single Claude invocation.
- **Auto-update**: Optionally enable a background watcher that detects new commits on `main`, pulls them, rebuilds the Docker image, and restarts the server automatically (disabled by default in `config/server_config.yaml`).

## Quick Start

### 1. Install (one command)

**Linux / macOS:**
```bash
bash helpers/linux/install.sh
```

**Windows** (run as Administrator):
```bat
helpers\windows\install.bat
```

Both installers handle Docker installation, Python venv setup, example config copying, and Docker image build. They are idempotent — safe to re-run.

### 2. (Alternative) Manual setup

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r server/requirements.txt
cp config/projects.json.example config/projects.json
cp config/users.json.example config/users.json
```

### 3. Configure users and agents

```bash
# Add a user (prompts for password)
python helpers/add_user.py add myuser

# Add a project pointing to a project folder
python helpers/add_project.py add myagent -u myuser -d "My assistant" -f /path/to/project
```

### 4. Start the server

**Linux / macOS:**
```bash
./helpers/linux/run_server.sh
```

**Windows:**
```bat
helpers\windows\run_server.bat
```

The server binds to `0.0.0.0:9000` by default (see `config/server_config.yaml`). On first run it authenticates Claude Code via browser OAuth.

### 5. Connect a client

**Android app** — build the APK and install it:
```bash
./helpers/linux/compile_apk.sh        # debug APK → build/
```
Open the app, enter your server IP, port `9000`, username, and password, then tap Connect.

**Web client** — open `clients/web/index.html` in a browser on the same network, or serve it with any static file server.

## Voice Trigger Phrases

| Phrase | Effect |
|--------|--------|
| `read back` | Claude summarises what it understood — no code changes. Useful for verifying garbled voice input. |
| `start working` | Claude executes the accumulated request. |

**Typical flow:**
1. Say your request (one or more messages).
2. Say "read back" — Claude replies with what it understood.
3. Say "start working" to proceed, or correct yourself and say "read back" again.

## Message Protocol (JSON over WebSocket)

| Direction | Type | Fields |
|-----------|------|--------|
| Client → Server | `hello` | `name`, `password_hash` |
| Server → Client | `projects` | `projects` (list of `{name, description}`) |
| Client → Server | `text` | `project`, `content` |
| Server → Client | `response` | `project`, `content` |

## Project Structure

```
klod_talk/
├── config/
│   ├── server_config.yaml      # Server host, port, Docker, auto-update
│   ├── projects.json.example     # Example agent definitions
│   └── users.json.example      # Example user definitions
├── server/
│   ├── server.py               # WebSocket server & broker
│   ├── run_agent.py            # Agent executor (runs inside container)
│   ├── session_manager.py      # Session lifecycle
│   ├── Dockerfile.agent        # Agent container image
│   ├── requirements.txt
│   └── utils/                  # Abstraction layers (claude_auth, os, git, docker)
├── clients/
│   ├── android/                # Android app (Kotlin / Jetpack Compose)
│   ├── web/
│   │   └── index.html          # Browser client (vanilla JS, zero deps)
│   └── ios/                    # Placeholder for future iOS client
├── teams/
│   ├── teams/                  # Team definitions (one .md per workflow)
│   ├── roles/                  # Shared role definitions (.md files)
│   ├── orchestrator.md         # Master orchestration instructions
│   └── run_claude_team.sh      # Entry point (shell → Claude)
├── helpers/
│   ├── add_user.py             # User management CLI (supports interactive mode)
│   ├── add_project.py          # Project management CLI
│   ├── linux/
│   │   ├── install.sh          # Full installer (Docker, venv, configs, image)
│   │   ├── run_server.sh       # Start server with venv Python
│   │   ├── compile_apk.sh      # Build Android APK
│   │   ├── docker_build.sh     # Build agent Docker image
│   │   ├── docker_rm.sh        # Remove agent containers
│   │   ├── rebuild_sessions.py # Rebuild session state from workspace data
│   │   └── generate_cert.sh    # Generate self-signed TLS cert
│   └── windows/
│       ├── install.bat         # Full installer for Windows
│       ├── install.ps1         # PowerShell helper (Docker/Python via winget)
│       ├── run_server.bat      # Start server with venv Python
│       ├── docker_build.bat    # Build agent Docker image
│       ├── docker_rm.bat       # Remove agent containers
│       └── generate_cert.bat   # Generate self-signed TLS cert
├── tests/                      # Unit tests (pytest)
├── docs/                       # Documentation
├── LICENSE
├── SECURITY.md
├── CONTRIBUTING.md
└── CLAUDE.md
```

## Setting Up WSS (Encrypted WebSocket)

KlodTalk supports WSS (WebSocket Secure) using a self-signed TLS certificate. This encrypts all traffic between clients and the server. **WSS is optional** — both clients support plain `ws://` as well.

### 1. Generate a certificate

**Linux / macOS:**
```bash
./helpers/linux/generate_cert.sh
# Enter your server's LAN IP (e.g. 192.168.1.100) when prompted
# Generates server.crt and server.key in ~/.klodtalk/certs/
```

**Windows:**
```bat
helpers\windows\generate_cert.bat
```

The certificate SAN must match the IP your clients connect to. If your server IP changes, regenerate the certificate.

### 2. Configure the server

Edit `config/server_config.yaml`:
```yaml
server:
  host: "0.0.0.0"
  port: 9000
  docker: true
  ssl_cert: "/home/youruser/.klodtalk/certs/server.crt"
  ssl_key: "/home/youruser/.klodtalk/certs/server.key"
```

Restart the server. You should see `WSS (TLS) enabled` in the log output.

### 3. Trust the certificate on clients

**Web browser:**
1. Before using wss://, you must first trust the certificate in your browser: navigate to `https://<server-ip>:9000` in a new tab.
2. Click "Advanced" → "Proceed anyway" to accept the self-signed cert. You should see a brief server response confirming the connection works.
3. In the web client settings, switch protocol to `wss://`. A help banner will appear reminding you of this step.
4. If you skip step 1, switching to wss:// will result in a connection error with a reminder to complete the cert trust step.

**Android:**
1. Get the `server.crt` file onto your device using one of these methods:
   - **Email**: send the cert to yourself and open the attachment.
   - **USB/ADB**: `adb push ~/.klodtalk/certs/server.crt /sdcard/Download/`
   - **Cloud storage**: upload to Google Drive, share link, open on device.
2. Go to Settings → Security → Install a certificate → CA certificate.
3. Select the `server.crt` file and confirm installation.
4. In the KlodTalk app settings, select `wss://` as the protocol. A help link in the settings explains these steps.

### Do I need WSS?

WSS is recommended if your LAN has untrusted devices, but **not required**. On a trusted home network, `ws://` works fine and avoids the certificate setup. Both the web client and Android app let you choose the protocol in settings.

For Google Play Store distribution, users who want WSS will need to manually install the self-signed CA certificate on their device. This is a one-time setup per device. Users on trusted networks can simply use `ws://` with no certificate setup needed.

## Security

KlodTalk is a **local-network tool**. Do not expose port 9000 to the internet. See [SECURITY.md](SECURITY.md) for the full threat model and recommendations.

## Roadmap

- iOS client
- Agent output streaming (real-time partial responses)
- Plugin system for non-Claude agents

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup instructions and guidelines.

## License

[MIT](LICENSE)
