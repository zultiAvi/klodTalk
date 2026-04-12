# Contributing to KlodTalk

Thanks for your interest in contributing! Here's how to get started.

## Prerequisites

- Python 3.11+
- Docker (for running agents)
- Java 17+ and Android SDK (only if building the Android app)

## Setup

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/klodTalk.git
cd klodTalk

# Create a Python virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r server/requirements.txt

# Copy example configs and edit them
cp config/projects.json.example config/projects.json
cp config/users.json.example config/users.json

# Add a user
python helpers/add_user.py add myuser

# Add a project
python helpers/add_project.py add myagent -u myuser -d "Test project" -f /path/to/workspace
```

## Running the Server

```bash
./helpers/linux/run_server.sh
```

The server starts on `0.0.0.0:3174` by default (configured in `config/server_config.yaml`).

## Building the Android APK

```bash
./helpers/linux/compile_apk.sh          # debug APK
./helpers/linux/compile_apk.sh release  # release APK (unsigned)
```

Requires `ANDROID_HOME` to be set. The APK is copied to `build/`.

## Code Style

- **Python**: Follow standard Python conventions (PEP 8). No specific linter is enforced yet.
- **Kotlin**: Follow standard Android/Kotlin conventions.
- **Web client**: Vanilla HTML/CSS/JS, no build tools or dependencies.

## Making Changes

1. Fork the repo and create a feature branch.
2. For large changes, open an issue first to discuss the approach.
3. Small fixes and improvements are welcome as direct pull requests.
4. Keep commits focused — one logical change per commit.
5. Test your changes locally before submitting.

## Project Structure

See the [README](README.md) for an overview of the folder layout and architecture.
