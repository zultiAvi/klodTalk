# Team: Documentation

A read-only documentation team. Reads source code and produces documentation without modifying any executable code. Uses Sonnet for efficient documentation generation and review.

## Members

| Name | Role | Model |
|------|------|-------|
| documenter | documenter | sonnet |
| reviewer | reviewer | sonnet |

## Pipeline

1. **documenter** — Read the relevant source code and produce the requested documentation (README, API docs, architecture overview, changelog, etc.).
2. **reviewer** — Review the documentation for accuracy, completeness, and clarity. Cross-check all claims against the source code.
   - Review loop: if changes required, send back to **documenter** for fixes.
   - Max iterations: **2**

## Special Rules

**These rules apply to ALL pipeline members and to the orchestrator itself. The orchestrator MUST include these Special Rules verbatim in every sub-agent prompt.**

- **No executable code changes**: No team member may create, modify, or delete executable source files (`.py`, `.js`, `.ts`, `.sh`, `.java`, `.kt`, etc.), configuration files that affect runtime behavior, build scripts, Dockerfiles, or CI/CD pipelines. Documentation files (`.md`, docstrings, diagram sources) are the only permitted outputs.
- **Accuracy over volume**: Every factual claim in the documentation must be verifiable from the source code. If something is unclear, omit it or flag it as needing human verification rather than guessing.
- **Read before writing**: The documenter MUST read the relevant source files before writing documentation about them. Do not document from memory or assumptions.
- **Reviewer blocks on inaccuracy**: The reviewer MUST flag `CHANGES REQUIRED` if any factual statement in the documentation contradicts the source code. Style and completeness issues are secondary to accuracy.
- **Always COMPLEX**: Always classify the task as COMPLEX. Never take the SIMPLE path. Never implement directly.
