#!/usr/bin/env python3
"""Project execution script — Python replacement for run_agent.sh.
Called via: docker exec -e MODE=<mode> <container> /agent/run_agent.py
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timezone

from utils.claude_auth import get_claude_auth

IN_DIR = "/workspace/.klodTalk/in_messages"
OUT_DIR = "/workspace/.klodTalk/out_messages"
PR_DIR = "/workspace/.klodTalk/pr_messages"
IN_FILE = os.path.join(IN_DIR, "in_message.txt")
OUT_FILE = os.path.join(OUT_DIR, "out_message.txt")
CONFIRM_FILE = os.path.join(OUT_DIR, "confirm_message.txt")
BTW_FILE = os.path.join(IN_DIR, "btw_message.txt")
BTW_RESPONSE_FILE = os.path.join(OUT_DIR, "btw_response.txt")
PR_FILE = os.path.join(PR_DIR, "pr_message.txt")
CHANGED_FILES_PATH = "/workspace/.klodTalk/changed_files.txt"
AGENT_SCRIPT = "/workspace/agent_run.sh"
PROGRESS_FILE = os.path.join(OUT_DIR, "progress_message.txt")
TEAM_CURRENT_DIR = "/workspace/.klodTalk/team/current"

HISTORY_FILE = "/workspace/.klodTalk/history/session.jsonl"
MAX_HISTORY_CHARS = 20000
MAX_HISTORY_MESSAGES = 50

_claude_auth = get_claude_auth()

BASE_BRANCH = os.environ.get("BASE_BRANCH", "main")
MODE = os.environ.get("MODE", "execute")
MERGE_STATUS = os.environ.get("MERGE_STATUS", "ok")
TEAM_MODE = os.environ.get("TEAM_MODE", "false").lower() == "true"
USER_NAME = os.environ.get("USER_NAME", "unknown")
PROJECT_NAME = os.environ.get("PROJECT_NAME", "unknown")
GIT_USER_NAME = os.environ.get("GIT_USER_NAME", "Claude Bot")
GIT_USER_EMAIL = os.environ.get("GIT_USER_EMAIL", "claude@bot.local")
TEAM_NAME = os.environ.get("TEAM_NAME", "")


def _disable_workspace_plugins():
    """Remove enabledPlugins from workspace .claude/settings.json.

    Plugins that start MCP servers (e.g. chrome-devtools-mcp) will hang
    inside the container because the required host tools (Chrome, etc.) are
    absent.  Strip them before launching Claude so they are never loaded.
    """
    settings_path = "/workspace/.claude/settings.json"
    try:
        if not os.path.isfile(settings_path):
            return
        with open(settings_path) as f:
            settings = json.load(f)
        if "enabledPlugins" not in settings:
            return
        del settings["enabledPlugins"]
        with open(settings_path, "w") as f:
            json.dump(settings, f, indent=2)
    except Exception as e:
        print(f"WARNING: Could not disable workspace plugins: {e}")


def _setup_agent_hooks():
    """Install a PreToolUse hook that blocks destructive commands and logs tool calls.

    Writes a bash hook script and registers it in ~/.claude/settings.json.
    The hook intercepts Bash tool calls and blocks dangerous patterns like
    force-push, hard reset, etc. All tool calls are logged to a JSONL file.
    """
    hook_script_path = "/home/agent/.klodtalk_pretool_hook.sh"
    settings_path = os.path.expanduser("~/.claude/settings.json")
    history_dir = "/workspace/.klodTalk/history"

    # Ensure history directory exists for tool call logging
    os.makedirs(history_dir, exist_ok=True)

    hook_script = r"""#!/usr/bin/env bash
# KlodTalk PreToolUse hook — blocks destructive commands and logs tool calls.
# Reads JSON from stdin ($CLAUDE_TOOL_INPUT).

set -euo pipefail

TOOL_INPUT=$(cat)
TOOL_NAME="${CLAUDE_TOOL_NAME:-unknown}"
LOG_FILE="/workspace/.klodTalk/history/tool_calls.jsonl"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Extract command for Bash tool calls
COMMAND=""
if [ "$TOOL_NAME" = "Bash" ] || [ "$TOOL_NAME" = "bash" ]; then
    COMMAND=$(echo "$TOOL_INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('command',''))" 2>/dev/null || echo "")
