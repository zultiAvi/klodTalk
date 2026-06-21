---
skill_name: verify-scouted-mcp-package
triggers:
  - A nightly scout / evaluator recommends adding a new MCP server to a role's frontmatter
  - About to wire an `npx`-launched MCP package into teams/roles/*.md
  - Diagnosing why a role's MCP startup fails on every nightly run
summary: "Before wiring any scouted MCP server into a role's `mcpServers` frontmatter, confirm its launch command resolves (`npm view <pkg> version` for npx packages). Scout findings hallucinate package names; a non-resolving entry makes `npx -y` fail on EVERY unattended run and can break the role. If it does not resolve, keep the idea doc-only."
---

# Skill: Verify a Scouted MCP Package Before Wiring It Into a Role

## When to Use
Whenever a scout or evaluator proposes adding a new MCP server (especially an `npx`-launched one) to a KlodTalk role's `mcpServers` frontmatter. Scout findings frequently misname packages or invent ones that do not exist on npm.

## Why This Matters
Roles like `github_scout` run unattended nightly. A `mcpServers` entry pointing at a non-existent package makes `npx -y <pkg>` fail on every launch and can break the role's MCP startup — strictly worse than not adding it. The package name in a scout finding is a *claim*, not a fact.

## Instructions
1. **Verify the launch target resolves before editing any frontmatter:**
   ```bash
   npm view <package-name> version      # npx-launched MCP servers
   # E404 / "is not in this registry"  => DO NOT wire it
   ```
   For non-npm launchers (a binary, a `uvx` package, a git URL), run the equivalent existence check (`which`, `uvx --help <pkg>`, `git ls-remote`).
2. **If it resolves:** add the entry alongside existing servers, preserving valid YAML and any `${TOKEN}` env interpolation (see `mcp-frontmatter.md`). Use the EXACT name the check resolved.
3. **If it does NOT resolve (or the name is uncertain):** keep the role frontmatter UNCHANGED. Capture the idea as a doc-only skill that records the registry/repo, the exact verification command, the failing result + date, and a conditional wiring snippet to apply once the name is confirmed (see `awesome-claude-registry-mcp.md` as the worked example).
4. **State the verification result explicitly** in `coder_output.txt` (command + output) so the reviewer can confirm which path you took.

## Cross-References
- `mcp-frontmatter.md` — `mcpServers` frontmatter shape; only `mcpServers`/`disallowedTools` are forwarded.
- `github-mcp-scout.md` — the existing authenticated `@github/mcp-server` entry.
- `awesome-claude-registry-mcp.md` — worked example where `npm view` returned E404 and wiring was deferred.
