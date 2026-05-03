# Team: TDD

Test-driven development team. The coder follows strict red-green-refactor methodology.

## enabled

## Members

| Name | Role | Model | Optional |
|------|------|-------|----------|
| planner | planner | sonnet | |
| coder | coder_tdd | opus | |
| qa_analyst | qa_analyst | sonnet | |
| reviewer | reviewer_test_runner | sonnet | |
| executor | executor | sonnet | yes |

## Pipeline

1. **planner** — Analyze the request, write implementation plan with test cases to cover.
2. **coder** — Implement using TDD: write failing tests, implement to pass, refactor.
3. **qa_analyst** — Read the coder's changed files and the existing test suite. Identify uncovered code paths, missing edge case tests, and regression scenarios. Write findings to `qa_analyst_output.txt`.
4. **reviewer** — Run the test suite and review the code.
   - Review loop: if changes required, send back to **coder** for fixes.
   - Max iterations: **3**
5. **executor** (optional) — Run the code: tests, builds, scripts. Capture all output. The orchestrator runs this when the planner sets NEEDS_EXECUTION=true in plan_meta.txt, or when the task clearly involves runnable code.