fi

# Log every tool call
mkdir -p "$(dirname "$LOG_FILE")"
HOOK_TIMESTAMP="$TIMESTAMP" HOOK_TOOL="$TOOL_NAME" HOOK_COMMAND="$COMMAND" python3 -c "
import json, os
entry = {
    'timestamp': os.environ.get('HOOK_TIMESTAMP', ''),
    'tool': os.environ.get('HOOK_TOOL', ''),
    'command': os.environ.get('HOOK_COMMAND', '').strip()
}
print(json.dumps(entry))
" >> "$LOG_FILE" 2>/dev/null || true

# Block destructive patterns for Bash tool calls
if [ -n "$COMMAND" ]; then
    BLOCKED=""
    case "$COMMAND" in
        *"git push"*"--force"*)   BLOCKED="git push --force is blocked" ;;
        *"git push"*"-f"*)        BLOCKED="git push -f is blocked" ;;
        *"git reset"*"--hard"*)   BLOCKED="git reset --hard is blocked" ;;
        *"git clean"*"-f"*)       BLOCKED="git clean -f is blocked" ;;
        *"git checkout ."*)       BLOCKED="git checkout . is blocked" ;;
        *"git restore ."*)        BLOCKED="git restore . is blocked" ;;
        *"rm -rf /"*)             BLOCKED="rm -rf / is blocked" ;;
    esac

    if [ -n "$BLOCKED" ]; then
        echo "{\"decision\": \"block\", \"reason\": \"$BLOCKED\"}" >&2
        exit 2
    fi
fi

