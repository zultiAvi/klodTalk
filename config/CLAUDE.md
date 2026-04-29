# config/

Runtime configuration for the server. Core files: **`server_config.yaml`**, **`users.json`**, and **`projects.json`**.

Team pipeline definitions live in `teams/teams/` as `.md` files.

## Why This Layout

- **`server_config.yaml`** — Operator-level settings (host, port, Docker toggle, Claude auth method, git protocol). YAML because it's human-friendly for a small config.
- **`users.json`** — Authentication data. Contains password hashes and is gitignored. Managed through `helpers/add_user.py`.
- **`projects.json`** — Project definitions. Maps project names to workspace folders and allowed users.

Runtime state files live in `.klodTalk/state/` (gitignored). The `config/` folder is for static admin configuration only.

## Design Decisions

**Users and projects are loosely coupled.** A user in `users.json` can exist without any projects. A project's `users` list references usernames from `users.json`, but there's no foreign key enforcement — the server simply filters at runtime. This keeps management simple: add users and projects independently, link them by putting usernames in the project's `users` list.

**`users` is always a list.** Even if an project has a single user, `users` is `["Avi"]` not `"Avi"`. This avoids type-checking everywhere and makes shared projects (multiple users on the same workspace) a natural extension rather than a special case.

**Project folders are absolute paths.** Each project points to a real directory on the host machine. The server mounts this into Docker containers and uses it for the `in_messages`/`out_messages` file exchange. Absolute paths avoid ambiguity about where the workspace lives.

**Passwords are SHA-256 hashed client-side** before sending over WebSocket. The server stores and compares hashes, never plaintext. This isn't full security (no TLS yet), but prevents casual password exposure in transit and at rest.

## File Schemas

### server_config.yaml
```yaml
server:
  host: "0.0.0.0"    # bind address
  port: 3174          # WebSocket port
  docker: true        # start agent containers on boot
  ssl_cert: ""        # Path to server.crt — leave empty for plain ws://
  ssl_key: ""         # Path to server.key — leave empty for plain ws://
  session_data_path: "/tmp/klodTalk"  # base dir for per-session logs (<path>/logs/) and workspace copies (<path>/workspaces/)

routine:
  enabled: false            # opt-in nightly GitHub scouting routine
  schedule_hour: 4          # 24h format, local time
  schedule_minute: 0
  github_search_tags:       # topics to search for on GitHub
    - "claude"
    - "claude-code"
    - "claude-skill"
    - "claude-agent"
    - "claude-mcp"
    - "anthropic"
  max_ideas_to_implement: 3 # max ideas to implement per run
  project: ""               # project name whose workspace the scout uses
```

`routine` (optional) -- Automated nightly routine that scouts GitHub for Claude-related improvements, evaluates ideas, and implements the best ones. When `enabled` is `true` and `project` is set to a valid project name, the server creates a permanent "system" session (ID: `system_routine`) visible to all users. At the configured time (default 4:00 AM local), a scout agent runs inside this session's Docker container, searches GitHub, and reports findings. The system session cannot be closed or deleted by users. All clients see it with distinct amber styling and a "System" badge.

### users.json (gitignored)
```json
{
  "Username": {
    "password_hash": "<sha256 hex>",
    "created": "<ISO timestamp>"
  }
}
```

### projects.json
```json
[
  {
    "name": "project_name",
    "users": ["User1", "User2"],
    "description": "what this project does",
    "folder": "/absolute/path/to/workspace",
    "base_branch": "main",
    "code_review": false,
    "allowed_external_paths": [
      {"path": "/home/avi/designs", "writable": true},
      {"path": "/home/avi/docs/specs.pdf", "writable": false},
      "/home/avi/legacy"
    ],
    "team": "plan-code-review",
    "created": "<ISO timestamp>"
  }
]
```

`base_branch` (default: `"main"`) — the branch merged into the project's current branch before Claude starts work (e.g. `"main"` or `"dev"`). Claude works on whatever branch is currently checked out in the workspace. Committing and PRs are left to the human.

`code_review` (default: `false`) — if `true`, a code review is automatically triggered after each successful execute. The reviewer writes to `.klodTalk/pr_messages/pr_message.txt` and the client receives it in a separate Reviews inbox.

`allowed_external_paths` (optional) — a list of external paths (directories or files) to mount into the project's Docker container and allow during task planning. Each entry can be:
- A **string** (legacy format, mounted read-only): `"/home/avi/docs"`
- An **object** with per-path writability: `{"path": "/home/avi/designs", "writable": true}`

When `writable` is `true`, the path is mounted read-write (`rw`) in the container; when `false` or omitted, it is mounted read-only (`ro`). The old string-list format is fully backward compatible and treated as read-only. Omit the field or use `[]` if no external paths are needed.

When `results` is `true`, the path is designated as the project's **results folder** — the location where agents should save all output/result files (reports, generated assets, exports, etc.). A results entry is always mounted read-write regardless of the `writable` setting. Only one entry should be marked as results. Example: `{"path": "/home/avi/KlodTalk/out/designs", "writable": true, "results": true}`.

`team` (optional) — references a file in `teams/teams/` by **basename without `.md`** (e.g. `"plan-code-review"` loads `teams/teams/plan-code-review.md`). When set, the multi-agent team pipeline is used instead of a single Claude invocation. Omit or set to `null` for direct mode. When `team` is set, `code_review` is redundant (the Reviewer is already part of the pipeline) and can be left `false`. Per-role model assignments live in the team definition, not in `projects.json`.

Each workspace gets a `.klodTalk/` directory (gitignored automatically) containing `in_messages/`, `out_messages/`, `pr_messages/`, `history/`, and `team/` (team pipeline session files).

### Team definitions (`teams/teams/<name>.md`)

Each team is a Markdown file. The filename stem is the team name (e.g. `plan-code-review.md` is team `plan-code-review`).

Team `.md` files define members (name, role, model) in a Markdown table and the pipeline as an ordered list. The Claude orchestrator reads these directly. See `docs/add_team.md` for the format.

**Available teams:** See the `.md` files in `teams/teams/` for the full list.

**Two-role teams (no reviewer):** When the reviewer role is omitted (e.g. `plan-code`), the orchestrator skips the review loop. Pipeline runs: Planner -> Coder -> done.

Role definitions live in `teams/roles/` as `.md` files. Each role file is the system prompt for that role.

Supported models:

- `opus` (claude-opus-4-7) — most capable, highest cost
- `sonnet` (claude-sonnet-4-6) — balanced capability and speed
- `haiku` (claude-haiku-4-5-20251001) — fastest and cheapest

**Deprecated models (do not use):**
- `claude-3-haiku-20240307` — RETIRED, returns API errors since March 2026
- `claude-sonnet-4-20250514` — retiring June 15, 2026; use `claude-sonnet-4-6` instead
- `claude-opus-4-20250514` — retiring June 15, 2026; use `claude-opus-4-7` instead

Pick per role: e.g. Opus for the Coder when changes are heavy, Sonnet or Haiku for Planner/Reviewer when you want lower latency or cost.
