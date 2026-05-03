# Team: Nightly Scout

Combined nightly scouting team. A website scout checks Claude/Anthropic official channels, a GitHub scout searches for community repos, an evaluator ranks all findings together, a coder implements the best ones, and a reviewer verifies.

## enabled

## Members

| Name | Role | Model | Optional |
|------|------|-------|----------|
| website_scout | website_scout | sonnet | |
| scout | github_scout | sonnet | |
| evaluator | idea_evaluator | sonnet | |
| coder | coder | opus | |
| reviewer | reviewer | sonnet | |

## Pipeline

1. **website_scout** -- Check Claude/Anthropic official websites for news, updates, API changes, new features, and deprecations. Write findings to `.klodTalk/team/current/website_scout_findings.md`. Focus on official Anthropic channels only (docs.anthropic.com, anthropic.com, github.com/anthropics). Do NOT search community GitHub repositories — that is the GitHub scout's job.
2. **scout** -- Search GitHub for repos and ideas matching configured tags. Write findings to `.klodTalk/team/current/scout_findings.md`.
3. **evaluator** -- Read BOTH `website_scout_findings.md` AND `scout_findings.md`. Evaluate all findings together. Write evaluation to `.klodTalk/team/current/evaluated_ideas.md`.
4. **coder** -- Implement the top-ranked ideas from the evaluator's shortlist. In `coder_output.txt`, include a **Source Attribution** section listing each implemented idea and its source (GitHub repo with name/URL/stars, or article with title/URL/source site).
5. **reviewer** -- Review the implementation for correctness, safety, and adherence to codebase conventions.
   - Review loop: if changes required, send back to **coder** for fixes.
   - Max iterations: **2**
