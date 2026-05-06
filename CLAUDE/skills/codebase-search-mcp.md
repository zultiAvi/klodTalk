---
skill_name: codebase-search-mcp
triggers:
  - Adding semantic codebase search to a role
  - Reducing token usage when navigating large workspaces
  - Enabling "find where X is implemented" queries without manual grep
summary: How to add claude-context (BM25 + vector semantic search MCP) to KlodTalk role frontmatter for efficient codebase navigation.
---

# Skill: Codebase Search MCP

## Quick Reference
- Package: `@zilliz/claude-context` (via npx)
- Pattern: add to role frontmatter `mcpServers` block
- Best roles: Coder, Reviewer, Debugger (read-heavy roles on large workspaces)
- Token savings: ~40% on large codebases vs. manual file reads
- Source: https://github.com/zilliztech/claude-context (⭐ 10,700)

## When to Use

Add the codebase-search MCP to a role when:
- The workspace is large (hundreds of files, many modules)
- The role needs to find where a function, class, or pattern is implemented without reading every file
- You want to reduce blind `grep` calls and manual file reads in Coder/Reviewer/Debugger roles
- Token usage on context-loading is a bottleneck

Do NOT add this MCP to:
- Write-only roles (Planner writing plan files) — not needed
- Roles that already have a narrow, well-known file scope
- Roles where adding an MCP server conflicts with `disallowedTools` frontmatter restrictions

## How to Add to a Role

Add an `mcpServers` entry to the role file's YAML frontmatter. The workspace path must be passed as a constructor argument:

```yaml
---
mcpServers:
  filesystem:
    command: npx
    args:
      - "-y"
      - "@modelcontextprotocol/server-filesystem"
      - "/workspace"
  codebase_search:
    command: npx
    args:
      - "-y"
      - "@zilliz/claude-context"
      - "/workspace"
---
```

The `codebase_search` MCP exposes tools for:
- Semantic similarity search across all indexed files
- Keyword (BM25) search with ranking
- Hybrid search combining both modes

## Important: Do Not Modify Dockerfile.agent

KlodTalk's `Dockerfile.agent` is pinned to a specific Claude Code CLI version intentionally. Adding the codebase-search MCP **does not require modifying the Dockerfile**. The `npx @zilliz/claude-context` command is fetched at MCP server startup time from within the running container, which has network access.

If the container environment is air-gapped or `npx` is not available, pre-install the package in a custom Docker image layer instead — but do not modify `Dockerfile.agent` directly.

## Recommended Role Targets

| Role | File | Why |
|------|------|-----|
| Coder | `teams/roles/coder.md` | Finds implementation locations before editing |
| Reviewer | `teams/roles/reviewer.md` | Traces call sites and dependencies |
| Debugger | `teams/roles/debugger.md` | Locates error origins across large codebases |

The Coder and Reviewer roles already have the `filesystem` MCP in their frontmatter — add `codebase_search` alongside it using the pattern above.

## Token Savings Mechanism

Without semantic search, agents read multiple files to locate relevant code, consuming input tokens for irrelevant content. The claude-context MCP indexes the workspace at startup and serves ranked results — agents receive only the top-K relevant snippets, reducing input token use by ~40% on large repos (per upstream benchmarks).

## Limitations

- First-run indexing takes 10-30 seconds on large workspaces (one-time per container lifecycle)
- Index is in-memory and rebuilt each container start — no persistence between sessions
- Requires `npx` and internet access at container startup to fetch the package
- Search quality depends on workspace language mix; Python and TypeScript are best-supported

## References

- Source repo: https://github.com/zilliztech/claude-context
- MCP frontmatter pattern: `CLAUDE/skills/mcp-frontmatter.md`
- Related roles: `teams/roles/coder.md`, `teams/roles/reviewer.md`, `teams/roles/debugger.md`
