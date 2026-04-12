#!/bin/bash
# Called via: docker exec -e MODE=<mode> <container> /agent/run_agent.sh
#
# Modes:
#   execute (default) — merge base branch, run Claude on the task, write result
#                       to /workspace/.klodTalk/out_messages/out_message.txt
#   confirm           — Claude reads the task and writes back what it understood
#                       to /workspace/.klodTalk/out_messages/confirm_message.txt
#                       (no code changes, no git operations)
#   review            — Claude reviews commits since base branch (or all source files
#                       if no git repo) and writes remarks to
#                       /workspace/.klodTalk/pr_messages/pr_message.txt
#
# The agent project can provide its own script at /workspace/agent_run.sh
# to fully override the execute mode.
#
# Environment variables (set by server):
#   PROJECT_NAME    - display name of the project
#   BASE_BRANCH   - base branch (informational; server already merged it)
#   MODE          - "execute" or "confirm" (default: execute)
#   MERGE_STATUS  - "ok" or "conflicts" (set by server after git merge)

set -e

IN_DIR="/workspace/.klodTalk/in_messages"
OUT_DIR="/workspace/.klodTalk/out_messages"
PR_DIR="/workspace/.klodTalk/pr_messages"
IN_FILE="$IN_DIR/in_message.txt"
OUT_FILE="$OUT_DIR/out_message.txt"
CONFIRM_FILE="$OUT_DIR/confirm_message.txt"
PR_FILE="$PR_DIR/pr_message.txt"
CHANGED_FILES_PATH="/workspace/.klodTalk/changed_files.txt"
CUSTOM_SCRIPT="/workspace/agent_run.sh"

BASE_BRANCH="${BASE_BRANCH:-main}"
MODE="${MODE:-execute}"
MERGE_STATUS="${MERGE_STATUS:-ok}"
TEAM_MODE="${TEAM_MODE:-false}"
TEAM_NAME="${TEAM_NAME:-}"
USER_NAME="${USER_NAME:-unknown}"
GIT_USER_NAME="${GIT_USER_NAME:-Claude Bot}"
GIT_USER_EMAIL="${GIT_USER_EMAIL:-claude@bot.local}"
REPOS_JSON="${REPOS_JSON:-}"

# Detect whether /workspace has a git repository
if git -C /workspace rev-parse --git-dir >/dev/null 2>&1; then
    IS_GIT=1
else
    IS_GIT=0
fi

# Detect multi-repo mode
IS_MULTI_REPO=0
if [ -n "$REPOS_JSON" ] && [ "$REPOS_JSON" != "[]" ]; then
    IS_MULTI_REPO=1
fi

mkdir -p "$IN_DIR" "$OUT_DIR" "$PR_DIR"

# ── Review mode: analyse committed diff, no input file needed ─────────────────
if [ "$MODE" = "review" ]; then
    if ! command -v claude &>/dev/null; then
        echo "Claude Code CLI not available." >&2
        exit 1
    fi

    cd /workspace

    echo "=== Code Review ==="
    echo "  Project:  ${PROJECT_NAME:-unknown}"
    echo "  Time:   $(date -u +"%Y-%m-%dT%H:%M:%SZ")"

    if [ "$IS_GIT" = "1" ]; then
        CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
        echo "  Branch: $CURRENT_BRANCH vs origin/$BASE_BRANCH"
        echo "==================="

        COMMITS=$(git log --oneline "origin/$BASE_BRANCH..$CURRENT_BRANCH" 2>/dev/null || echo "")
        DIFF=$(git diff "origin/$BASE_BRANCH...$CURRENT_BRANCH" 2>/dev/null || echo "")

        if [ -z "$COMMITS" ] && [ -z "$DIFF" ]; then
            echo "No commits ahead of origin/$BASE_BRANCH — checking changed_files.txt fallback"
            IS_GIT=0  # fall through to changed_files.txt / workspace review below
        fi
    else
        echo "  (no git repository — will review changed files)"
        echo "==================="
        CURRENT_BRANCH="(no git)"
        COMMITS=""
        DIFF=""
    fi

    GUIDELINES=""
    if [ -f "/workspace/review_guidelines.md" ]; then
        GUIDELINES=$(cat "/workspace/review_guidelines.md")
        echo "Loaded review_guidelines.md"
    fi

    if [ "$IS_GIT" = "1" ]; then
        PROMPT="You are an expert code reviewer. Review the following changes and provide clear, actionable feedback.

## Branch
$CURRENT_BRANCH (compared to origin/$BASE_BRANCH)

