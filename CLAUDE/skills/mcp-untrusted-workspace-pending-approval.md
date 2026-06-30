---
skill_name: mcp-untrusted-workspace-pending-approval
triggers:
  - An MCP server shows "Pending approval" in a cloned or mounted external repo
  - A KlodTalk agent reports MCP tool unavailability when working on a third-party codebase
  - Diagnosing why a repo's committed `.mcp.json` servers did not auto-start
summary: "As of Claude Code v2.1.196, `claude mcp list`/`get` no longer auto-spawn `.mcp.json` servers a repo self-approved via a committed `.claude/settings.json`; untrusted workspaces show an `⏸ Pending approval` notice. The server IS available once approved — the agent has NOT failed. Treat the notice as expected when working in cloned/mounted external repos; for known-trusted repos, declare the server under the project's own operator-controlled `.claude/settings.json` `mcpServers` instead."
---

# Skill: MCP Untrusted-Workspace Pending-Approval Behavior

## When to Use
When an MCP server shows `⏸ Pending approval` in a repo that KlodTalk cloned or mounted under `/workspace`, or when a KlodTalk agent reports that an MCP tool is unavailable while working on a third-party codebase. This is a CLI **behavior change**, not a connectivity failure — do not debug it as one.

## Version Gate
- Requires Claude Code **>= 2.1.196** (the floor pinned in `required-minimum-version-pin.md`).
- Before v2.1.196, `.mcp.json` servers that a repo self-approved via its own committed `.claude/settings.json` were silently auto-spawned even in untrusted workspaces. v2.1.196 closes that hole.

## What "Pending Approval" Means
v2.1.196 ships this security hardening (verbatim from the CHANGELOG):

> `claude mcp list`/`get` no longer spawn `.mcp.json` servers that a repo self-approved via a committed `.claude/settings.json`; untrusted workspaces show `⏸ Pending approval`.

The key points:
- A repo can no longer grant *itself* MCP trust by committing a `.claude/settings.json` that approves its own `.mcp.json` servers. Trust must come from the operator (the user running the CLI), not from the untrusted repo's own files.
- `⏸ Pending approval` means the server **is configured and available** — it is simply waiting for the user to approve it. The agent has **not** failed and the MCP package is **not** broken or misnamed.
- This is distinct from a real MCP startup failure (E404 package, bad launch command), which `verify-scouted-mcp-package.md` covers.

## KlodTalk Impact
KlodTalk agent containers can work on arbitrary repos mounted under `/workspace`. Nightly coder/scout agents that clone an external repo shipping a `.mcp.json` will, on v2.1.196+, see `⏸ Pending approval` for those servers instead of them silently starting.

**Treat this as expected behavior, not an error.** Do not:
- Report it as an "MCP connection failure" in `coder_output.txt`.
- Run `npm view` / re-verify the package as if it were misnamed (the package is fine).
- Block the task or spend a fix round debugging MCP connectivity.

If the task genuinely requires the server's tools, surface the pending-approval state to the operator (Zulti) as a one-line note rather than aborting.

## Mitigation for Known-Trusted Repos
When KlodTalk knowingly trusts a mounted repo and wants its MCP servers active without a per-run approval prompt, declare the server under the **project's own** `.claude/settings.json` `mcpServers` key — i.e. the operator-controlled workspace settings file at `/workspace/.claude/settings.json`, NOT the untrusted repo's committed copy. Servers declared in the operator's own settings are trusted by definition and bypass the untrusted-workspace gate:

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/workspace"]
    }
  }
}
```

This is the operator declaring trust explicitly, which is exactly what the v2.1.196 hardening intends. Do not work around the gate by editing the untrusted repo's committed `.claude/settings.json` — that is the self-approval path the hardening deliberately closes.

## Cross-References
- `required-minimum-version-pin.md` — the v2.1.196 floor that introduces this behavior.
- `verify-scouted-mcp-package.md` — for a *real* MCP startup failure (non-resolving package); a pending-approval notice is NOT that.
- `mcp-frontmatter.md` — how KlodTalk roles declare `mcpServers` (and why frontmatter is forward-looking).

## Source
Claude Code v2.1.196 (2026-06-29) — https://github.com/anthropics/claude-code/releases/tag/v2.1.196 (github.com/anthropics/claude-code). Behavior verified against the raw CHANGELOG.md.
