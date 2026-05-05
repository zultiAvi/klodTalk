# Team: Single-Module

The weaker team suitable for a single module simple work. A planner designs the approach, a coder implements it, and a reviewer verifies the result. Optionally includes execution, validation, and security review when the task warrants it.

## enabled

## Members

| Name | Role | Model  | Optional |
|------|------|--------|----------|
| planner | planner | opus   | |
| coder | coder | sonnet | |
| qa_analyst | qa_analyst | sonnet | |
| reviewer | reviewer | sonnet | |

## Pipeline

1. **planner** — Analyze the request, classify as simple/complex, write implementation plan.
2. **coder** — Implement the plan, commit changes.
3. **qa_analyst** — Read the coder's changed files and the existing test suite. Identify uncovered code paths, missing edge case tests, and regression scenarios. Write findings to `qa_analyst_output.txt`.
4. **reviewer** — Review the implementation against the plan.
   - Review loop: if changes required, send back to **coder** for fixes.
   - Max iterations: **3**
