---
skill_name: container-network-allowlist
triggers:
  - Wanting to restrict which domains/CIDRs an agent container can reach
  - Designing a per-project network firewall for KlodTalk Docker agents
  - Hardening a project workspace against data exfiltration over the network
summary: "Per-project Docker network allowlist: drop-all default plus explicit ACCEPT per domain/CIDR, configured via a `network_allowlist` field on a project entry and applied by run_agent.py as a mounted iptables init script (needs --cap-add NET_ADMIN). Documentation only — server wiring is a MANUAL follow-up."
---

# Skill: Per-Project Container Network Allowlist

## When to Use
When a project's agent container should only reach an explicit set of hosts (e.g.
`github.com`, `api.anthropic.com`, an internal registry) and nothing else — to limit
exfiltration risk for sensitive workspaces. Documentation/design only; the simpler
coarse alternative below may be enough.

## Design

### 1. Config field (proposed) on a `config/projects.json` entry
```json
{
  "name": "my_project",
  "network_allowlist": [
    "github.com",
    "api.anthropic.com",
    "10.0.0.0/8"
  ]
}
```
Absent or `[]` → no firewall applied (current behavior, unrestricted).

### 2. How `server/run_agent.py` would apply it
- Generate an iptables init script: default policy `DROP` on OUTPUT, then one
  `ACCEPT` rule per allowlist domain (resolved to IPs at container start) or CIDR,
  plus `ACCEPT` for established/related and loopback/DNS.
- Mount the script into the container and run it on startup.
- Requires the container to be launched with `--cap-add NET_ADMIN` (iptables needs it).
- Domain entries must be re-resolved if DNS rotates; CIDR entries are stable.

### 3. Coarse alternative (simpler, no iptables)
`docker network create --internal <net>` and attach the container to it — blocks ALL
external egress (intra-container only). Use when you need "no internet" rather than a
selective allowlist; it needs no NET_ADMIN and no per-domain script.

## Status
Server wiring (`run_agent.py`, projects.json schema) is a **MANUAL follow-up** — OUT of
auto-scope. This skill documents the pattern only.

## Related
- `config/CLAUDE.md` — project-configuration schema where `network_allowlist` is described.

## Source
RchGrav/claudebox — https://github.com/RchGrav/claudebox (1.1k stars), per-project container network firewall allowlist pattern.
