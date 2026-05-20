---
skill_name: github-mcp-scout
triggers:
  - Adding MCP-based GitHub access to a scout or research role
  - Replacing WebSearch site:github.com calls with authenticated API tool calls
  - Configuring GITHUB_TOKEN propagation for KlodTalk agents
summary: Give the GitHub Scout role authenticated MCP tool access (search_repositories, get_repository, get_readme) by declaring mcpServers.github in its frontmatter -- more reliable than scraping WebSearch results.
---

# Skill: GitHub MCP Server for the Scout Role

## Instructions

Any role whose job is to discover GitHub artefacts (repos, READMEs, issues) -- scout, researcher, evaluator -- should use the official GitHub MCP server instead of `WebSearch` with `site:github.com` filters. `WebSearch` returns scraped snippets; star counts and recent-commit dates often hallucinate. The official `@github/mcp-server` calls the GitHub REST/GraphQL APIs with an authenticated token, returning structured JSON.

**Frontmatter block on `teams/roles/github_scout.md`:**
```yaml
mcpServers:
  github:
    command: npx
    args: ["-y", "@github/mcp-server"]
    env:
      GITHUB_TOKEN: "${GITHUB_TOKEN}"
```

**Env var:** operators must export `GITHUB_TOKEN` on the host so it propagates into the agent container. (The legacy `@modelcontextprotocol/server-github` package is deprecated; its `GITHUB_PERSONAL_ACCESS_TOKEN` env var has been renamed to `GITHUB_TOKEN` in the new `@github/mcp-server` package.)

**Preferred MCP tools:** `search_repositories`, `get_repository`, `get_readme`, `search_code`, `list_issues`.

**Caveats:**
- Per `instincts.md` line 7, role frontmatter currently forwards `mcpServers` and `disallowedTools` only. Other keys (e.g., `settings:`) are silently ignored.
- Without `GITHUB_TOKEN`, the server starts in unauthenticated mode (60 req/hour rate limit) -- usable but lower-throughput.
- An alternative invocation is `docker run -e GITHUB_TOKEN ghcr.io/github/github-mcp-server`; prefer the npm variant for parity with other KlodTalk MCP configs.

## Source
github/github-mcp-server -- https://github.com/github/github-mcp-server (~26,000 stars).
