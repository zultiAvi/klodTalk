# Team: Debug

A debugging-focused team. The debugger reproduces the issue and diagnoses the root cause, then the coder fixes it following the debugger's suggested fix. The reviewer verifies the fix is correct. Optionally includes execution and validation.

## enabled

## Members

| Name | Role | Model | Optional |
|------|------|-------|----------|
| debugger | debugger | opus | |
| coder | coder | opus | |
| reviewer | reviewer | sonnet | |
| executor | executor | sonnet | yes |
| validator | validator | sonnet | yes |

## Pipeline

1. **debugger** — Reproduce the issue, diagnose root cause, write suggested fix to debugger_output.txt.
2. **coder** — Implement the fix from debugger_output.txt, commit changes.
3. **reviewer** — Review the fix against the debugger's diagnosis and suggested fix.
   - Review loop: if changes required, send back to **coder** for fixes.
   - Max iterations: **3**
4. **executor** (optional) — Run the code or tests to verify the fix resolves the issue.
5. **validator** (optional) — Validate that execution results confirm the bug is fixed and no regressions were introduced.
   - Review loop: if CODER_FIX_REQUIRED, send back to **coder** for fixes, then re-execute and re-validate. If REPLANNING_REQUIRED, restart from **debugger**.
   - Max iterations: **2**

## Special Rules

**These rules apply to ALL pipeline members and to the orchestrator itself. The orchestrator MUST include these Special Rules verbatim in every sub-agent prompt.**

- The coder MUST follow the Suggested Fix from debugger_output.txt. Do not ignore or reinterpret the debugger's diagnosis — implement the fix as specified unless it is clearly wrong, in which case explain the deviation in coder_output.txt.
- If debugger_output.txt contains `NO_ISSUE_FOUND`, the orchestrator MUST stop the pipeline immediately and report to the user that the debugger could not reproduce the issue. Do not proceed to the coder step.
- The debugger's diagnosis is the source of truth for the root cause. The coder implements the fix, the reviewer verifies it matches the diagnosis.
