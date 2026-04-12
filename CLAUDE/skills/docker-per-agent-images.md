# Skill: Docker Per-Project Image Management

## When to Use
When working on Docker container persistence, per-project images, `docker commit`, project dependencies, Docker-in-Docker setup, or Docker socket mounting in the KlodTalk system.

## Instructions

### Architecture
- Per-project images: `klodtalk_{sanitized_project_name}` created via `docker commit` on session close
- Two independent config flags: `docker_commit` (default true), `docker_socket` (default false)
- Bind mounts (`/workspace`, `~/.claude`, `~/.ssh`) are excluded from commit automatically
- Docker-in-Docker via socket mount (`/var/run/docker.sock`) with `--group-add` (not `--privileged`)

### Key Files
- `server/session_manager.py` — Session lifecycle, image selection, commit logic
- `server/utils/docker/local.py` — Docker CLI wrapper (`commit_container`, `get_image_size`)
- `server/utils/docker/base.py` — Abstract Docker interface
- `server/Dockerfile.agent` — Base image with `docker-ce-cli`

### Lifecycle
1. Session start: check per-project image exists -> use it or fall back to base
2. Session close: commit running container -> then `docker rm -f`
3. Rebuild: `docker rmi klodtalk_{name}` forces next session to use base

### Gotchas
- Must commit BEFORE `stop_container()` (which does `docker rm -f`)
- Only last session for a project commits (concurrent session check)
- Commit failure is non-fatal — log and proceed
- Image name sanitization: lowercase, replace special chars, collapse underscores
- Docker socket GID: `os.stat("/var/run/docker.sock").st_gid` for `--group-add`
