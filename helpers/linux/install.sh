#!/usr/bin/env bash
set -euo pipefail

# ── KlodTalk Installer — Linux ──────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m'

ok()   { echo -e "${GREEN}[OK]${NC}    $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC}  $*"; }
err()  { echo -e "${RED}[ERROR]${NC} $*"; }
step() { echo -e "\n${BOLD}── $* ──${NC}"; }

echo -e "${BOLD}"
echo "╔══════════════════════════════════════╗"
echo "║     KlodTalk Installer — Linux       ║"
echo "╚══════════════════════════════════════╝"
echo -e "${NC}"

# ── 1. Docker ────────────────────────────────────────────────────────────────

step "Checking Docker"

if docker info &>/dev/null; then
    ok "Docker is installed and running"
else
    warn "Docker not found or not running — attempting install"

    if [ ! -f /etc/os-release ]; then
        err "Cannot detect Linux distribution (/etc/os-release missing)"
        err "Please install Docker manually: https://docs.docker.com/engine/install/"
        exit 1
    fi

    # shellcheck disable=SC1091
    source /etc/os-release

    case "${ID:-}" in
        ubuntu|debian|linuxmint|pop)
            echo "Detected ${ID} — installing Docker via official convenience script..."
            curl -fsSL https://get.docker.com | sudo sh
            ;;
        fedora)
            echo "Detected Fedora — installing Docker via dnf..."
            sudo dnf -y install dnf-plugins-core
            sudo dnf config-manager --add-repo https://download.docker.com/linux/fedora/docker-ce.repo
            sudo dnf install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin
            ;;
        rhel|centos|rocky|almalinux)
            echo "Detected ${ID} — installing Docker via dnf..."
            sudo dnf -y install dnf-plugins-core
            sudo dnf config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
            sudo dnf install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin
            ;;
        arch|manjaro)
            echo "Detected ${ID} — installing Docker via pacman..."
            sudo pacman -S --noconfirm docker
            ;;
        *)
            err "Unsupported distribution: ${ID}"
            err "Please install Docker manually: https://docs.docker.com/engine/install/"
            exit 1
            ;;
    esac

    sudo systemctl enable --now docker

    if ! groups "$USER" | grep -q '\bdocker\b'; then
        sudo usermod -aG docker "$USER"
        warn "Added $USER to the docker group."
        warn "You may need to log out and back in (or run 'newgrp docker') for this to take effect."
    fi

    if docker info &>/dev/null; then
        ok "Docker installed and running"
    else
        warn "Docker installed but current shell may not have group permissions yet."
        warn "Try: newgrp docker   (or log out and back in), then re-run this script."
    fi
fi

# ── 2. Python 3 ──────────────────────────────────────────────────────────────

step "Checking Python"

PYTHON=""
for cmd in python3 python; do
    if command -v "$cmd" &>/dev/null; then
        PYTHON="$cmd"
        break
    fi
done

if [ -z "$PYTHON" ]; then
    err "Python 3 not found. Install it via your package manager:"
    err "  Ubuntu/Debian: sudo apt install python3 python3-venv"
    err "  Fedora:        sudo dnf install python3"
    err "  Arch:          sudo pacman -S python"
    exit 1
fi

PY_VERSION=$("$PYTHON" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PY_MAJOR=$("$PYTHON" -c 'import sys; print(sys.version_info.major)')
PY_MINOR=$("$PYTHON" -c 'import sys; print(sys.version_info.minor)')

if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 9 ]; }; then
    err "Python >= 3.9 required (found $PY_VERSION)"
    exit 1
fi

ok "Python $PY_VERSION ($PYTHON)"

# ── 3. Python venv ───────────────────────────────────────────────────────────

step "Setting up Python virtual environment"

if [ -d .venv ]; then
    ok ".venv already exists — skipping creation"
else
    "$PYTHON" -m venv .venv
    ok "Created .venv"
fi

.venv/bin/pip install -q -r server/requirements.txt
ok "Dependencies installed"

# ── 4. Example configs ───────────────────────────────────────────────────────

step "Copying example configs"

if [ -f config/users.json ]; then
    ok "config/users.json already exists — skipping"
else
    cp config/users.json.example config/users.json
    ok "Created config/users.json from example"
fi

if [ -f config/projects.json ]; then
    ok "config/projects.json already exists — skipping"
else
    cp config/projects.json.example config/projects.json
    ok "Created config/projects.json from example"
fi

# ── 5. Build Docker image ────────────────────────────────────────────────────

step "Building Docker image"

if bash helpers/linux/docker_build.sh; then
    ok "Docker image 'klodtalk-agent' built successfully"
else
    err "Docker image build failed"
    exit 1
fi

# ── 6. Next steps ────────────────────────────────────────────────────────────

echo ""
echo -e "${GREEN}${BOLD}Installation complete!${NC}"
echo ""
echo -e "${BOLD}Next steps:${NC}"
echo ""
echo "  1. Add a user:"
echo "     $PYTHON helpers/add_user.py add <name>"
echo ""
echo "  2. Add a project:"
echo "     $PYTHON helpers/add_project.py add <name> --users <user> --description '...' --folder <path>"
echo ""
echo "  3. Generate TLS certificate:"
echo "     bash helpers/linux/generate_cert.sh"
echo ""
echo "  4. Run the server:"
echo "     bash helpers/linux/run_server.sh"
echo ""
