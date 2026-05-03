# Team: Unit Test

Write comprehensive unit tests for existing code. Does not modify implementation.

## enabled

## Members

| Name | Role | Model | Optional |
|------|------|-------|----------|
| planner | planner | sonnet | |
| coder | coder_unit_test | opus | |
| reviewer | reviewer_test_runner | sonnet | |
| executor | executor | sonnet | yes |

## Pipeline

1. **planner** — Identify what code needs test coverage, plan the test strategy.
2. **coder** — Write unit tests covering happy paths, edge cases, and error cases.
3. **reviewer** — Run the test suite and review test quality.
   - Review loop: if changes required, send back to **coder** for fixes.
   - Max iterations: **3**