## Commits
$COMMITS

## Diff
$DIFF
${GUIDELINES:+
## Project Review Guidelines
$GUIDELINES}

## Instructions
- Point out bugs, security issues, and logic errors first.
- Then note code quality, readability, and style issues.
- Finally, mention any positive aspects worth keeping.
- Be concise — this will be read by the developer, not in a formal review system.
- Plain text only, no markdown fences."
    elif [ -f "$CHANGED_FILES_PATH" ] && [ -s "$CHANGED_FILES_PATH" ]; then
        CHANGED_FILES_LIST=$(cat "$CHANGED_FILES_PATH")
        echo "  Changed files: $(wc -l < "$CHANGED_FILES_PATH") file(s)"
        PROMPT="You are an expert code reviewer. The developer just made changes to the following files in /workspace:

$CHANGED_FILES_LIST

Read each file listed above and review the changes.
${GUIDELINES:+
## Project Review Guidelines
$GUIDELINES}

## Instructions
- Point out bugs, security issues, and logic errors first.
- Then note code quality, readability, and style issues.
- Finally, mention any positive aspects worth keeping.
- Be concise — this will be read by the developer, not in a formal review system.
- Plain text only, no markdown fences."
    else
        echo "  (no changed_files.txt found — falling back to workspace exploration)"
        PROMPT="You are an expert code reviewer. There is no git repository and no list of changed files. Explore the source files in /workspace and perform a general code review.

${GUIDELINES:+## Project Review Guidelines
$GUIDELINES

}## Instructions
- Explore the source files in /workspace (ignore .klodTalk/, node_modules/, __pycache__).
- Point out bugs, security issues, and logic errors first.
- Then note code quality, readability, and style issues.
- Finally, mention any positive aspects worth keeping.
- Be concise — this will be read by the developer, not in a formal review system.
- Plain text only, no markdown fences."
    fi

    echo "Running Claude Code CLI in review mode..."
    CLAUDE_TMP=$(mktemp)
    claude --dangerously-skip-permissions -p "$PROMPT" > "$CLAUDE_TMP" || true

    if [ -s "$CLAUDE_TMP" ]; then
        mv "$CLAUDE_TMP" "$PR_FILE"
        echo "Review written to $PR_FILE ($(wc -c < "$PR_FILE") bytes)"
    else
        rm -f "$CLAUDE_TMP"
        echo "WARNING: Claude produced empty review output"
        echo "Code review completed but no remarks were produced." > "$PR_FILE"
    fi

    echo "=== Code Review Complete ==="
    exit 0
fi

# ── Validate input ────────────────────────────────────────────────────────────
if [ ! -f "$IN_FILE" ]; then
    echo "ERROR: No input file at $IN_FILE"
    exit 1
fi

INPUT=$(cat "$IN_FILE")
if [ -z "$INPUT" ]; then
    echo "ERROR: Input file is empty"
    exit 1
fi

echo "=== Session Run ==="
echo "  Project:      ${PROJECT_NAME:-unknown}"
echo "  Mode:         $MODE"
echo "  Base branch:  $BASE_BRANCH"
echo "  Merge status: $MERGE_STATUS"
echo "  Git repo:     $IS_GIT"
echo "  Time:         $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
echo "  Input:        ${INPUT:0:200}"
echo "================="

# ── Confirm mode: just summarise the request, no code changes ─────────────────
if [ "$MODE" = "confirm" ]; then
    if ! command -v claude &>/dev/null; then
        echo "Claude Code CLI not available." >&2
        echo "Cannot confirm — Claude Code CLI is not installed." > "$CONFIRM_FILE"
        exit 1
    fi

    PROMPT="The user sent the following request via voice. It may be a bit garbled or informal.

<request>
$INPUT
</request>

DO NOT implement anything or make any changes.
Just write a short, clear summary of what you understood the user is asking you to do.
Start your reply with: \"I understood you want me to:\"
Keep it to 2-4 sentences. Plain text only."

    echo "Running Claude Code CLI in confirm mode..."
    CLAUDE_TMP=$(mktemp)
    claude --dangerously-skip-permissions -p "$PROMPT" > "$CLAUDE_TMP" || true

    if [ -s "$CLAUDE_TMP" ]; then
        mv "$CLAUDE_TMP" "$CONFIRM_FILE"
        echo "Confirm message written to $CONFIRM_FILE ($(wc -c < "$CONFIRM_FILE") bytes)"
    else
        rm -f "$CLAUDE_TMP"
        echo "WARNING: Claude produced empty output, using fallback"
        echo "Could not summarise the request — Claude returned an empty response." > "$CONFIRM_FILE"
    fi

    echo "=== Run Complete (confirm) ==="
    exit 0
