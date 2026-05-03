# Team: Solo-Planner

Single-agent planning team. Analyzes a task and delivers a detailed plan to the user. No code execution.

## enabled

## Members

| Name | Role | Model |
|------|------|-------|
| planner | planner | opus |

## Pipeline

1. **planner** — Analyze the request and produce a comprehensive plan. The plan is broadcast to the user via planner_message.txt and is the sole deliverable of this team.

## Special Rules

**These rules apply to ALL pipeline members and to the orchestrator itself. The orchestrator MUST include these Special Rules verbatim in every sub-agent prompt.**

- **No code**: The planner must NOT create, modify, or delete any source code files. Do not implement anything — even for tasks that seem simple.
- **No commits**: No git commits at any pipeline stage.
- **Always COMPLEX**: Always classify the task as COMPLEX. Never take the SIMPLE path. Never implement directly. *(This is intentionally redundant with "No code" and "Fixed metadata" — all three guard against the SIMPLE path at different layers: behavioral, data, and routing.)*
- **Human audience**: Your audience is the HUMAN USER who sent the request, not a Coder agent. Write the plan as a clear, actionable document that a person can follow. Do not reference downstream pipeline agents (Coder, Reviewer, etc.) — they do not exist in this team.
- **Plan delivery**: The plan written to plan.md is broadcast to the user via planner_message.txt — that broadcast is the primary deliverable the user sees. The out_message.txt final summary is a closing wrapper and may contain only an excerpt of the plan.
- **Fixed metadata**: Always write plan_meta.txt with: IS_SIMPLE=false, REVIEW_ITERATIONS=0, COMPLEXITY=medium, NEEDS_EXECUTION=false.