# Allow the tool call
exit 0
"""

    try:
        with open(hook_script_path, "w") as f:
            f.write(hook_script)
        os.chmod(hook_script_path, 0o755)

        # Read or initialize settings
        settings = {}
        if os.path.isfile(settings_path):
            try:
                with open(settings_path) as f:
                    settings = json.load(f)
            except (json.JSONDecodeError, OSError):
                settings = {}

        # Register the hook under hooks.PreToolUse
        settings["hooks"] = {
            "PreToolUse": [
                {
                    "matcher": "",
                    "hooks": [
                        {
                            "type": "command",
                            "command": hook_script_path,
                        }
                    ],
                }
            ]
        }

        os.makedirs(os.path.dirname(settings_path), exist_ok=True)
        with open(settings_path, "w") as f:
            json.dump(settings, f, indent=2)

    except Exception as e:
        print(f"WARNING: Could not set up agent hooks: {e}")


def _claude_cmd(prompt: str) -> list[str]:
    """Build the claude CLI command with auth-specific args."""
    return ["claude"] + _claude_auth.get_cli_args() + [
        "--dangerously-skip-permissions", "--output-format", "json", "-p", prompt
    ]


def _claude_env() -> dict:
    """Return environment dict with auth-specific env vars merged in."""
    env = os.environ.copy()
    env.update(_claude_auth.get_env())
    return env


def read_session_history() -> str:
    """Read session history JSONL and return formatted conversation log.

    Returns empty string if no history exists. Truncates to the most recent
    messages if history exceeds MAX_HISTORY_MESSAGES or MAX_HISTORY_CHARS.
    """
    if not os.path.isfile(HISTORY_FILE):
        return ""
    try:
        messages = []
        with open(HISTORY_FILE) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    role = entry.get("role", "unknown")
                    content = entry.get("content", "").strip()
                    if content:
                        messages.append(f"[{role}]: {content}")
                except json.JSONDecodeError:
                    continue

        if not messages:
            return ""

        # Keep only the most recent messages
        messages = messages[-MAX_HISTORY_MESSAGES:]

        # Truncate from the front if total chars exceed limit
        result = "\n\n".join(messages)
        while len(result) > MAX_HISTORY_CHARS and len(messages) > 1:
            messages.pop(0)
            result = "\n\n".join(messages)

        return result
    except Exception:
        return ""


def parse_claude_json_output(raw_stdout: str) -> tuple[str, str]:
    """Parse --output-format json stdout. Returns (content, usage_summary).
    Falls back to (raw_stdout, "") if JSON is missing or malformed."""
    try:
        data = json.loads(raw_stdout)
        content = data.get("result", raw_stdout)
        usage = data.get("usage", {})
        input_tokens = usage.get("input_tokens", 0)
        output_tokens = usage.get("output_tokens", 0)
        cache_tokens = usage.get("cache_read_input_tokens", 0)
        cost = data.get("total_cost_usd", 0)

        if not input_tokens and not output_tokens:
            return content, ""

        cache_part = f" ({cache_tokens:,} cached)" if cache_tokens else ""
        token_part = f"[Tokens: {input_tokens:,} in{cache_part} / {output_tokens:,} out"
        if cost:
            summary = f"{token_part} | Cost: ${cost:.4f}]"
        else:
            summary = f"{token_part}]"
        return content, summary
    except (json.JSONDecodeError, AttributeError):
        return raw_stdout, ""


def git_available() -> bool:
    try:
        r = subprocess.run(
            ["git", "-C", "/workspace", "rev-parse", "--git-dir"],
            capture_output=True
        )
        return r.returncode == 0
    except FileNotFoundError:
        return False



def write_progress(msg: str):
    try:
        with open(PROGRESS_FILE, 'w') as f:
            f.write(msg)
    except Exception:
        pass


def get_repo_branch_info() -> str:
    """Return formatted branch info string; empty if no git repo."""
    repos_json = os.environ.get("REPOS_JSON", "")
    if repos_json and repos_json != "[]":
        try:
            repos = json.loads(repos_json)
            lines = []
            for repo in repos:
                path = os.path.join("/workspace", repo["path"])
                r = subprocess.run(
                    ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                    cwd=path, capture_output=True, text=True
                )
                branch = r.stdout.strip() if r.returncode == 0 else "(unknown)"
                lines.append(f"{repo['path']}: {branch}")
            return "\n".join(lines)
        except Exception:
            return ""
    elif git_available():
        r = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd="/workspace", capture_output=True, text=True
        )
        return r.stdout.strip() if r.returncode == 0 else ""
    return ""


def run_review_mode():
    """Review mode: analyze committed diff, write to pr_message.txt."""
    is_git = git_available()
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"=== Code Review ===")
    print(f"  Project:  {PROJECT_NAME}")
    print(f"  Time:   {timestamp}")

    current_branch = "(no git)"
    commits = ""
    diff = ""

    if is_git:
        r = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd="/workspace", capture_output=True, text=True
        )
        current_branch = r.stdout.strip()
        print(f"  Branch: {current_branch} vs origin/{BASE_BRANCH}")
        print("===================")

        r = subprocess.run(
            ["git", "log", "--oneline", f"origin/{BASE_BRANCH}..{current_branch}"],
            cwd="/workspace", capture_output=True, text=True
        )
        commits = r.stdout.strip()

        r = subprocess.run(
            ["git", "diff", f"origin/{BASE_BRANCH}...{current_branch}"],
            cwd="/workspace", capture_output=True, text=True
        )
        diff = r.stdout.strip()

        if not commits and not diff:
            print("No commits ahead of origin — falling back")
            is_git = False
    else:
        print("  (no git repository — will review changed files)")
        print("===================")

    guidelines = ""
    if os.path.isfile("/workspace/review_guidelines.md"):
        with open("/workspace/review_guidelines.md") as f:
            guidelines = f.read()
        print("Loaded review_guidelines.md")

    guidelines_section = f"\n## Project Review Guidelines\n{guidelines}" if guidelines else ""

    if is_git:
        prompt = f"""You are an expert code reviewer. Review the following changes and provide clear, actionable feedback.

## Branch
{current_branch} (compared to origin/{BASE_BRANCH})

## Commits
{commits}

## Diff
{diff}
{guidelines_section}

## Instructions
- Point out bugs, security issues, and logic errors first.
- Then note code quality, readability, and style issues.
- Finally, mention any positive aspects worth keeping.
- Be concise — this will be read by the developer, not in a formal review system.
- Plain text only, no markdown fences."""
    elif os.path.isfile(CHANGED_FILES_PATH) and os.path.getsize(CHANGED_FILES_PATH) > 0:
        with open(CHANGED_FILES_PATH) as f:
            changed_files = f.read()
        print(f"  Changed files: {len(changed_files.splitlines())} file(s)")
        prompt = f"""You are an expert code reviewer. The developer just made changes to the following files in /workspace:

