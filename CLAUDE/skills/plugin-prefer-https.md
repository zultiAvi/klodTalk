---
skill_name: plugin-prefer-https
triggers:
  - Plugin/skill installation silently failing inside a KlodTalk agent container
  - Configuring environment variables for the agent Docker runtime
  - Operators preparing docker-compose.yml or server/run_agent.py env blocks
summary: Set `CLAUDE_CODE_PLUGIN_PREFER_HTTPS=1` (Claude Code v2.1.141+) in the agent container environment so plugin clones use HTTPS instead of SSH -- avoids silent failures in containers without SSH keys.
---

# Skill: Prefer HTTPS for Plugin Cloning in Docker Agents

## Quick Reference
- Env var: `CLAUDE_CODE_PLUGIN_PREFER_HTTPS=1` (Claude Code v2.1.141+)
- Where to set: container env (`docker-compose.yml` `environment:` block, or the env dict in `server/run_agent.py`)
- Do **NOT** add to `server/Dockerfile.agent` -- that file is pinned (see `docker-claude-stability`)
- Effect: plugin cloning falls back to HTTPS URLs instead of `git@github.com:...` SSH

## When to Use
- An agent container is failing to install a Claude Code plugin or skill plugin pulled from a Git source.
- Setting up a new KlodTalk deployment where Docker containers have no mounted SSH keys.
- Reviewing the agent container env block to ensure plugin transport is HTTPS-only.

## Why It Matters

KlodTalk agents run in Docker containers (`server/Dockerfile.agent`). The default container image has no SSH keys mounted, so any Git clone attempted over SSH (`git@github.com:...`) will fail at the authentication step. Some plugin install paths in Claude Code default to SSH for hosts where it has been used before, which produces a silent install failure inside the container while working fine on the host.

`CLAUDE_CODE_PLUGIN_PREFER_HTTPS=1` instructs the CLI to rewrite plugin Git URLs to their HTTPS equivalents before cloning. HTTPS clones of public plugin repos succeed without credentials, which matches the default Docker agent environment.

## Instructions

### Recommended Placement
Set the variable at **container runtime**, not in the pinned Dockerfile:

1. **docker-compose.yml** -- under the agent service `environment:` block:
   ```yaml
   environment:
     - CLAUDE_CODE_PLUGIN_PREFER_HTTPS=1
   ```
2. **server/run_agent.py** -- in the env dict passed when spawning the container:
   ```python
   env = {
       ...,
       "CLAUDE_CODE_PLUGIN_PREFER_HTTPS": "1",
   }
   ```

### Why Not in Dockerfile.agent
`server/Dockerfile.agent` is pinned and managed under the `docker-claude-stability` skill. Baking runtime-env variables into the image conflates build-time pinning with operational configuration and forces an image rebuild whenever the env policy changes. Keep this variable in the runtime env so operators can toggle it without rebuilding the base image.

### Verifying
Inside a running agent container:
```bash
echo "${CLAUDE_CODE_PLUGIN_PREFER_HTTPS:-unset}"
```
Expected output: `1`. If `unset`, the variable did not propagate from `docker-compose.yml` / `run_agent.py` and plugin clones may still attempt SSH.

### Scope and Limits
- The variable governs plugin Git transport only. It does not affect MCP server downloads, npm installs, or non-plugin clones.
- Setups that **do** mount SSH keys (e.g., a developer running the agent container locally with their `~/.ssh` bind-mounted) can leave the variable unset without harm -- SSH clones will succeed.
- The variable was added in Claude Code v2.1.141. Containers pinned to an earlier CLI version will silently ignore it; verify the CLI version pinned in `server/Dockerfile.agent` is v2.1.141 or newer before relying on it.

## Related
- `docker-claude-stability` -- companion skill on pinning the CLI version and suppressing auto-updates in `Dockerfile.agent`.
- `session-id-in-bash-tools` -- another runtime env var (`CLAUDE_CODE_SESSION_ID`) that lives in container env, not in the Dockerfile.

## Source
Claude Code v2.1.141 release notes: https://github.com/anthropics/claude-code/releases/tag/v2.1.141 (github.com/anthropics/claude-code).
