---
skill_name: mcp-frontmatter
triggers:
  - Adding or modifying MCP server configs in team role files
  - Giving a role access to external tools via MCP
  - Combining mcpServers with disallowedTools in frontmatter
summary: Declare MCP servers in role YAML frontmatter for tool access (forward-looking for native parsing).
---

# Skill: MCP Servers in Role Frontmatter

## Quick Reference
- Add `mcpServers:` in YAML frontmatter with `command` and `args` per server
- Currently used by: `coder.md` (filesystem), `reviewer.md` (filesystem)
- Forward-looking: frontmatter not yet parsed natively by orchestrator

## When to Use
When adding or modifying MCP (Model Context Protocol) server configurations in team role files, or when a role needs access to external tools via MCP.

## Instructions

### Pattern
Role `.md` files in `teams/roles/` can declare MCP servers in YAML frontmatter at the very top of the file. The frontmatter block is enclosed between `---` markers and must be the first thing in the file.

### Example
```yaml
---
mcpServers:
  filesystem:
    command: npx
    args:
      - "-y"
      - "@modelcontextprotocol/server-filesystem"
      - "/workspace"
---

# Role Name
...
```

### Key Files
- `teams/roles/coder.md` — Has filesystem MCP for structured file access during implementation
- `teams/roles/reviewer.md` — Has filesystem MCP for structured file access during review

### Notes
- The `mcpServers` key maps server names to their launch configuration.
- Each server needs `command` (the binary to run) and `args` (command-line arguments).
- The filesystem MCP server restricts access to the paths listed in `args`.
- Only add MCP servers to roles that genuinely need tool access; not every role requires them.
- **Forward-looking**: The frontmatter is not currently interpreted as MCP config by the orchestrator (it is passed as prompt text). For the MCP servers to be active, the role `.md` file must be loaded directly by the Claude Code CLI (e.g., via `--mcp-config` or as a session file). This format is forward-looking for when the orchestrator or CLI gains native frontmatter parsing support.

### Source
Inspired by Claude Code CLI v2.1.117 release (github.com/anthropics/claude-code).
