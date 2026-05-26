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

## Code Quality Standards

These rules apply to **all code you add or modify**, regardless of the project. They are about long-term maintainability, not the immediate task.

### Structure & Size

1. **Max 1024 lines per file.** When a module grows past this, split by class, concern, or layer. Long files hide complexity.
2. **1–2 top-level classes per file.** Helpers, inner types, and small dataclasses are fine; do not pile multiple public classes into one module.
3. **Wrap behavior in classes, not loose functions.** When functions share state or operate on the same data, group them as methods on a class. Reserve module-level functions for pure, stateless utilities.
4. **Single responsibility per class.** If a class name needs "and" to describe it, split it.
5. **Max ~50 lines per method.** If a method grows past that, extract sub-methods. Long methods almost always hide multiple concerns.
6. **Max nesting depth of 3.** Deeper nesting is a refactor signal — use early returns / guard clauses to flatten.

### Data Modeling

7. **Dataclasses over dicts.** Use `@dataclass` (or `pydantic.BaseModel` where the project uses it) for any structured record with a known shape. Reserve plain dicts for genuinely dynamic key/value maps (e.g., JSON payloads in transit).
8. **No `getattr(obj, "field", default)` for known fields.** Declare the field on the dataclass with a default value. `getattr`-with-default silently masks missing-field bugs and renames.
9. **No mutable default arguments.** Use `field(default_factory=list)` on dataclasses; use `None` + lazy init on functions. A shared mutable default is almost always a bug.
10. **Type-annotate public function/method signatures.** Internal helpers can skip annotations when types are obvious from context.
11. **Constants for magic numbers and strings.** Anything repeated, or anything whose meaning isn't obvious from the value, becomes a named module-level constant.

### Configuration & Environment

12. **Minimize environment variables.** Read env vars at most once at startup inside a single config loader. Application code receives parsed config objects — it never reads `os.environ` directly. This makes config testable and discoverable.
13. **No hardcoded paths or hosts.** Pass them through config; never inline `/tmp/...`, `localhost:8080`, or production hostnames in business logic.

### Readability

14. **Few inline comments.** Names and structure should carry intent. Comments explain **why** (a non-obvious decision, a workaround, a constraint), never **what** the code already says.
15. **Self-documenting names.** `parse_user_session` is better than `handle_data` plus a comment. Variable names ≥3 chars except for tight loop indices (`i`, `j`).
16. **No commented-out code.** Delete it — version control already remembers.
17. **Explicit imports.** No `from x import *`. Star imports break tooling and hide name origins.

### Error Handling

18. **No bare `except:` and no broad `except Exception:` without re-raise or structured logging.** Either handle the specific exception you expect, or let it propagate.
19. **No silent failure paths.** Returning `None`/`-1`/`""` to signal "something went wrong" is a trap. Raise an exception or return an explicit result type.

When in doubt, prefer the rule that makes the next person (or the next agent) faster.

## General Guidelines

- Follow the project's existing code style and conventions.
- Do not add features beyond what the plan requires.
- Do not refactor unrelated code.
