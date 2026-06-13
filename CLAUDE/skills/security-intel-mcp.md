---
skill_name: security-intel-mcp
triggers:
  - A Reviewer role on a security-focused team needs live CVE / advisory data
  - Adding optional MCP server access for dependency-vulnerability checks
  - Setting up env-var dispatch for an opt-in MCP server (no Dockerfile changes)
summary: "Optional `cve_intel` MCP for the Reviewer role -- opt in via `KLODTALK_SECURITY_MCP=1` + `NVD_API_KEY`; absent keys degrade reviewer gracefully."
---

# Skill: Security Intelligence MCP for the Reviewer Role

## Quick Reference
- Package: `mukul975/cve-mcp-server` -- https://github.com/mukul975/cve-mcp-server
- Tools provided: CVE lookup, EPSS scoring, CISA KEV, MITRE ATT&CK, VirusTotal (key-gated), Shodan (key-gated).
- Operator opt-in: export `KLODTALK_SECURITY_MCP=1` on the agent container. **Required**: `NVD_API_KEY`. **Optional**: `VIRUSTOTAL_API_KEY`.
- Graceful degradation: missing keys -> the MCP server starts but tools return errors; the Reviewer logs the failure and proceeds with training-knowledge review (no hard fail).

## When to Use
- Security-focused team pipelines only -- e.g. `teams/teams/security.md`.
- Do **not** add this MCP to generic Coder / Reviewer roles. The CVE feed is noise for non-security review and consumes the reviewer's context budget.

## Pattern (Env-Var Dispatch, Not Frontmatter Conditional)

Role `.md` frontmatter only forwards `mcpServers` and `disallowedTools` (see `mcp-frontmatter.md` and instinct #5 in the operator playbook). The frontmatter cannot conditionally enable a server -- the operator chooses whether to set `NVD_API_KEY` and `KLODTALK_SECURITY_MCP=1`.

The conditionality therefore lives in the **operator-side container env**, mirroring `plugin-dir-dispatch.md`:

1. Frontmatter declares the `cve_intel` MCP entry unconditionally.
2. When operator sets `KLODTALK_SECURITY_MCP=1` + `NVD_API_KEY=<key>`, the MCP starts with full functionality.
3. When the operator does NOT set the keys, the MCP server still starts but its tool calls return error responses. The Reviewer treats this as a soft signal ("CVE intel unavailable -- relying on training knowledge for this review").

## Operator Setup

```bash
# On the agent container (docker-compose env, -e flag, or project config):
export KLODTALK_SECURITY_MCP=1
export NVD_API_KEY=<your-nvd-key>          # required for live CVE queries
export VIRUSTOTAL_API_KEY=<optional-key>   # optional, enables VT enrichment
```

Do **NOT** modify `Dockerfile.agent` (pinned). The env block belongs in the operator's container env.

## Reviewer Workflow When MCP Is Active

When `NVD_API_KEY` is set, the Reviewer uses the `cve_intel` tools to:
- Look up CVEs touching dependencies named in the diff (`package.json`, `requirements.txt`, `Cargo.toml`).
- Cross-reference EPSS scores and CISA KEV listings on flagged CVEs.
- Add `BLOCKER:` lines for any dependency with an active CISA KEV listing.

When the MCP is unavailable (missing key or network error), the Reviewer logs a `WARNING:` noting that live CVE data was unreachable and proceeds with model-knowledge-only review.

## Related
- `security-auditor-role.md` -- the dedicated read-only Security Auditor role that reuses this same `cve_intel` MCP, gated identically.
- `mcp-frontmatter.md` -- the unconditional frontmatter forwarding contract.
- `codebase-search-mcp.md` -- another MCP server added to Reviewer (sibling pattern).
- `plugin-dir-dispatch.md` -- the env-var dispatch precedent (`KLODTALK_PLUGIN_DIR`); same operator-side conditionality model.

## Source
- mukul975/cve-mcp-server -- https://github.com/mukul975/cve-mcp-server
