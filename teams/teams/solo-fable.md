# Team: Solo-Fable

Single-agent team running on Claude Fable 5 (`claude-fable-5`) — the most capable widely-released model. Like Solo-General, the agent has no fixed specialty: it reads the request and decides for itself how to handle it (plan, code, review, run, document, or any combination).

## enabled

## Members

| Name | Role | Model |
|------|------|-------|
| general | general | claude-fable-5 |

## Pipeline

1. **general** — Read the user's request and do whatever the agent judges to be right: investigate, plan, implement, run, verify, and document. The agent owns the entire task end-to-end.
