# Team: TDD

Test-driven development team. The coder follows strict red-green-refactor methodology.

## enabled

## Members

| Name | Role | Model | Optional |
|------|------|-------|----------|
| planner | planner | sonnet | |
| coder | coder_tdd | opus | |
| reviewer | reviewer_test_runner | sonnet | |
| executor | executor | sonnet | yes |

## Pipeline

1. **planner** — Analyze the request, write implementation plan with test cases to cover.
2. **coder** — Implement using TDD: write failing tests, implement to pass, refactor.
3. **reviewer** — Run the test suite and review the code.
   - Review loop: if changes required, send back to **coder** for fixes.
   - Max iterations: **3**
