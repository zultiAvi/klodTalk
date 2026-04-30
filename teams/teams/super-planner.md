# Team: Super-Planner

An ideation-focused team that does NOT write any code. It generates, critiques, and refines implementation ideas over multiple rounds, then produces a detailed plan for another team to execute.

## enabled

## Members

| Name | Role | Model |
|------|------|-------|
| idea_maker | idea_maker | opus |
| idea_reviewer | idea_reviewer | opus |
| super_planner | super_planner | opus |

## Pipeline

1. **idea_maker** — Analyze the task (assume it's complicated with hidden issues). Generate 5 implementation ideas ranked from best to far-fetched. Write them to plan.md with IS_SIMPLE=false in plan_meta.txt.

2. **idea_reviewer** — Critically evaluate all 5 ideas: feasibility, completeness, risks, effort vs. value. Return detailed remarks and recommend which ideas to keep, drop, or merge.
   - Review loop: send remarks back to **idea_maker** for refinement.
   - Max iterations: **5**
   - Round 2: idea_maker narrows to best 3 ideas, modifies per remarks, develops them further.
   - Round 3+: idea_maker and reviewer converge on the best single idea with full detail.
   - Approve (NO_ISSUES_FOUND) only when a clear winner is identified and detailed enough for planning.
   - **Important for review loop**: In rounds 2+, the idea_maker's refined output is in coder_output.txt (not plan.md). The reviewer should read coder_output.txt for the latest ideas.

3. **super_planner** — Take the winning idea and produce a comprehensive, self-contained implementation plan. The plan must be detailed enough for a separate planner+coder+reviewer team to execute without access to the ideation rounds.

## Special Rules

**These rules apply to ALL pipeline members and to the orchestrator itself. The orchestrator MUST include these Special Rules verbatim in every sub-agent prompt.**

- **No code**: No team member (idea_maker, idea_reviewer, super_planner, or any other sub-agent) may create, modify, or delete any source code files in the repository. This is an ideation-only team. If a sub-agent writes code, the pipeline has failed.
- **No commits**: Since no code is written, no git commits should be made at any pipeline stage.
- **No code reviews**: Reviewers evaluate the QUALITY OF IDEAS, not code changes. "No implementation exists" is the expected and correct state. Do NOT flag the absence of code as an issue.
- **Focus on ideas**: The value of this team is in thorough analysis, creative thinking, and convergence on the best approach — not implementation.
- **Minimum 3 rounds**: The idea_reviewer should NOT approve before at least 3 rounds of idea_maker ↔ idea_reviewer exchange.
- **Review loop fix role**: When the idea_reviewer requests changes, the orchestrator must use **idea_maker** (not coder) as the fix role in the review loop.