{changed_files}

Read each file listed above and review the changes.
{guidelines_section}

## Instructions
- Point out bugs, security issues, and logic errors first.
- Then note code quality, readability, and style issues.
- Finally, mention any positive aspects worth keeping.
- Be concise — this will be read by the developer, not in a formal review system.
- Plain text only, no markdown fences."""
    else:
        print("  (no changed_files.txt — falling back to workspace exploration)")
        prompt = f"""You are an expert code reviewer. There is no git repository and no list of changed files. Explore the source files in /workspace and perform a general code review.
{guidelines_section}
## Instructions
- Explore the source files in /workspace (ignore .klodTalk/, node_modules/, __pycache__).
- Point out bugs, security issues, and logic errors first.
- Then note code quality, readability, and style issues.
- Finally, mention any positive aspects worth keeping.
- Be concise — this will be read by the developer, not in a formal review system.
- Plain text only, no markdown fences."""

    print("Running Claude Code CLI in review mode...")
    os.makedirs(PR_DIR, exist_ok=True)

    result = subprocess.run(
        _claude_cmd(prompt),
        capture_output=True, text=True, env=_claude_env(),
    )
    raw = result.stdout.strip()
    if raw:
        content, usage_summary = parse_claude_json_output(raw)
        with open(PR_FILE, 'w') as f:
            f.write(content)
            if usage_summary:
                f.write(f"\n\n{usage_summary}")
        print(f"Review written to {PR_FILE} ({len(content)} bytes)")
    else:
        with open(PR_FILE, 'w') as f:
            f.write("Code review completed but no remarks were produced.")
        print("WARNING: Claude produced empty review output")

    print("=== Code Review Complete ===")


def run_confirm_mode(input_text: str):
    """Confirm mode: answer questions or summarise tasks — no code changes."""
    history = read_session_history()
    history_section = ""
    if history:
        history_section = f"""Here is the conversation history from this session so far. Use it to understand context and references in the current message.

<session_history>
{history}
</session_history>

"""

    prompt = f"""{history_section}The user sent the following message via voice. It may be a bit garbled or informal.

<message>
{input_text}
</message>

First decide: is this a QUESTION or a TASK?

- QUESTION: the message asks for information, an explanation, or an answer (e.g. starts with what/how/why/where/when/who/can/does/is/are, or ends with "?").
- TASK: the message asks you to do something, build something, change something, or implement something.

If it is a QUESTION:
  Answer it directly and helpfully. You may use your knowledge of the codebase if relevant.
  Keep the answer concise (3-6 sentences). Plain text only.

