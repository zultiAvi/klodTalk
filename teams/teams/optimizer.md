# Team: Optimizer

Iterative optimization team. Tunes configuration and optionally code to improve a numeric metric.

**Type: optimizer** — This team uses a special iterative loop instead of a linear pipeline.

## enabled

## Members

| Name | Role | Model |
|------|------|-------|
| intake | optimizer_intake | sonnet |
| config_optimizer | optimizer_config | opus |
| code_optimizer | optimizer_code | opus |
| analyzer | optimizer_analyzer | sonnet |

## Pipeline

1. **intake** — Validate the optimization request has all required fields (objective, test_command, score_extraction, optimize_direction, config_targets). If missing info, report what's needed and stop.

2. **Iterative loop** (repeat until stopped):
   a. **config_optimizer** — Make targeted config parameter changes based on history.
   b. **code_optimizer** — Optionally make code-level changes (usually NO_CHANGES early on).
   c. **Run test command** — Execute the test/benchmark command (bash, not a sub-agent).
   d. **analyzer** — Extract score from test output, update history, decide CONTINUE or STOP.

3. **Stop when**: analyzer says STOP, target score reached, score plateaued for 3+ iterations, or max iterations (default 10) reached.

## Iteration Tracking

Each iteration records: score, config changes, code changes, timestamp. The analyzer maintains `/workspace/.klodTalk/team/current/optimizer_history.json`.
