# Team: Refactor

Two-phase refactoring team. First refactor the code, then validate with tests.

## Members

| Name | Role | Model | Optional |
|------|------|-------|----------|
| planner | planner | sonnet | |
| coder | coder | opus | |
| reviewer | reviewer | sonnet | |
| test_coder | coder_unit_test | opus | |
| test_reviewer | reviewer_test_runner | sonnet | |
| executor | executor | sonnet | yes |

## Pipeline

1. **planner** — Analyze the code to refactor, plan the restructuring approach.
2. **coder** — Implement the refactoring changes.
3. **reviewer** — Review that behavior is preserved and code quality improved.
   - Review loop: if changes required, send back to **coder** for fixes.
   - Max iterations: **3**
4. **test_coder** — Write unit tests to validate the refactored code.
5. **test_reviewer** — Run the test suite and review test coverage.
   - Review loop: if changes required, send back to **test_coder** for fixes.
   - Max iterations: **2**
