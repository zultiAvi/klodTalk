# Team: Plan-Code-QA-Review

A quality-focused team. A planner designs the approach, a coder implements it, a QA analyst identifies test coverage gaps, and a reviewer verifies the result. The QA step catches missing tests before the reviewer signs off.

## disabled

## Members

| Name | Role | Model | Optional |
|------|------|-------|----------|
| planner | planner | sonnet | |
| coder | coder | opus | |
| qa_analyst | qa_analyst | sonnet | |
| reviewer | reviewer | sonnet | |

## Pipeline

1. **planner** — Analyze the request, classify as simple/complex, write implementation plan.
2. **coder** — Implement the plan, commit changes.
3. **qa_analyst** — Read the coder's changed files and the existing test suite. Identify uncovered code paths, missing edge case tests, and regression scenarios. Write findings to `qa_analyst_output.txt`.
4. **reviewer** — Review the implementation against the plan. If `qa_analyst_output.txt` shows `QA RESULT: GAPS FOUND`, treat unaddressed gaps as additional review items.
   - Review loop: if changes required, send back to **coder** for fixes.
   - Max iterations: **3**
