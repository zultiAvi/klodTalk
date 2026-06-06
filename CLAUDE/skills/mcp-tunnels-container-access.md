---
skill_name: mcp-tunnels-container-access
triggers:
  - A Dockerized KlodTalk agent needs to reach a host-side or private-network MCP server
  - Wanting to avoid baking MCP credentials (e.g. GITHUB_TOKEN) into the agent image
  - An MCP tool returns a very large payload and you need to know where it goes
summary: "MCP tunnels (Research Preview — advisory only) let a containerized agent reach a private/host-side MCP server without mounting credentials into the image; managed-agent MCP config can be hot-updated on active sessions, and MCP outputs over 100K tokens spill to a sandbox file."
---

# Skill: MCP Tunnels for Containerized Agent Access

## Quick Reference
- MCP tunnels (Research Preview) connect an agent to MCP servers inside a private network / on the host.
- Status: RESEARCH PREVIEW — treat as advisory; evaluate before relying on it in the nightly pipeline.
- KlodTalk runs each agent in an isolated Docker container; instincts prefer `@github/mcp-server` (env `GITHUB_TOKEN`).
- Managed-agent MCP config can be hot-updated on ACTIVE sessions (no restart needed).
- MCP outputs over 100K tokens spill to a sandbox file (pairs with `large-output-spill.md`).

## When to Use
- A containerized agent needs a host-side or private-network MCP server (e.g. a host GitHub MCP) and you do NOT want to bake the token into the image or mount secrets per container.
- You are evaluating how to surface an internal/private MCP endpoint to isolated agents.

## The KlodTalk Use Case
- Today, giving a container access to a GitHub MCP means provisioning `GITHUB_TOKEN` into that container. MCP tunnels are the supported path to instead reach a host-side/private MCP server, keeping credentials off the image.
- Because tunnels are preview-stage, do NOT rewire the container build for them yet — document the pattern, prototype behind a flag, and confirm stability first.

## Notes
- Hot-update: managed-agent MCP configuration changes apply to active sessions, so an MCP endpoint can be added/changed mid-run.
- Large output: any MCP tool result exceeding ~100K tokens is written to a sandbox file rather than streamed inline — read it selectively, same discipline as `large-output-spill.md`.

## Cross-References
- `mcp-frontmatter.md` — declaring MCP servers in role frontmatter (forward `mcpServers` only).
- `github-mcp-scout.md` — the preferred `@github/mcp-server` + `GITHUB_TOKEN` setup tunnels would complement.
- `large-output-spill.md` — the matching >100K-token spill discipline.

## Source
MCP tunnels research preview + GitHub MCP guidance — https://docs.anthropic.com/en/agents-and-tools/mcp-tunnels/overview (platform.claude.com / API release notes, 2026-05-19).
