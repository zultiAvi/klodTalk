# Skill: disallowedTools Frontmatter for Roles

## When to Use
When adding or modifying role files that need tool restrictions, or when enforcing least-privilege for agent roles in --print mode.

## Instructions

### Pattern
Role `.md` files in `teams/roles/` can declare `disallowedTools:` in YAML frontmatter to restrict which Claude Code tools the agent can use. This is enforced in `--print` mode (Claude Code v2.1.119+).

### Example
```yaml
---
disallowedTools:
  - Bash
  - Write
  - Edit
  - MultiEdit
  - NotebookEdit
---
```

### Current Role Restrictions
- **reviewer.md**: Read-only (no Bash, Write, Edit, MultiEdit, NotebookEdit)
- **executor.md**: Run-only (no Write, Edit, MultiEdit, NotebookEdit — keeps Bash)
- **validator.md**: Read-only (no Bash, Write, Edit, MultiEdit, NotebookEdit)

### Combining with MCP Frontmatter
If a role already has `mcpServers:` in frontmatter, add `disallowedTools:` to the same block:
```yaml
---
mcpServers:
  filesystem:
    command: npx
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/workspace"]
disallowedTools:
  - Bash
  - Write
---
```

### Notes
- Requires Claude Code v2.1.119+ with `--print` mode (Dockerfile.agent is pinned to @2.90.0, which satisfies this)
- Use `tools:` for allowlists, `disallowedTools:` for denylists