If it is a TASK:
  DO NOT implement anything or make any changes.
  Write a short, clear summary of what you understood the user is asking you to do.
  Start your reply with: "I understood you want me to:"
  Keep it to 2-4 sentences. Plain text only."""

    print("Running Claude Code CLI in confirm mode...")
    os.makedirs(OUT_DIR, exist_ok=True)

    result = subprocess.run(
        _claude_cmd(prompt),
        capture_output=True, text=True, env=_claude_env(),
    )
    raw = result.stdout.strip()
    if raw:
        content, usage_summary = parse_claude_json_output(raw)
        with open(CONFIRM_FILE, 'w') as f:
            f.write(content)
            if usage_summary:
                f.write(f"\n\n{usage_summary}")
        print(f"Confirm message written to {CONFIRM_FILE} ({len(content)} bytes)")
    else:
        with open(CONFIRM_FILE, 'w') as f:
            f.write("Could not summarise the request — Claude returned an empty response.")
        print("WARNING: Claude produced empty output")

    print("=== Run Complete (confirm) ===")


def run_execute_mode(input_text: str):
    """Execute mode: implement the task."""
    is_git = git_available()

    if TEAM_MODE:
        repos_json_str = os.environ.get("REPOS_JSON", "")
        is_multi_repo = bool(repos_json_str and repos_json_str != "[]")

        if is_multi_repo:
            repos = json.loads(repos_json_str)
            current_branch = "(multi-repo)"
            for repo in repos:
                path = os.path.join("/workspace", repo["path"])
                git_dir = os.path.join(path, ".git")
                if os.path.isdir(git_dir):
                    subprocess.run(["git", "config", "user.name", GIT_USER_NAME], cwd=path, capture_output=True)
                    subprocess.run(["git", "config", "user.email", GIT_USER_EMAIL], cwd=path, capture_output=True)
                    r = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=path, capture_output=True, text=True)
                    if r.returncode == 0 and current_branch == "(multi-repo)":
                        current_branch = r.stdout.strip()
            print(f"Current branch (multi-repo, team mode): {current_branch}")
        elif is_git:
            subprocess.run(["git", "config", "user.name", GIT_USER_NAME], cwd="/workspace", capture_output=True)
            subprocess.run(["git", "config", "user.email", GIT_USER_EMAIL], cwd="/workspace", capture_output=True)
            r = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd="/workspace", capture_output=True, text=True)
            current_branch = r.stdout.strip()
        else:
            current_branch = "(no git)"

        env = os.environ.copy()
        env["CURRENT_BRANCH"] = current_branch
        env["IS_MULTI_REPO"] = "1" if is_multi_repo else "0"

        # Claude team orchestrator (no bash fallback)
        claude_team_script = "/agent/claude_team/run_claude_team.sh"
        if not os.path.isfile(claude_team_script) or not os.access(claude_team_script, os.X_OK) or not TEAM_NAME:
            print("ERROR: Claude team orchestrator not available (script missing or TEAM_NAME empty)", file=sys.stderr)
            with open(OUT_FILE, 'w') as f:
                f.write("Team mode requires the Claude orchestrator but it is not available.")
            return

        print(f"Delegating to Claude team orchestrator (team={TEAM_NAME})...")
        write_progress("Starting Claude team pipeline...")
        result = subprocess.run([claude_team_script, TEAM_NAME], env=env)

        if not os.path.isfile(OUT_FILE):
            with open(OUT_FILE, 'w') as f:
                f.write("Team pipeline completed but did not write a summary.")

        # Parse token usage from orchestrator JSON output
        claude_output_file = os.path.join(TEAM_CURRENT_DIR, "claude_orchestrator_output.json")
        if os.path.isfile(claude_output_file):
            try:
                with open(claude_output_file, 'r') as f:
                    raw_output = f.read().strip()
                _, usage_summary = parse_claude_json_output(raw_output)
                if usage_summary and os.path.isfile(OUT_FILE):
                    with open(OUT_FILE, 'a') as f:
                        f.write(f"\n\n{usage_summary}")
            except Exception as e:
                print(f"WARNING: Could not parse orchestrator token usage: {e}")

        # Append branch info (same as non-team mode)
        branch_info = get_repo_branch_info()
        if branch_info and os.path.isfile(OUT_FILE):
            repos_json = os.environ.get("REPOS_JSON", "")
            is_multi = bool(repos_json and repos_json != "[]")
            with open(OUT_FILE, 'a') as f:
                if is_multi:
                    f.write(f"\n\nBranches:\n{branch_info}\n")
                else:
                    f.write(f"\n\nBranch: {branch_info}\n")

        print(f"=== Run Complete (team mode, exit={result.returncode}) ===")
        return

    # Custom agent script
    if os.path.isfile(AGENT_SCRIPT) and os.access(AGENT_SCRIPT, os.X_OK):
        print(f"Running custom project script: {AGENT_SCRIPT}")
        subprocess.run([AGENT_SCRIPT, IN_FILE, OUT_FILE])
        if not os.path.isfile(OUT_FILE):
            print(f"WARNING: Custom script did not produce output at {OUT_FILE}")
        print("=== Run Complete ===")
        return

    # Default: Claude CLI
    repos_json_str = os.environ.get("REPOS_JSON", "")
    is_multi_repo = bool(repos_json_str and repos_json_str != "[]")

    if is_multi_repo:
        repos = json.loads(repos_json_str)
        current_branch = "(multi-repo)"
        for repo in repos:
            path = os.path.join("/workspace", repo["path"])
            git_dir = os.path.join(path, ".git")
            if os.path.isdir(git_dir):
                subprocess.run(["git", "config", "user.name", GIT_USER_NAME], cwd=path, capture_output=True)
                subprocess.run(["git", "config", "user.email", GIT_USER_EMAIL], cwd=path, capture_output=True)
                r = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=path, capture_output=True, text=True)
                if r.returncode == 0 and current_branch == "(multi-repo)":
                    current_branch = r.stdout.strip()
        print(f"Current branch (multi-repo): {current_branch}")
    elif is_git:
        subprocess.run(["git", "config", "user.name", GIT_USER_NAME], cwd="/workspace", capture_output=True)
        subprocess.run(["git", "config", "user.email", GIT_USER_EMAIL], cwd="/workspace", capture_output=True)
        r = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd="/workspace", capture_output=True, text=True)
        current_branch = r.stdout.strip()
        print(f"Current branch: {current_branch}")
    else:
        current_branch = "(no git)"

    # Clear previous changed-files record
    if os.path.isfile(CHANGED_FILES_PATH):
        os.remove(CHANGED_FILES_PATH)

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Build merge note, multi-repo section, and git instructions
    multi_repo_section = ""
    if is_multi_repo:
        repos = json.loads(repos_json_str)
        repos_list = "\n".join(
            f"  - /workspace/{r['path']}  (base branch: {r.get('base_branch', 'main')})"
            for r in repos
        )
        if MERGE_STATUS == "conflicts":
            merge_note = "IMPORTANT: The server attempted to merge the base branch into one or more repositories but there are merge conflicts. You must resolve all conflict markers (<<<<<<, =======, >>>>>>>) before making your changes."
        else:
            merge_note = "The server has already merged each repository's base branch into its working branch — you are up to date."
        multi_repo_section = f"""## Workspace Structure
