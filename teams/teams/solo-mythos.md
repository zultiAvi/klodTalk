# Team: Solo-Mythos

Single-agent team running on Claude Mythos 5 (`claude-mythos-5`) — a limited-availability top-tier model (Project Glasswing, invitation-only). Like Solo-General, the agent has no fixed specialty: it reads the request and decides for itself how to handle it (plan, code, review, run, document, or any combination).

## enabled

## Members

| Name | Role | Model |
|------|------|-------|
| general | general | claude-mythos-5 |

## Pipeline

1. **general** — Read the user's request and do whatever the agent judges to be right: investigate, plan, implement, run, verify, and document. The agent owns the entire task end-to-end.
