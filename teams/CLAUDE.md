# teams/

Claude-native team orchestration. A single Claude instance acts as the orchestrator, reading `.md` files and spawning sub-agents for each pipeline step.

## How It Works

1. `run_claude_team.sh` composes a prompt from `orchestrator.md` + team definition + all role definitions.
2. Claude (Opus) runs as the orchestrator, reading the team pipeline and spawning sub-agents via the Agent tool.
3. Each sub-agent gets its role instructions and context from the orchestrator.
4. The orchestrator handles review loops, progress tracking, and final summary.

## Directory Structure

```
teams/
├── CLAUDE.md                # This file
├── orchestrator.md          # Master orchestration instructions
├── run_claude_team.sh       # Entry point (shell -> Claude)
├── teams/                   # Team definitions (one per workflow)
│   ├── plan-code-review.md  # Default: planner -> coder -> reviewer
│   ├── plan-code.md         # Fast: planner -> coder
│   ├── tdd.md               # Test-driven development
│   ├── unit-test.md         # Write unit tests
│   ├── refactor.md          # Refactor + test validation
│   ├── security.md          # Security-focused
│   ├── optimizer.md         # Iterative optimization
│   └── ...
└── roles/                   # Shared role definitions
    ├── planner.md
    ├── coder.md
    ├── reviewer.md
    └── ...
```

## Adding a New Team

Create a `.md` file in `teams/` with:
- **Members table**: name, role (references `roles/*.md`), model (opus/sonnet/haiku).
- **Pipeline**: ordered steps, with review loop config where needed.
- **Optional members**: Set `yes` in the Optional column and add `(optional)` in the pipeline step. The orchestrator decides at runtime whether to run these steps.

See `docs/add_team.md` for the full format.

## Modifying a Role

Edit the role's `.md` file in `roles/`. All teams referencing that role automatically get the update.

## Adding a New Role

Create a `.md` file in `roles/` describing the role's behavior. Reference it from any team's members table.
