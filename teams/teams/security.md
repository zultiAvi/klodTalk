# Team: Security

Security-focused team. Uses Opus throughout for deeper threat analysis and secure implementation.

## enabled

## Members

| Name | Role | Model |
|------|------|-------|
| planner | planner | opus |
| coder | coder | opus |
| reviewer | reviewer | sonnet |

> Reviewer in this pipeline gets the CVE intel MCP when `KLODTALK_SECURITY_MCP=1` (with `NVD_API_KEY`) is set on the agent container. See `CLAUDE/skills/security-intel-mcp.md`.

## Pipeline

1. **planner** — Analyze the request with security threat modeling. Include OWASP concerns in the plan.
2. **coder** — Implement with security best practices. Validate inputs, sanitize outputs, avoid common vulnerabilities.
3. **reviewer** — Security-focused code review. Check for injection, auth issues, data exposure, and OWASP top 10.
   - Review loop: if changes required, send back to **coder** for fixes.
   - Max iterations: **3**
