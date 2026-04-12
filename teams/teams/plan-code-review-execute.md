# Team: Plan-Code-Review-Execute

Five-role pipeline with execution and validation. The planner designs the approach, the coder implements it, the reviewer checks code quality, the executor runs everything, and the validator verifies the results.

## Members

| Name | Role | Model |
|------|------|-------|
| planner | planner | opus |
| coder | coder | opus |
| reviewer | reviewer | sonnet |
| executor | executor | sonnet |
| validator | validator | sonnet |

## Pipeline

1. **planner** — Analyze the request, write the implementation plan.
2. **coder** — Implement the plan, commit changes.
3. **reviewer** — Review the implementation for correctness and quality.
   - Review loop: if changes required, send back to **coder** for fixes.
   - Max iterations: **3**
4. **executor** — Run the code: tests, builds, scripts. Capture all output.
5. **validator** — Validate execution results against the plan's success criteria.
   - Review loop: if `CODER_FIX_REQUIRED`, send back to **coder** for fixes, then re-execute and re-validate. If `REPLANNING_REQUIRED`, restart from **planner**.
   - Max iterations: **2**
