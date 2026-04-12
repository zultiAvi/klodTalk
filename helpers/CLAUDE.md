# helpers/

CLI tools and scripts that manage the system from the outside. Nothing here runs at server runtime — these are operator tools you run manually from the terminal.

## Why Separate Scripts

The server itself has no admin UI. Instead of building web-based admin panels or embedding management commands into the server process, we keep administration as standalone scripts. This means:

- You can add users and projects without the server running.
- Config files are the single source of truth, and these scripts are just convenient editors for them.
- No admin endpoints to secure on the WebSocket server.

## Files

### add_user.py
Manages `config/users.json`. Handles SHA-256 password hashing so you never manually create hashes. Supports add, update, delete, and list operations. Passwords can be passed inline (`-p`) or entered interactively (prompted, hidden input).

### add_project.py
Manages `config/projects.json`. Each project gets a name, a list of allowed users (`--users`, accepts multiple names), a description, and a folder path. The `list` command can filter by user to show only their projects. Supports add, modify, delete, and list operations.

### rebuild_sessions.py
Rebuilds session state from workspace data. References `config/projects.json`.

### linux/

Linux/macOS shell scripts.

#### install.sh
Full installer for Linux. Installs Docker (detects Ubuntu/Debian, Fedora/RHEL, Arch), sets up the Python venv, copies example configs, and builds the Docker image. Idempotent — safe to re-run. Run from anywhere; it detects the project root from its own location.

#### compile_apk.sh
Builds the Android APK via Gradle. Validates prerequisites (ANDROID_HOME, Java 17+), runs the appropriate Gradle task (debug or release), and copies the APK to `build/` at the project root.

#### run_server.sh
Launches `server.py` using the project's `.venv` Python. Fails early with a helpful message if `.venv` doesn't exist yet.

#### generate_cert.sh
Generates a self-signed TLS certificate with SAN for the server's LAN IP. Auto-detects the IP and prompts for confirmation.

#### docker_build.sh
Builds the `klodtalk-agent` Docker image.

#### docker_rm.sh
Removes all running `klodtalk_*` containers.

### windows/

Windows batch scripts — equivalent functionality to the Linux scripts.

#### install.bat
Full installer for Windows. Delegates Docker Desktop and Python installation to `install.ps1` (PowerShell helper), sets up the Python venv, copies example configs, and builds the Docker image. Idempotent — safe to re-run. Handles restart requirements after Docker Desktop install.

#### install.ps1
PowerShell helper called by `install.bat` for Docker Desktop and Python installation via winget. Handles winget availability checks and provides clear error messages with manual install URLs as fallback. Not intended to be run standalone.

#### run_server.bat
Launches `server.py` using the project's `.venv` Python.

#### generate_cert.bat
Generates a self-signed TLS certificate with SAN for the server's LAN IP.

#### docker_build.bat
Builds the `klodtalk-agent` Docker image.

#### docker_rm.bat
Removes all running `klodtalk_*` containers.
