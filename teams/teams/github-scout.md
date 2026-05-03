# Team: GitHub Scout

Automated GitHub scouting team for the nightly routine. A scout searches GitHub for relevant repos and ideas, an evaluator ranks them, a coder implements the best ones, and a reviewer verifies.

## enabled

## Members

| Name | Role | Model | Optional |
|------|------|-------|----------|
| scout | github_scout | sonnet | |
| evaluator | idea_evaluator | sonnet | |
| coder | coder | opus | |
| reviewer | reviewer | sonnet | |

## Pipeline

1. **scout** -- Search GitHub for repos and ideas matching configured tags. Prefer higher-star repos but include promising low-star ones. Write findings to `.klodTalk/team/current/scout_findings.md`.
2. **evaluator** -- Read scout findings, evaluate relevance/feasibility/impact, rank ideas, select top candidates. Write evaluation to `.klodTalk/team/current/evaluated_ideas.md`.
3. **coder** -- Implement the top-ranked ideas from the evaluator's shortlist. Focus on small, self-contained improvements. In `coder_output.txt`, include a **Source Attribution** section listing each implemented idea and the GitHub repo it came from (name, URL, stars).
4. **reviewer** -- Review the implementation for correctness, safety, and adherence to codebase conventions.
   - Review loop: if changes required, send back to **coder** for fixes.
   - Max iterations: **2**
