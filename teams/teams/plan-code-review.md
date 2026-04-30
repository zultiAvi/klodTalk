# Team: Plan-Code-Review

The default balanced team. A planner designs the approach, a coder implements it, and a reviewer verifies the result. Optionally includes execution, validation, and security review when the task warrants it.

## enabled

## Members

| Name | Role | Model | Optional |
|------|------|-------|----------|
| planner | planner | opus | |
| coder | coder | opus | |
| reviewer | reviewer | sonnet | |
| executor | executor | sonnet | yes |
| validator | validator | sonnet | yes |
| security_reviewer | reviewer | sonnet | yes |

## Pipeline

1. **planner** — Analyze the request, classify as simple/complex, write implementation plan.
2. **coder** — Implement the plan, commit changes.
3. **reviewer** — Review the implementation against the plan.
   - Review loop: if changes required, send back to **coder** for fixes.
   - Max iterations: **3**
4. **executor** (optional) — Run the code: tests, builds, scripts. Capture all output. The orchestrator runs this when the planner sets NEEDS_EXECUTION=true in plan_meta.txt, or when the task clearly involves runnable code.
5. **validator** (optional) — Validate execution results against the plan's success criteria. Only runs if the executor ran.
   - Review loop: if CODER_FIX_REQUIRED, send back to **coder** for fixes, then re-execute and re-validate. If REPLANNING_REQUIRED, restart from **planner**.
   - Max iterations: **2**
6. **security_reviewer** (optional) — Security-focused review of the implementation. The orchestrator runs this when the task involves authentication, user input handling, data exposure, or other security-sensitive areas.
