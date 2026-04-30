# Adding a New Team Pipeline

Teams define multi-agent workflows where different Claude roles collaborate on a task.

## Structure

```
teams/
├── orchestrator.md          # Master orchestration instructions
├── run_claude_team.sh       # Entry point (shell -> Claude)
├── teams/                   # Team definitions (one .md per workflow)
│   └── my-team.md
└── roles/                   # Role instruction files
    └── my_role.md
```

## Step 1: Define the Team

Create `teams/teams/my-team.md`:

```markdown
# Team: My Team

A description of what this team does.

## Members

| Name | Role | Model | Optional |
|------|------|-------|----------|
| planner | planner | sonnet | |
| coder | coder | opus | |
| reviewer | reviewer | haiku | |
| security_check | reviewer | haiku | yes |

## Pipeline

1. **planner**: Creates the implementation plan.
2. **coder**: Implements the plan.
3. **reviewer**: Reviews the implementation.
   - Review loop: fix_role=coder, max_iterations=2
4. **security_check** (optional): Security-focused review. Orchestrator decides based on task.
```

The first line after the `# Team:` header (that isn't a heading or separator) becomes the team's description.

## Step 2: Add Custom Roles (optional)

If your team uses custom roles, create a `.md` file in `teams/roles/`:

```bash
# Create the role file
cat > teams/roles/my_custom_role.md << 'EOF'
# My Custom Role

You are a custom role that does X, Y, Z.

## Instructions
...
EOF
```

Reference it in your team's Members table by using the role filename (without `.md`) in the Role column.

## Step 3: Assign the Team to a Project

In `config/projects.json`, set the `team` field to the team filename (without `.md`):

```
{
  "name": "my-project",
  "team": "my-team",
  ...
}
```

## Members Table Fields

| Column | Description |
|--------|-------------|
| Name | Identifier for this pipeline member |
| Role | References a file in `teams/roles/` (without `.md`) |
| Model | `opus`, `sonnet`, or `haiku` |
| Optional | `yes` if the orchestrator may skip this step (blank = required) |

## Pipeline Section

Define ordered steps. For review loops, specify:
- `fix_role` — which member handles fix passes after review
- `max_iterations` — max review/fix cycles (hard cap: 3)

## Optional Steps

Mark a member as optional by setting `yes` in the Optional column and adding `(optional)` after the member name in the pipeline step.

The orchestrator evaluates each optional step before running it. It considers the task's nature, complexity, and risk to decide whether the step adds value. When in doubt, optional steps are run (bias toward running).

Optional steps that are skipped still appear in the progress and log output with a "skipped" annotation.

### Planner Signals for Optional Steps

The planner role can set flags in `plan_meta.txt` to guide the orchestrator's decision on optional steps. Currently supported:

- `NEEDS_EXECUTION=true|false` — Tells the orchestrator whether the executor and validator optional steps should run. The planner evaluates whether the task involves running code (tests, builds, scripts) and sets this flag accordingly.

When the flag is present, the orchestrator uses it as the primary signal. When absent, the orchestrator falls back to its own heuristic evaluation of the task.

## Available Models

- `opus` — most capable (claude-opus-4-7)
- `sonnet` — balanced (claude-sonnet-4-6)
- `haiku` — fastest/cheapest (claude-haiku-4-5-20251001)

**Deprecated models (do not use):**
- `claude-3-haiku-20240307` — RETIRED, returns API errors since March 2026
- `claude-sonnet-4-20250514` — retiring June 15, 2026; use `sonnet` alias instead
- `claude-opus-4-20250514` — retiring June 15, 2026; use `opus` alias instead

## Disabling a team

Add a line `disabled: true` anywhere in the team's `.md` file. Disabled teams are skipped by the server and do not appear in the client's team dropdown. Remove the line (or set `disabled: false`) to re-enable.