This workspace contains multiple independent git repositories:
{repos_list}

Work in the appropriate repository for the task. Commit separately in each repository you modify."""
        git_instructions = "## Git Instructions\n- Stage and commit your changes in each repository you modified, with clear, descriptive commit messages.\n- Do NOT push — the server handles pushing after you are done.\n- Do NOT open a pull request."
    elif not is_git:
        merge_note = "This workspace has no git repository. Do not run any git commands."
        git_instructions = "## Git Instructions\n- This workspace has no git repository. Do not run any git commands."
    elif MERGE_STATUS == "conflicts":
        merge_note = f"IMPORTANT: The server attempted to merge '{BASE_BRANCH}' into this branch but there are merge conflicts. You must resolve all conflict markers (<<<<<<, =======, >>>>>>>) before making your changes."
        git_instructions = "## Git Instructions\n- Stage and commit your changes with a clear, descriptive commit message.\n- Do NOT push — the server handles pushing after you are done.\n- Do NOT open a pull request."
    else:
        merge_note = f"The server has already merged '{BASE_BRANCH}' into this branch — you are up to date."
        git_instructions = "## Git Instructions\n- Stage and commit your changes with a clear, descriptive commit message.\n- Do NOT push — the server handles pushing after you are done.\n- Do NOT open a pull request."

    multi_repo_prompt = f"\n{multi_repo_section}\n" if multi_repo_section else ""

    host_workspace = os.environ.get("HOST_WORKSPACE_PATH", "")
    docker_note = ""
    if host_workspace:
        docker_note = f"""
## Docker (if needed)
The `docker` CLI is available. You are running inside a container; the Docker daemon is on the host.
- /workspace inside this container maps to `{host_workspace}` on the host.
- When running sibling containers with volume mounts, use the HOST path, not /workspace:
    docker run -v {host_workspace}/mydir:/app/mydir myimage
  You can also reference it as: -v $HOST_WORKSPACE_PATH/mydir:/app/mydir
- `docker compose` (v2) is also available.
- Containers you start are siblings on the host, not nested inside this container.
"""

    history = read_session_history()
    history_section = ""
    if history:
        history_section = f"""
## Session History
Here is the conversation history from this session. Use it to understand context and references in the task request.

<session_history>
{history}
</session_history>
"""

    prompt = f"""You are an autonomous coding assistant.
You are working in git branch: {current_branch}

{merge_note}
{multi_repo_prompt}{history_section}
## Task
<user_request>
{input_text}
</user_request>

## Required: Write your response
After completing all code changes, you MUST write a plain-text summary to exactly this path:
  {OUT_FILE}

The summary should include:
- What was done
- Files created or modified
- Any important notes, caveats, or follow-up suggestions

Keep the summary concise — it will be read aloud to the user.

