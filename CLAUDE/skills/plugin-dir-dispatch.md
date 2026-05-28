---
skill_name: plugin-dir-dispatch
triggers:
  - Injecting a Claude Code plugin (e.g. the official security-guidance plugin) into KlodTalk agent containers
  - Adding `--plugin-dir` to the CLI invocation without modifying Dockerfile.agent
  - Deciding between frontmatter-based and env-var-based plugin dispatch
summary: Operator exports KLODTALK_PLUGIN_DIR; run_agent.py forwards it as --plugin-dir to every claude invocation. Frontmatter dispatch is not yet supported.
---

# Skill: `--plugin-dir` Dispatch in KlodTalk

## Quick Reference
- Env var: `KLODTALK_PLUGIN_DIR` (a directory path or a `.zip` bundle path)
- Forwarder: `server/run_agent.py` (`_claude_cmd`) appends `--plugin-dir <path>` when the env var is non-empty
- Container delivery: operator sets the env var on the agent container (e.g. via docker-compose, `-e`, or the project config) -- **DO NOT modify Dockerfile.agent**, it is pinned
- CLI flag source: Claude Code CLI changelog -- https://code.claude.com/docs/en/changelog

## When to Use
- Enabling the Claude Code Security-Guidance Plugin for Coder / Reviewer roles without baking the plugin into the agent image.
- Loading any community plugin packaged as a directory or `.zip` archive at session launch.
- Letting operators ship plugin updates without rebuilding `Dockerfile.agent`.

## Why an Env Var (Not Frontmatter)

Today, role `.md` files declare `mcpServers:` and `disallowedTools:` in YAML frontmatter, but `server/run_agent.py` **does not parse role frontmatter** -- the orchestrator concatenates role bodies into a prompt and spawns sub-agents via the Task tool. Adding a `pluginDir:` key to `teams/roles/coder.md` would be silently ignored at the `run_agent.py` layer.

Until the orchestrator gains native frontmatter parsing, the contract is:

1. Operator exports `KLODTALK_PLUGIN_DIR=/workspace/.klodTalk/plugins/security` on the agent container (or globally across all team containers if the plugin is generic).
2. `run_agent.py` checks the env var at every `claude` invocation and appends `--plugin-dir <path>` when set.
3. Per-role plugin dispatch is **not** available today. If a future plan needs per-role plugins, the orchestrator must first learn to forward `pluginDir:` (parallel to how `mcpServers` is being introduced -- see `mcp-frontmatter.md`).

## Implementation in `server/run_agent.py`

```python
def _claude_cmd(prompt: str) -> list[str]:
    cmd = ["claude"] + _claude_auth.get_cli_args() + [
        "--dangerously-skip-permissions", "--output-format", "json"
    ]
    plugin_dir = os.environ.get("KLODTALK_PLUGIN_DIR", "").strip()
    if plugin_dir:
        cmd += ["--plugin-dir", plugin_dir]
    cmd += ["-p", prompt]
    return cmd
```

Empty / unset values are ignored, so the change is a no-op for existing deployments.

## Installing the Security Plugin (One-Time Operator Step)

The Claude Code Security-Guidance Plugin (free, public; https://www.anthropic.com/news/claude-code-security) is installed via the in-session command and then exposed via a directory the container can read:

```bash
# Inside any container with claude CLI authenticated:
claude /plugins install security-guidance

# Copy / link the installed plugin under the workspace mount so all team containers see it:
mkdir -p /workspace/.klodTalk/plugins
cp -R ~/.claude/plugins/security-guidance /workspace/.klodTalk/plugins/security
```

Then on the host (or in the container env block):

```bash
export KLODTALK_PLUGIN_DIR=/workspace/.klodTalk/plugins/security
```

`.zip` archives are accepted directly -- point `KLODTALK_PLUGIN_DIR` at the archive path and Claude Code unpacks it on launch.

## Operator Env Block Documentation

Because `Dockerfile.agent` is pinned and must not be modified (project instinct), new env vars are documented here for the operator's container env block (docker-compose service `environment:` list, `docker run -e`, or the project-config equivalent). `run_agent.py` reads `KLODTALK_PLUGIN_DIR` from the process environment; no Dockerfile change is required.

## Related
- `mcp-frontmatter.md` -- frontmatter forwarding contract (forward-looking; not active for `pluginDir` today).
- `disallowed-tools-frontmatter.md` -- the other frontmatter key currently in use.
- `claude-agents-cli.md` -- catalogue of other `claude` CLI dispatch flags (`--model`, `--effort`, `--settings`, `--mcp-config`).

## Source
- Claude Code Security-Guidance Plugin announcement (anthropic.com/news, 2026-05-27) -- https://www.anthropic.com/news/claude-code-security
- Claude Code CLI `--plugin-dir` flag (GA, accepts directories and `.zip` archives) -- https://code.claude.com/docs/en/changelog