fi

# ── Execute mode ──────────────────────────────────────────────────────────────

# ── Team mode: delegate to multi-agent pipeline ───────────────────────────────
if [ "$TEAM_MODE" = "true" ]; then
    if [ "$IS_MULTI_REPO" = "1" ]; then
        CURRENT_BRANCH=$(python3 -c "
import json, os, subprocess
repos = json.loads(os.environ.get('REPOS_JSON', '[]'))
git_user = os.environ.get('GIT_USER_NAME', 'Claude Bot')
git_email = os.environ.get('GIT_USER_EMAIL', 'claude@bot.local')
branch = '(multi-repo)'
for repo in repos:
    path = '/workspace/' + repo['path']
    if os.path.isdir(os.path.join(path, '.git')):
        subprocess.run(['git', 'config', 'user.name', git_user], cwd=path, capture_output=True)
        subprocess.run(['git', 'config', 'user.email', git_email], cwd=path, capture_output=True)
        r = subprocess.run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], cwd=path, capture_output=True, text=True)
        if r.returncode == 0 and branch == '(multi-repo)':
            branch = r.stdout.strip()
print(branch)
")
        echo "Current branch (multi-repo, team mode): $CURRENT_BRANCH"
    elif [ "$IS_GIT" = "1" ]; then
        git config user.name  "$GIT_USER_NAME"
        git config user.email "$GIT_USER_EMAIL"
        CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
    else
        CURRENT_BRANCH="(no git)"
    fi

    export CURRENT_BRANCH USER_NAME BASE_BRANCH MERGE_STATUS PROJECT_NAME REPOS_JSON IS_MULTI_REPO GIT_USER_NAME GIT_USER_EMAIL TEAM_NAME TEAM_MODE

    # Choose orchestrator: Claude-native (default) or legacy bash
    CLAUDE_TEAM_SCRIPT="/agent/claude_team/run_claude_team.sh"

    if [ ! -f "$CLAUDE_TEAM_SCRIPT" ] || [ ! -x "$CLAUDE_TEAM_SCRIPT" ] || [ -z "$TEAM_NAME" ]; then
        echo "ERROR: Claude team orchestrator not available (script missing or TEAM_NAME empty)" >&2
        echo "Team mode requires the Claude orchestrator but it is not available." > "$OUT_FILE"
        exit 1
    fi
    echo "Delegating to Claude team orchestrator (team=$TEAM_NAME)..."
    "$CLAUDE_TEAM_SCRIPT" "$TEAM_NAME"
    TEAM_EXIT=$?

    if [ -f "$OUT_FILE" ]; then
        echo "Team pipeline output written to $OUT_FILE ($(wc -c < "$OUT_FILE") bytes)"
    else
        echo "WARNING: Team pipeline did not produce output at $OUT_FILE"
        echo "Team pipeline completed but did not write a summary." > "$OUT_FILE"
    fi

    echo "=== Run Complete (team mode, exit=${TEAM_EXIT}) ==="
    exit $TEAM_EXIT
fi

# ── Custom agent script (full override) ──────────────────────────────────────
if [ -f "$CUSTOM_SCRIPT" ] && [ -x "$CUSTOM_SCRIPT" ]; then
    echo "Running custom project script: $CUSTOM_SCRIPT"
    "$CUSTOM_SCRIPT" "$IN_FILE" "$OUT_FILE"
    if [ -f "$OUT_FILE" ]; then
        echo "Output written to $OUT_FILE ($(wc -c < "$OUT_FILE") bytes)"
    else
        echo "WARNING: Custom script did not produce output at $OUT_FILE"
    fi
    echo "=== Run Complete ==="
    exit 0
fi

# ── Default: Claude Code CLI ──────────────────────────────────────────────────
if ! command -v claude &>/dev/null; then
    echo "No custom script and no Claude CLI available." >&2
    echo "Received your message but could not process it. No agent_run.sh found and Claude Code CLI is not installed." > "$OUT_FILE"
    exit 1
fi

cd /workspace

# Clear previous changed-files record so the reviewer only sees this run's changes
rm -f "$CHANGED_FILES_PATH"

