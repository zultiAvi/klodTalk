# Team: Migration

A safety-first team for database schema migrations, API migrations, and data transformations. Uses Opus throughout for high-stakes planning, implementation, and review. Enforces idempotency, rollback plans, and backward compatibility.

## Members

| Name | Role | Model | Optional |
|------|------|-------|----------|
| planner | planner | opus | |
| coder | coder | opus | |
| reviewer | reviewer | opus | |
| executor | executor | sonnet | yes |
| validator | validator | sonnet | yes |

## Pipeline

1. **planner** — Analyze the migration request. Classify the migration type (schema, data, API). Write a plan that includes: migration steps, rollback plan, backward compatibility analysis, and risk assessment.
2. **coder** — Implement the migration following the plan. Every migration script must be idempotent and include a rollback script.
3. **reviewer** — Review the migration for correctness, safety, and completeness. Verify all Special Rules are followed.
   - Review loop: if changes required, send back to **coder** for fixes.
   - Max iterations: **3**
4. **executor** (optional) — Run the migration in a test environment or dry-run mode. Capture all output including row counts and timing.
5. **validator** (optional) — Validate execution results: verify data integrity, check rollback works, confirm no regressions. Only runs if the executor ran.
   - Review loop: if CODER_FIX_REQUIRED, send back to **coder** for fixes, then re-execute and re-validate. If REPLANNING_REQUIRED, restart from **planner**.
   - Max iterations: **2**

## Special Rules

**These rules apply to ALL pipeline members and to the orchestrator itself. The orchestrator MUST include these Special Rules verbatim in every sub-agent prompt.**

- **Idempotency required**: Every migration script MUST use guards (`IF NOT EXISTS`, `IF EXISTS`, `ON CONFLICT DO NOTHING`, etc.) so it can be safely re-run without side effects.
- **Mandatory rollback plan**: The planner MUST include a rollback plan for every migration step. The coder MUST implement a corresponding rollback script or reversible migration. If a step is irreversible (e.g., dropping a column with data), the planner must explicitly flag it as irreversible and justify why.
- **No unbatched large-table DML**: Any `UPDATE`, `DELETE`, or `INSERT ... SELECT` that may affect more than 10,000 rows MUST be batched (e.g., loop with `LIMIT` or chunk by ID range). Include estimated row counts in the plan.
- **Backward compatibility**: API migrations MUST maintain backward compatibility during the transition period. Old clients must continue to work. If breaking changes are unavoidable, the plan must include a deprecation/versioning strategy.
- **Proof of non-use before drops**: Column drops, table drops, or API endpoint removals require evidence that the target is no longer in use (grep for references, query logs, or explicit justification).
- **Executor tests the migration**: When the executor step runs, it MUST execute the migration (not just lint it) and verify the result — check that tables/columns exist, data is correct, and the rollback script also works.
