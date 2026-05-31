---
skill_name: fresh-context-evaluator
triggers:
  - Building or tuning a code-review stage that must be free of context contamination
  - Adding a second-opinion reviewer to nightly or unattended pipelines
  - Choosing between the in-context reviewer.md and a fresh-context evaluator
summary: "Spawn the reviewer in a fresh context window with read-only tools and a default-FAIL rubric so code review is not biased by the coder's framing."
---

# Skill: Fresh-Context Evaluator Subagent

## Quick Reference
- Role file: `teams/roles/reviewer_fresh_context.md`
- Tool restrictions: `disallowedTools: [Bash, Write, Edit, MultiEdit, NotebookEdit]`
- Default verdict per criterion: **FAIL** until evidence file is read.
- Output file: `/workspace/.klodTalk/team/current/reviewer_output.txt` (same path/format as the regular reviewer, so existing tooling keeps working).
- Pipeline opt-in only: existing teams (including `nightly_scout.md`) are **not modified**; teams that want this stage add the role explicitly.

## When to Use
- Nightly / unattended pipelines where no human spot-checks intermediate output.
- Optimizer or refactor pipelines where the coder may have over-trimmed something the reviewer would otherwise overlook because "we just discussed it".
- Any team that has already run a regular `reviewer` and wants a second, blind pass for high-confidence approvals.

Do **not** swap this in for the regular `reviewer.md` blindly — the regular reviewer has access to the coder's context and is faster for interactive workflows. The fresh-context evaluator is a **complement**, not a replacement.

## Instructions

### Role Contract
1. The role is spawned in a fresh context window — it has no shared history with the coder.
2. Its only inputs are artefacts on disk: `in_message.txt`, `plan.md`, `changed_files.txt`, `*_output.txt`, and the source files listed in the changed-files list.
3. Every rubric criterion starts at FAIL. The role may only mark PASS after citing the file and line it actually read.
4. Tool restrictions (`disallowedTools`) are enforced by `server/run_agent.py` per `disallowed-tools-frontmatter.md` — the camelCase form is required.

### Output Compatibility
Output is written to `/workspace/.klodTalk/team/current/reviewer_output.txt` in the **same schema** the regular reviewer uses (per `reviewer-exit-condition-scoring.md`). This means:
- `REVIEW RESULT: APPROVED` / `REVIEW RESULT: CHANGES REQUIRED`
- One `EXIT_CONDITION_SCORE: <n>/10` line in `## Exit Condition Check`
- Issue lines prefixed `BLOCKER:` / `WARNING:` / `SUGGESTION:`

Downstream consumers (the orchestrator review loop, the nightly review-fix loop) do not need to change.

### Opting a Team In
**Important — do NOT modify existing team files.** The role is available for any team that explicitly adds it to its pipeline. To opt in, edit your own team `.md` file (e.g. `teams/teams/my_team.md`) and add a pipeline step that references `reviewer_fresh_context` after the coder. Example skeleton:

```
| Name      | Role                     | Model   | Optional |
|-----------|--------------------------|---------|----------|
| coder     | coder                    | sonnet  | no       |
| reviewer  | reviewer                 | sonnet  | no       |
| evaluator | reviewer_fresh_context   | opus    | yes      |
```

The fresh-context evaluator is typically marked **optional** in the members table so the orchestrator skips it for short interactive runs and only invokes it for nightly / unattended pipelines.

### Why Not Modify nightly_scout.md Directly
Editing `nightly_scout.md` to insert a new reviewer stage would change the behaviour of an existing, working team — risky for nightly automation that operators may be relying on. The safer path is to leave the role available and let team authors opt in deliberately. Future nightly cycles can add the stage once the role has been exercised on a lower-stakes team.

### Default-FAIL Rubric Reinforcement
The role prompt explicitly says: "Default assumption: FAIL. You must open and read the evidence file before marking any criterion as PASS." Combined with the required `## Fresh-Context Reading Log` section listing which files were opened, this makes drive-by APPROVAL verdicts visible — if the reading log is empty but the verdict is APPROVED, the orchestrator can treat the verdict as untrusted.

### Tool Restriction Layer
`disallowedTools` in role frontmatter is forwarded by `server/run_agent.py` to `claude --print` (instinct #7 — only `mcpServers` and `disallowedTools` are forwarded; other keys are no-ops). This is enforced at the CLI flag layer, so even if the prompt is jailbroken, the tools simply aren't registered.

## Related
- `teams/roles/reviewer.md` — the regular (context-sharing) reviewer.
- `disallowed-tools-frontmatter.md` — how the tool restriction is enforced.
- `reviewer-exit-condition-scoring.md` — the verdict format both reviewers must emit.
- `role-inheritance-pattern.md` — base.md inheritance via `<!-- inherits: base.md -->`.
- `pipeline-stage-isolation.md` — how the orchestrator isolates stages so a fresh context window is meaningful.

## Source
anthropics/cwc-long-running-agents — https://github.com/anthropics/cwc-long-running-agents (102 stars, official Anthropic, May 2026). The standalone evaluator subagent pattern: spawn the reviewer with a fresh context, read-only tools, rubric-based grading, default-FAIL until evidence is opened.