# Configure git identity and detect current branch
if [ "$IS_MULTI_REPO" = "1" ]; then
    # Set git identity in each sub-repo and get branch name from the first one
    CURRENT_BRANCH=$(python3 -c "
import json, os, subprocess
repos = json.loads(os.environ.get('REPOS_JSON', '[]'))
git_user = os.environ.get('GIT_USER_NAME', 'Claude Bot')
git_email = os.environ.get('GIT_USER_EMAIL', 'claude@bot.local')
branch = '(multi-repo)'
for repo in repos:
    path = '/workspace/' + repo['path']
    if os.path.isdir(os.path.join(path, '.git')):
        subprocess.run(['git', 'config', 'user.name', git_user], cwd=path, capture_output=True)
        subprocess.run(['git', 'config', 'user.email', git_email], cwd=path, capture_output=True)
        r = subprocess.run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], cwd=path, capture_output=True, text=True)
        if r.returncode == 0 and branch == '(multi-repo)':
            branch = r.stdout.strip()
print(branch)
")
    echo "Current branch (multi-repo): $CURRENT_BRANCH"
elif [ "$IS_GIT" = "1" ]; then
    git config user.name  "$GIT_USER_NAME"
    git config user.email "$GIT_USER_EMAIL"
    CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
    echo "Current branch: $CURRENT_BRANCH"
else
    CURRENT_BRANCH="(no git)"
    echo "No git repository — git operations will be skipped"
