---
skill_name: gpu-passthrough-sessions
triggers:
  - User asks whether GPU is exposed in session containers
  - Modifying `_start_session_container` GPU detection
  - Adding a per-project GPU opt-out
summary: Session containers auto-receive `--gpus all` whenever host `nvidia-smi` returns 0; no per-project opt-out exists today.
---

# Skill: GPU Passthrough in Session Containers

## Quick Reference
- Auto-detection lives in `server/session_manager.py:_start_session_container()` (~line 498).
- Logic: `subprocess.run(["nvidia-smi"])` -> if returncode==0, append `["--gpus", "all"]` to the docker run args. `FileNotFoundError` -> CPU-only.
- Applies uniformly to regular user sessions AND the `system_routine` session.
- Base image (`server/Dockerfile.agent`) is CUDA-enabled, so GPU workloads run inside the container when passthrough is active.

## When to Use
When answering "is the GPU exposed?", when changing GPU detection, or when implementing a per-project opt-out.

## How a Per-Project Opt-Out Would Look
1. Add `"gpu": false` (default `true`) to `projects.json` schema; document in `config/CLAUDE.md`.
2. In `_start_session_container`, read the project's `gpu` field; short-circuit the `nvidia-smi` check when `false`.
3. Update tests to cover both branches.

Not implemented today — every session with a working `nvidia-smi` host gets full passthrough.
