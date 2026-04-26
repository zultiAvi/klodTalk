# Base Role Conventions

Shared conventions inherited by all team roles. Individual role files reference this via `<!-- inherits: base.md -->`.

## Results Folder

If the orchestrator provides a results folder path in the context, save all output/result files there (reports, generated images, exports, CSVs, etc.) instead of inside the repository. The results folder is an external directory specifically designated for project output. Always use absolute paths when writing to the results folder.

## Pre-Commit Self-Check

Before committing, scan your own changes for stubs and placeholders:
1. Search all changed files for `TODO`, `FIXME`, `HACK`, `XXX`, `PLACEHOLDER`.
2. Verify no function body is empty, uses `pass` as a stub, raises `NotImplementedError` where real logic is needed, or uses `...` as a placeholder.
3. Check for hardcoded placeholder values: `"example.com"`, `"changeme"`, `"your-api-key-here"`, `"lorem ipsum"`, `password123`.
4. Ensure no commented-out code blocks (3+ consecutive lines) remain.
5. If any are found, fix them before committing. If a TODO is intentional and tracked, add a comment explaining why it must remain.

## Issue Severity Prefixes

Every issue line in review/validation output **must** start with one of these severity prefixes:

| Prefix | Meaning | When to use |
|--------|---------|-------------|
| `BLOCKER:` | Must be fixed before approval | Bugs, security holes, missing requirements, data loss risks |
| `WARNING:` | Should be fixed, but not a dealbreaker | Poor error handling, fragile logic, style violations that cause confusion |
| `SUGGESTION:` | Nice-to-have improvement | Readability tweaks, minor refactors, naming improvements |

## Git Commit Rules

- Stage and commit your changes with a descriptive message.
- Do NOT push.
- Keep commits focused -- one logical change per commit if possible.

## Output File Conventions

Each role writes its output to `/workspace/.klodTalk/team/current/<role>_output.txt`. The changed files list goes to `/workspace/.klodTalk/changed_files.txt` (one file path per line, relative to `/workspace`).

## Stub and Placeholder Detection

When reviewing or validating code, flag these as issues:
- **TODO/FIXME/HACK markers**: `TODO`, `FIXME`, `HACK`, `XXX`, `PLACEHOLDER` in changed files.
- **Incomplete implementations**: Empty function bodies, `pass` stubs, `NotImplementedError` where real logic is needed, `...` as a body placeholder.
- **Placeholder values**: `"example.com"`, `"changeme"`, `"your-api-key-here"`, `"lorem ipsum"`, `0.0.0.0` as a production host, `password123`.
- **Commented-out code blocks**: More than 3 consecutive commented-out lines of code.
- **Stub returns**: Functions that return `None`, `null`, `0`, `""`, `[]`, or `{}` without any logic.

## General Guidelines

- Follow the project's existing code style and conventions.
- Do not add features beyond what the plan requires.
- Do not refactor unrelated code.
