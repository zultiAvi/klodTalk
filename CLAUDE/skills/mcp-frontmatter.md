# Skill: MCP Servers in Role Frontmatter

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
      - "@anthropic-ai/mcp-filesystem"
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
- The frontmatter is parsed by the orchestrator or Claude Code CLI before the role instructions are applied.

### Source
Inspired by Claude Code CLI v2.1.117 release (github.com/anthropics/claude-code).
