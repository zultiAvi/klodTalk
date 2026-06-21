---
skill_name: awesome-claude-registry-mcp
triggers:
  - Considering wiring an awesome-claude registry MCP server into the github_scout role
  - Looking for a deduplicated, star-validated source to complement raw GitHub search in the Scout
  - Verifying whether the awesome-claude-mcp npm package exists before enabling it
summary: "JSONbored/awesome-claude is a curated registry of Claude ecosystem assets; it is claimed to ship a read-only MCP server (`npx awesome-claude-mcp`), but that npm package does NOT currently resolve. Do NOT wire an unverified package into github_scout frontmatter — verify with `npm view` first, since a broken MCP entry breaks the scout on every nightly run."
---

# Skill: awesome-claude Registry MCP for the GitHub Scout

## Quick Reference
- **Registry:** JSONbored/awesome-claude — https://github.com/JSONbored/awesome-claude (~268 stars). A curated, deduplicated index of Claude ecosystem assets (agents, MCP servers, skills, hooks, rules).
- **Claimed MCP server:** read-only, invoked via `npx awesome-claude-mcp`, giving structured/deduplicated registry access to complement the existing `github` MCP server in `teams/roles/github_scout.md`.
- **Wiring status: PENDING package-name verification.** As of 2026-06-21, `npm view awesome-claude-mcp` returns **E404 (Not Found)** — the package name does not resolve on the public npm registry. The Scout frontmatter was therefore left UNCHANGED.
- **Why not wire it anyway:** the GitHub Scout runs unattended nightly. A `mcpServers` entry pointing at a non-existent npm package would fail `npx -y` on every run and could break the scout's MCP startup — strictly worse than not having it.

## When to Use
Apply this when a scout or evaluator wants a pre-vetted, deduplicated source to cross-check raw GitHub search results (which hallucinate star counts and recency). Use it as the gate that prevents wiring an unverified MCP package into the Scout role.

## Instructions

### Mandatory verification step (run BEFORE enabling)
An operator must confirm the exact, resolvable package name first:

```bash
npm view awesome-claude-mcp version
# Current result (2026-06-21): npm error code E404 — 'awesome-claude-mcp@*' is not in this registry.
```

- **If it returns a version** (the package resolves): add the second MCP server alongside the existing `github` entry in `teams/roles/github_scout.md` frontmatter, preserving valid YAML and the existing `${GITHUB_TOKEN}` env:

  ```yaml
  mcpServers:
    github:
      command: npx
      args:
        - "-y"
        - "@github/mcp-server"
      env:
        GITHUB_TOKEN: "${GITHUB_TOKEN}"
    awesome-claude:
      command: npx
      args:
        - "-y"
        - "awesome-claude-mcp"   # use the EXACT name npm view resolved
  ```

  Then add a one-line note in the role's "Search Strategy" section: "The `awesome-claude` MCP server provides structured access to a curated registry of Claude ecosystem assets — query it alongside the GitHub MCP for deduplicated, validated listings. See `CLAUDE/skills/awesome-claude-registry-mcp.md`."

- **If it returns E404 / the name is uncertain** (current state): do NOT touch the Scout frontmatter. The registry can still be consulted manually via the repo's web/JSON exports until the MCP package name is confirmed.

### Caveats
- Registry coverage lags by days for the newest repos, so it complements — does not replace — raw GitHub search for last-7-days discovery.
- Per `instincts.md`, role frontmatter forwards `mcpServers` and `disallowedTools` only; other keys are silently ignored.

## Cross-References
- `github-mcp-scout.md` — the existing authenticated `@github/mcp-server` entry this would sit alongside.
- `mcp-frontmatter.md` — the `mcpServers` role-frontmatter shape and forwarding rules.

## Source Attribution
- JSONbored/awesome-claude — https://github.com/JSONbored/awesome-claude (~268 stars): curated registry of Claude ecosystem assets; claims a read-only `npx awesome-claude-mcp` MCP server. The npm package `awesome-claude-mcp` did NOT resolve on `npm view` as of 2026-06-21 (E404), so MCP wiring is documented-but-deferred pending package-name verification.
