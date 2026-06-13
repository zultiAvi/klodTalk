---
skill_name: security-auditor-role
triggers:
  - Adding a dedicated read-only Security Auditor step to a team pipeline
  - Reusing the OWASP/secrets/CVE/privilege-escalation audit role on another team
  - Wiring the cve_intel MCP into a non-reviewer role
summary: "Read-only Security Auditor role (teams/roles/security_auditor.md) sits between Coder and Reviewer; denies Bash/Edit/MultiEdit/NotebookEdit but KEEPS Write, reuses the cve_intel MCP gated by KLODTALK_SECURITY_MCP, and emits security_audit.md with BLOCKER/WARNING/INFO lines for the orchestrator loop."
---

# Skill: Security Auditor Role

## Quick Reference
- Role file: `teams/roles/security_auditor.md` (inherits `base.md`).
- Tools: read-only — `disallowedTools: [Bash, Edit, MultiEdit, NotebookEdit]`; **Write kept** so it can emit its report.
- MCP: same `cve_intel` (`@mukul975/cve-mcp-server`) the reviewer uses, gated operator-side by `KLODTALK_SECURITY_MCP=1` + `NVD_API_KEY`.
- Output: `/workspace/.klodTalk/team/current/security_audit.md`.
- Pipeline slot: between **coder** and **reviewer** (see `teams/teams/security.md`).

## When to Use
- A team runs arbitrary code / produces production patches and needs systematic security coverage rather than the reviewer's opportunistic checks.
- You want a security pass that the orchestrator's BLOCKER loop can route back to the Coder before the quality review.

## What the Role Does
1. OWASP Top-10 pass over changed files.
2. Secrets/regex scan (same families as `post-tool-output-sanitize.md`).
3. Dependency CVE check via `cve_intel` MCP (EPSS + CISA KEV); degrades gracefully to model knowledge when the MCP/key is absent.
4. Privilege-escalation review (`shell=True`, `eval`/`exec`, `sudo`, file modes, container privilege).

## Output Convention (matters for the loop)
Lines are prefixed `BLOCKER:` / `WARNING:` / `INFO:` with `file:line — description`. The orchestrator's BLOCKER-scan (same convention as the reviewer) routes any `BLOCKER:` back to the Coder; zero blockers → `AUDIT RESULT: PASS`. Keep the prefix grammar exact or the loop will not trigger.

## Reusing on Another Team
1. Add `security_auditor` to the team's Members table AND a numbered Pipeline step (don't renumber referenced steps mid-stream — see `orchestrator-step-edits.md`).
2. Place it between implementation and review so findings are fixed before quality review.
3. Document the `KLODTALK_SECURITY_MCP` requirement in the team note (as in `security.md`).

## Related
- `CLAUDE/skills/security-intel-mcp.md` — the `cve_intel` MCP and its env-var gate.
- `CLAUDE/skills/security-guidance-plugin.md` — complementary security guidance.
- `CLAUDE/skills/role-inheritance-pattern.md` — the `<!-- inherits: base.md -->` convention.
- `CLAUDE/skills/orchestrator-step-edits.md` — editing pipeline step numbers safely.

## Source
0ldh/claude-code-agents-orchestra — https://github.com/0ldh/claude-code-agents-orchestra; alirezarezvani/claude-skills — https://github.com/alirezarezvani/claude-skills (~17k stars). Both expose the missing dedicated Security Auditor role in KlodTalk's taxonomy.
