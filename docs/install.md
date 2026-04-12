# Installation Guide

## Prerequisites

- **Docker** — required for agent isolation
- **Python 3.9+** — required for the server
- **Git** — required for workspace management

## Quick Install (Linux)

```bash
git clone <repo-url> klodtalk
cd klodtalk
bash helpers/linux/install.sh
```

The installer will:
1. Install Docker if not present (Ubuntu/Debian, Fedora/RHEL, Arch)
2. Set up a Python virtual environment at `.venv/`
3. Install Python dependencies from `server/requirements.txt`
4. Copy example configs (`config/users.json`, `config/projects.json`)
5. Build the `klodtalk-agent` Docker image

## Quick Install (Windows)

```cmd
git clone <repo-url> klodtalk
cd klodtalk
helpers\windows\install.bat
```

## Post-Install Setup

### 1. Add a user

```bash
python helpers/add_user.py add <username>
# Or run without arguments for interactive mode:
python helpers/add_user.py
```

### 2. Add a project

```bash
python helpers/add_project.py add <name> \
    --users <username> \
    --description "What this project does" \
    --folder /path/to/workspace
```

### 3. Generate TLS certificate (recommended)

```bash
bash helpers/linux/generate_cert.sh
```

Update `config/server_config.yaml` with the cert paths:
```yaml
server:
  ssl_cert: "/path/to/server.crt"
  ssl_key: "/path/to/server.key"
```

### 4. Configure authentication method

Edit `config/server_config.yaml`:
```yaml
claude:
  auth_method: "session"    # "session" (OAuth) or "api_key"
```

If using `api_key`, set the `ANTHROPIC_API_KEY` environment variable before starting the server.

### 5. Start the server

```bash
bash helpers/linux/run_server.sh
```

The server listens on the port configured in `server_config.yaml` (default: 3174).

## Connecting Clients

- **Web**: Open `https://<server-ip>:<port>` in a browser (serve `clients/web/index.html`)
- **Android**: Build the APK with `bash helpers/linux/compile_apk.sh` and install on your device