fi

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Build context notes for the prompt
if [ "$IS_MULTI_REPO" = "1" ]; then
    REPOS_LIST=$(python3 -c "
import json, os
repos = json.loads(os.environ.get('REPOS_JSON', '[]'))
for r in repos:
    print(f\"  - /workspace/{r['path']}  (base branch: {r.get('base_branch', 'main')})\")
")
    if [ "$MERGE_STATUS" = "conflicts" ]; then
        MERGE_NOTE="IMPORTANT: The server attempted to merge the base branch into one or more repositories but there are merge conflicts. You must resolve all conflict markers (<<<<<<, =======, >>>>>>>) before making your changes."
    else
        MERGE_NOTE="The server has already merged each repository's base branch into its working branch — you are up to date."
    fi
    MULTI_REPO_SECTION="## Workspace Structure
This workspace contains multiple independent git repositories:
$REPOS_LIST

Work in the appropriate repository for the task. Commit separately in each repository you modify."
    GIT_INSTRUCTIONS="## Git Instructions
- Stage and commit your changes in each repository you modified, with clear, descriptive commit messages.
- Do NOT push — the server handles pushing after you are done.
- Do NOT open a pull request."
elif [ "$IS_GIT" = "0" ]; then
    MERGE_NOTE="This workspace has no git repository. Do not run any git commands."
    MULTI_REPO_SECTION=""
    GIT_INSTRUCTIONS="## Git Instructions
- This workspace has no git repository. Do not run any git commands."
elif [ "$MERGE_STATUS" = "conflicts" ]; then
    MERGE_NOTE="IMPORTANT: The server attempted to merge '$BASE_BRANCH' into this branch but there are merge conflicts. You must resolve all conflict markers (<<<<<<, =======, >>>>>>>) before making your changes."
    MULTI_REPO_SECTION=""
    GIT_INSTRUCTIONS="## Git Instructions
- Stage and commit your changes with a clear, descriptive commit message.
- Do NOT push — the server handles pushing after you are done.
- Do NOT open a pull request."
else
    MERGE_NOTE="The server has already merged '$BASE_BRANCH' into this branch — you are up to date."
    MULTI_REPO_SECTION=""
    GIT_INSTRUCTIONS="## Git Instructions
- Stage and commit your changes with a clear, descriptive commit message.
- Do NOT push — the server handles pushing after you are done.
- Do NOT open a pull request."
fi

PROMPT="You are an autonomous coding assistant.
You are working in git branch: $CURRENT_BRANCH

$MERGE_NOTE
${MULTI_REPO_SECTION:+
$MULTI_REPO_SECTION
}
## Task
$INPUT

## Required: Write your response
After completing all code changes, you MUST write a plain-text summary to exactly this path:
  $OUT_FILE

The summary should include:
- What was done
- Files created or modified
- Any important notes, caveats, or follow-up suggestions

Keep the summary concise — it will be read aloud to the user.

## Required: Write changed files list
Also write the list of every file you created or modified to:
  $CHANGED_FILES_PATH
One file path per line, relative to /workspace (e.g. src/main.py). This is used by the code reviewer.

$GIT_INSTRUCTIONS

Timestamp: $TIMESTAMP"

echo ""
echo "Running Claude Code CLI..."
echo "──────────────────────────────────────────────────────────────"

# Monitor out_messages in background — detect any output file written during the run.
# The flag persists even if the server polls and removes the output file before our check.
# We prefer inotifywait (event-driven, zero CPU) when available, with a polling fallback.
mkdir -p "$OUT_DIR"
_OUT_WRITTEN_FLAG=$(mktemp /tmp/out_written_XXXXXX)
rm -f "$_OUT_WRITTEN_FLAG"
_HAS_INOTIFY=0
command -v inotifywait >/dev/null 2>&1 && _HAS_INOTIFY=1
(
    trap 'exit 0' TERM INT
    if [ "$_HAS_INOTIFY" -eq 1 ]; then
        # Cover the startup race: check for files written between mkdir and inotifywait
        # starting to watch. The final ls check (below) also covers this if the file
        # still exists, but the flag covers the case where the server already consumed it.
        ls "$OUT_DIR"/*.txt 2>/dev/null | grep -qv "confirm_message.txt" \
            && touch "$_OUT_WRITTEN_FLAG"
        # Single-event mode in a loop. -t 5 ensures inotifywait exits periodically so
        # a pending SIGTERM trap can fire between iterations rather than blocking forever.
        # Kill path: SIGTERM to this subshell interrupts the blocking wait syscall,
        # trap fires, subshell exits.
        # rc=0: event received; rc=1: transient error (retry); rc=2: timeout (re-watch).
        while true; do
            fname=$(inotifywait -q -e create,moved_to --format '%f' -t 5 "$OUT_DIR" 2>/dev/null)
            rc=$?
            if [ "$rc" -eq 0 ]; then
                [ "$fname" != "confirm_message.txt" ] && touch "$_OUT_WRITTEN_FLAG"
            elif [ "$rc" -eq 1 ]; then
                sleep 0.1  # transient error — brief pause then retry
            fi
            # rc=2 (timeout): loop and re-watch; pending SIGTERM trap fires here
        done
    else
        while true; do
            if ls "$OUT_DIR"/*.txt 2>/dev/null | grep -qv "confirm_message.txt"; then
                touch "$_OUT_WRITTEN_FLAG"
            fi
            sleep 0.1
        done
    fi
) &
_MONITOR_PID=$!

claude --dangerously-skip-permissions -p "$PROMPT"
echo "──────────────────────────────────────────────────────────────"

# Grace period before killing the monitor. For inotifywait, events fire synchronously
# so any remaining event arrives well within 0.2s. For the polling fallback (0.1s
# cycle), worst-case the write occurs just after a ls check; 1s gives at least 5 full
# poll cycles of margin, matching the original conservative value.
if [ "$_HAS_INOTIFY" -eq 1 ]; then
    sleep 0.2
else
    sleep 1
fi
kill "$_MONITOR_PID" 2>/dev/null || true
wait "$_MONITOR_PID" 2>/dev/null || true

if ls "$OUT_DIR"/*.txt 2>/dev/null | grep -qv "confirm_message.txt" || [ -f "$_OUT_WRITTEN_FLAG" ]; then
    echo "Output written to $OUT_DIR"
else
    echo "WARNING: Claude did not write output to $OUT_FILE"
    echo "Claude finished the task but did not write a summary to $OUT_FILE." > "$OUT_FILE"
fi
rm -f "$_OUT_WRITTEN_FLAG"

# Append branch/repo info to the output so the user knows which branch was used.
if [ -f "$OUT_FILE" ]; then
    if [ "$IS_MULTI_REPO" = "1" ]; then
        BRANCH_INFO=$(python3 -c "
import json, os, subprocess
repos = json.loads(os.environ.get('REPOS_JSON', '[]'))
lines = []
for repo in repos:
    path = '/workspace/' + repo['path']
    r = subprocess.run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                       cwd=path, capture_output=True, text=True)
    branch = r.stdout.strip() if r.returncode == 0 else '(unknown)'
    lines.append(repo['path'] + ': ' + branch)
print('\n'.join(lines))
" 2>/dev/null) || true
        if [ -n "$BRANCH_INFO" ]; then
            printf "\n\nBranches:\n%s\n" "$BRANCH_INFO" >> "$OUT_FILE"
        fi
    elif [ "$IS_GIT" = "1" ]; then
        printf "\n\nBranch: %s\n" "$CURRENT_BRANCH" >> "$OUT_FILE"
    fi
fi

echo "=== Run Complete ==="