## Required: Write changed files list
Also write the list of every file you created or modified to:
  {CHANGED_FILES_PATH}
One file path per line, relative to /workspace (e.g. src/main.py). This is used by the code reviewer.

{git_instructions}
{docker_note}
Timestamp: {timestamp}"""

    print("\nRunning Claude Code CLI...")
    print("─" * 60)

    os.makedirs(OUT_DIR, exist_ok=True)

    result = subprocess.run(
        _claude_cmd(prompt),
        cwd="/workspace", capture_output=True, text=True, env=_claude_env(),
    )

    print("─" * 60)

    if not os.path.isfile(OUT_FILE):
        print(f"WARNING: Claude did not write output to {OUT_FILE}")
        with open(OUT_FILE, 'w') as f:
            f.write(f"Claude finished the task but did not write a summary to {OUT_FILE}.")

    # Append usage summary before branch info.
    _, usage_summary = parse_claude_json_output(result.stdout.strip())
    if usage_summary and os.path.isfile(OUT_FILE):
        with open(OUT_FILE, 'a') as f:
            f.write(f"\n\n{usage_summary}")

    # Append branch/repo info so the user knows which branch was used.
    branch_info = get_repo_branch_info()
    if branch_info and os.path.isfile(OUT_FILE):
        repos_json = os.environ.get("REPOS_JSON", "")
        is_multi = bool(repos_json and repos_json != "[]")
        with open(OUT_FILE, 'a') as f:
            if is_multi:
                f.write(f"\n\nBranches:\n{branch_info}\n")
            else:
                f.write(f"\n\nBranch: {branch_info}\n")

    print("=== Run Complete ===")


def run_btw_mode():
    """BTW mode: quick side-channel response without interrupting main work."""
    if not os.path.isfile(BTW_FILE):
        print("No BTW message found")
        return
    btw_text = open(BTW_FILE).read().strip()
    os.remove(BTW_FILE)
    if not btw_text:
        return

    history = read_session_history()
    history_section = ""
    if history:
        history_section = f"Session context:\n{history}\n\n"

    prompt = f"""{history_section}The user sent a brief side note (BTW) while you are working on another task. Acknowledge it briefly and note if it affects the current work.

BTW message: {btw_text}

Keep your response to 1-3 sentences. Plain text only."""

    print(f"Running Claude Code CLI in BTW mode...")
    os.makedirs(OUT_DIR, exist_ok=True)

    result = subprocess.run(
        _claude_cmd(prompt),
        capture_output=True, text=True, env=_claude_env(),
    )
    raw = result.stdout.strip()
    if raw:
        content, usage_summary = parse_claude_json_output(raw)
        with open(BTW_RESPONSE_FILE, 'w') as f:
            f.write(f"[BTW Response] {content}")
            if usage_summary:
                f.write(f"\n\n{usage_summary}")
    else:
        with open(BTW_RESPONSE_FILE, 'w') as f:
            f.write("[BTW Response] Acknowledged.")

    print("=== Run Complete (btw) ===")


def main():
    os.makedirs(IN_DIR, exist_ok=True)
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(PR_DIR, exist_ok=True)

    _disable_workspace_plugins()
    _setup_agent_hooks()

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    is_git = git_available()

    if MODE == "review":
        run_review_mode()
        return

    if MODE == "btw":
        run_btw_mode()
        return

    if not os.path.isfile(IN_FILE):
        print(f"ERROR: No input file at {IN_FILE}", file=sys.stderr)
        sys.exit(1)

    with open(IN_FILE) as f:
        input_text = f.read()

    if not input_text.strip():
        print("ERROR: Input file is empty", file=sys.stderr)
        sys.exit(1)

    print("=== Session Run ===")
    print(f"  Project:      {PROJECT_NAME}")
    print(f"  Mode:         {MODE}")
    print(f"  Base branch:  {BASE_BRANCH}")
    print(f"  Merge status: {MERGE_STATUS}")
    print(f"  Git repo:     {is_git}")
    print(f"  Time:         {timestamp}")
    print(f"  Input:        {input_text[:200]}")
    print("=================")

    if MODE == "confirm":
        run_confirm_mode(input_text)
    else:
        run_execute_mode(input_text)


if __name__ == "__main__":
    main()
