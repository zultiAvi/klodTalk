---
skill_name: security-guidance-plugin
triggers:
  - Enabling Anthropic's security-guidance plugin for KlodTalk Coder/Reviewer roles
  - Reducing security-related review comments via in-session vulnerability scanning
  - Pairing CLAUDE_CODE_PLUGIN_PREFER_HTTPS with a concrete plugin install
summary: Install Anthropic's official security-guidance plugin manually via /plugin install; ship to agents via KLODTALK_PLUGIN_DIR -- role frontmatter `plugins:` would be a silent no-op (instinct #7).
---

# Skill: Security-Guidance Plugin (Documentation-First)

## Quick Reference
- Plugin: `security-guidance@claude-plugins-official`
- Marketplace: `anthropics/claude-plugins-official`
- Install command (one-time, inside an authenticated container or on the host):
  `/plugin install security-guidance@claude-plugins-official`
- Verify: `/plugin list` should show `security-guidance` enabled
- Required env on container: `CLAUDE_CODE_PLUGIN_PREFER_HTTPS=1` (no SSH keys in agent images)
- Dispatch to agents: `KLODTALK_PLUGIN_DIR=/workspace/.klodTalk/plugins/security` (see `plugin-dir-dispatch.md`)

## When to Use
- Coder or Reviewer roles writing or reviewing code that touches the
  public surface (input handling, auth, persistence, command exec).
- You want real-time vulnerability hints (SQLi, XSS, command injection,
  hard-coded secrets, ~25 classes total) flagged at edit/diff/commit time
  before the change reaches the Reviewer stage.
- You want to cut security-related review comments in the KlodTalk
  pipeline by an estimated 30-40% (Anthropic-reported internal benchmark).

## Why Documentation-First (Not Frontmatter)

Per **instinct #7**, KlodTalk role `.md` frontmatter currently parses only
`mcpServers` and `disallowedTools`. Adding `plugins:` to
`teams/roles/coder.md` would be silently ignored at `server/run_agent.py`
-- a no-op. Until the orchestrator gains native frontmatter parsing for
plugins, the contract is:

1. Operator installs the plugin once via the Claude Code CLI.
2. Operator exports `KLODTALK_PLUGIN_DIR` pointing at the installed
   plugin directory (or `.zip` bundle).
3. `server/run_agent.py` already forwards `KLODTALK_PLUGIN_DIR` as
   `--plugin-dir <path>` on every `claude` invocation (see
   `plugin-dir-dispatch.md`).

This is exactly the same pattern as `plugin-dir-dispatch.md`; the present
skill names a specific, motivating plugin and documents the install steps.

## Install Steps (operator, one-time)

### 1. Authenticate and install
Inside any container (or on the host) where the Claude Code CLI is
authenticated:

```bash
claude /plugin install security-guidance@claude-plugins-official
```

### 2. Stage the plugin under the workspace mount
So every team container sees the same plugin directory:

```bash
mkdir -p /workspace/.klodTalk/plugins
cp -R ~/.claude/plugins/security-guidance /workspace/.klodTalk/plugins/security
```

`.zip` archives are also accepted by `--plugin-dir` directly -- point
`KLODTALK_PLUGIN_DIR` at the archive path and Claude Code unpacks it on
launch.

### 3. Configure the container env block
In `docker-compose.yml` (or the equivalent operator config):

```yaml
environment:
  - CLAUDE_CODE_PLUGIN_PREFER_HTTPS=1
  - KLODTALK_PLUGIN_DIR=/workspace/.klodTalk/plugins/security
```

Both env vars are required:
- `CLAUDE_CODE_PLUGIN_PREFER_HTTPS=1` -- agent containers have no SSH keys;
  without this, plugin clones fail silently. See `plugin-prefer-https.md`.
- `KLODTALK_PLUGIN_DIR=...` -- tells `run_agent.py` to append
  `--plugin-dir <path>` on every claude invocation. See
  `plugin-dir-dispatch.md`.

Do **NOT** modify `server/Dockerfile.agent` -- it is pinned (see
`docker-claude-stability.md`).

### 4. Verify
Inside a running agent container, ask Claude:

```
/plugin list
```

You should see `security-guidance` listed and enabled. If not, double
check that `KLODTALK_PLUGIN_DIR` resolves to a directory the container
can read.

## When to Apply It (per-role)

The plugin adds a small latency on every Edit and Bash-commit pass.
Recommended scopes:

| Role         | Recommended | Reason |
| ------------ | ----------- | ------ |
| Coder        | Yes         | Catches vuln patterns at write time |
| Coder (TDD)  | Yes         | Same |
| Reviewer     | Yes         | Defense in depth over the Coder pass |
| Planner      | No          | Planner does not edit code |
| Documenter   | No          | Documenter does not edit code |
| Scout        | No          | Scout reads docs/marketplaces, no edits |

Because per-role plugin dispatch via frontmatter is unsupported today
(instinct #7), the way to scope this per role is via **per-role container
env**: only set `KLODTALK_PLUGIN_DIR` in the env blocks of the Coder and
Reviewer containers, not in Planner/Scout. The orchestrator already runs
each role in a separate container, so each role's env block is
independent.

## False-Positive Suppression

The plugin understands inline suppression comments. To silence a known
false positive on a single line, append the suppression marker on that
line:

```python
query = f"SELECT * FROM x WHERE id = {id}"  # security-guidance: ignore[sql-injection]
```

Or to silence across a block:

```python
# security-guidance: ignore-start[sql-injection]
...
# security-guidance: ignore-end
```

Document each suppression with a justification comment so the Reviewer
role can audit them.

## Failure Modes

- **No SSH keys, no HTTPS env var.** Symptom: silent install failure.
  Fix: set `CLAUDE_CODE_PLUGIN_PREFER_HTTPS=1`.
- **`KLODTALK_PLUGIN_DIR` not propagated.** Symptom: `/plugin list` is
  empty inside the container even though the install succeeded on the
  host. Fix: confirm `docker-compose.yml` (or the equivalent) sets the
  env var on the agent service, not just on the orchestrator host.
- **Plugin marketplace name typo.** The official marketplace is
  `claude-plugins-official` (hyphenated, plural `plugins`). The plugin
  itself is `security-guidance` (hyphenated).

## Related
- `plugin-dir-dispatch.md` -- the underlying `KLODTALK_PLUGIN_DIR`
  dispatch contract used to ship this plugin to agents.
- `plugin-prefer-https.md` -- the HTTPS env-var prerequisite for
  keyless plugin installs in Docker.
- `disallowed-tools-frontmatter.md` -- one of the two frontmatter keys
  that *is* honored today, for contrast.

## Source
- helpnetsecurity.com -- "Security-Guidance Plugin Released for Claude
  Code" -- https://www.helpnetsecurity.com/2026/05/27/anthropic-claude-code-security-guidance-plugin/
  (2026-05-27).
- anthropics/claude-plugins-official (Official Anthropic marketplace) --
  https://github.com/anthropics/claude-plugins-official.
