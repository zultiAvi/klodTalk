#!/bin/bash
# Run a team using Claude as the orchestrator.
#
# Instead of bash scripts controlling the pipeline, a single Claude instance
# reads the orchestrator.md, team.md, and role definitions, then uses its
# built-in Agent tool to spawn sub-agents for each pipeline step.
#
# Usage: run_claude_team.sh <team_name> [workspace_path]
#
# Environment variables (same interface as existing team_orchestrator.sh):
#   PROJECT_NAME       - Display name of the project
#   USER_NAME        - Authenticated user name
#   BASE_BRANCH      - Branch to merge from (default: main)
#   CURRENT_BRANCH   - Current git branch
#   MERGE_STATUS     - "ok" or "conflicts"
#   CLAUDE_MODEL     - Override orchestrator model (default: claude-opus-4-6)
#   CLAUDE_TIMEOUT   - Timeout in seconds (default: 3600)

set -euo pipefail

# ─────────────────────────────────────────────────────────────
# Arguments and defaults
# ─────────────────────────────────────────────────────────────
TEAM_NAME="${1:?Usage: run_claude_team.sh <team_name> [workspace_path]}"
WORKSPACE="${2:-/workspace}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEAMS_DIR="${SCRIPT_DIR}/teams"
ROLES_DIR="${SCRIPT_DIR}/roles"
ORCHESTRATOR_MD="${SCRIPT_DIR}/orchestrator.md"

PROJECT_NAME="${PROJECT_NAME:-${TEAM_NAME}}"
USER_NAME="${USER_NAME:-unknown}"
BASE_BRANCH="${BASE_BRANCH:-main}"
CURRENT_BRANCH="${CURRENT_BRANCH:-$(git -C "${WORKSPACE}" branch --show-current 2>/dev/null || echo 'unknown')}"
MERGE_STATUS="${MERGE_STATUS:-ok}"
REPOS_JSON="${REPOS_JSON:-}"
RESULTS_FOLDER="${RESULTS_FOLDER:-$(jq -r '.results_folder // ""' "${2:-/workspace}/.klodTalk/team/team.json" 2>/dev/null || echo "")}"
# Model alias resolution: opus->claude-opus-4-6, sonnet->claude-sonnet-4-6, haiku->claude-haiku-4-5-20251001
# Deprecation warnings (as of April 2026):
#   - claude-3-haiku-20240307: RETIRED — returns API errors since March 2026
#   - claude-sonnet-4-20250514: retiring June 15 2026 — migrate to claude-sonnet-4-6
#   - claude-opus-4-20250514: retiring June 15 2026 — migrate to claude-opus-4-6
CLAUDE_MODEL="${CLAUDE_MODEL:-claude-opus-4-6}"
CLAUDE_TIMEOUT="${CLAUDE_TIMEOUT:-3600}"

# ─────────────────────────────────────────────────────────────
# Validate inputs
# ─────────────────────────────────────────────────────────────
TEAM_MD="${TEAMS_DIR}/${TEAM_NAME}.md"
if [[ ! -f "${TEAM_MD}" ]]; then
    echo "ERROR: Team definition not found: ${TEAM_MD}"
    echo "Available teams:"
    ls -1 "${TEAMS_DIR}"/*.md 2>/dev/null | xargs -I{} basename {} .md
    exit 1
fi

if [[ ! -f "${ORCHESTRATOR_MD}" ]]; then
    echo "ERROR: Orchestrator instructions not found: ${ORCHESTRATOR_MD}"
    exit 1
fi

# ─────────────────────────────────────────────────────────────
# Read all .md files
# ─────────────────────────────────────────────────────────────
ORCHESTRATOR_CONTENT=$(cat "${ORCHESTRATOR_MD}")
TEAM_CONTENT=$(cat "${TEAM_MD}")

# Read the user request
REQUEST_FILE="${WORKSPACE}/.klodTalk/in_messages/in_message.txt"
if [[ -f "${REQUEST_FILE}" ]]; then
    USER_REQUEST=$(cat "${REQUEST_FILE}")
else
    echo "ERROR: No user request found at ${REQUEST_FILE}"
    exit 1
fi

# Collect only role definitions referenced in the team's Members table
ROLES_CONTENT=""
# Extract role names from the Members table (lines matching "| name | role | model |")
# Skip the header and separator lines, grab the second column (Role)
TEAM_ROLES=$(grep -E '^\|[^|]+\|[^|]+\|[^|]+\|[^|]*\|?' "${TEAM_MD}" \
    | grep -v -E '^\|[-\s]+\|' \
    | grep -v -E '^\|\s*Name\s*\|' \
    | awk -F'|' '{gsub(/^[ \t]+|[ \t]+$/, "", $3); print $3}')

for role_name in ${TEAM_ROLES}; do
    role_file="${ROLES_DIR}/${role_name}.md"
    if [[ -f "${role_file}" ]]; then
        ROLES_CONTENT="${ROLES_CONTENT}

---

### Role: ${role_name}

$(cat "${role_file}")
"
    else
        echo "WARNING: Role file not found: ${role_file}"
    fi
done

# ─────────────────────────────────────────────────────────────
# Collect skills from CLAUDE/skills/
# ─────────────────────────────────────────────────────────────
# For multi-repo projects, use the first repo's CLAUDE/skills directory
if [ -n "$REPOS_JSON" ] && [ "$REPOS_JSON" != "[]" ]; then
    FIRST_REPO_PATH=$(python3 -c "import json, os; repos = json.loads(os.environ.get('REPOS_JSON', '[]')); print(repos[0]['path'] if repos else '')")
    if [ -n "$FIRST_REPO_PATH" ]; then
        SKILLS_DIR="${WORKSPACE}/${FIRST_REPO_PATH}/CLAUDE/skills"
    else
        SKILLS_DIR="${WORKSPACE}/CLAUDE/skills"
    fi
else
    SKILLS_DIR="${WORKSPACE}/CLAUDE/skills"
fi
SKILLS_CONTENT=""
SKILLS_LIST=""

if [[ -d "${SKILLS_DIR}" ]]; then
    for skill_file in "${SKILLS_DIR}"/*.md; do
        [[ -f "${skill_file}" ]] || continue
        skill_name=$(basename "${skill_file}" .md)
        [[ "${skill_name}" == "README" ]] && continue
        SKILLS_LIST="${SKILLS_LIST}  - ${skill_name}\n"
        SKILLS_CONTENT="${SKILLS_CONTENT}

---

### Skill: ${skill_name}

$(cat "${skill_file}")
"
    done
fi

SKILLS_SECTION=""
if [[ -n "${SKILLS_CONTENT}" ]]; then
    SKILLS_SECTION="
## Available Skills

The following reusable skills were found in \`CLAUDE/skills/\`. Use relevant ones when spawning sub-agents.

${SKILLS_CONTENT}
"
else
    SKILLS_SECTION="
## Available Skills

No skills found in \`CLAUDE/skills/\`. After completing this task, create skills for any reusable patterns discovered.
"
fi

# ─────────────────────────────────────────────────────────────
# Compose the prompt
# ─────────────────────────────────────────────────────────────
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

MULTI_REPO_CONTEXT=""
if [ -n "$REPOS_JSON" ] && [ "$REPOS_JSON" != "[]" ]; then
    MULTI_REPO_CONTEXT="
- **Multi-repo workspace**: This workspace contains multiple git repositories.
- **Repos JSON**: \`${REPOS_JSON}\`
- **IMPORTANT**: Each repo is a subdirectory under /workspace. Git operations (commit, branch) must be run from within each repo's directory, not from /workspace root. The git identity has been configured in each repo already."
fi

PROMPT="${ORCHESTRATOR_CONTENT}

---

## Team Definition

${TEAM_CONTENT}

---

## Role Definitions

${ROLES_CONTENT}

---

## Environment

- **Workspace**: ${WORKSPACE}
- **Branch**: ${CURRENT_BRANCH}
- **Base branch**: ${BASE_BRANCH}
- **Merge status**: ${MERGE_STATUS}
- **Project name**: ${PROJECT_NAME}
- **Results folder**: ${RESULTS_FOLDER:-none}
- **Skills directory**: ${SKILLS_DIR}
- **Timestamp**: ${TIMESTAMP}
${MULTI_REPO_CONTEXT}
${SKILLS_SECTION}
## User Request

<user_request>
${USER_REQUEST}
</user_request>

---

User: ${USER_NAME}
Timestamp: ${TIMESTAMP}

Begin orchestrating the team now. Follow the pipeline defined in the team definition above."

# ─────────────────────────────────────────────────────────────
# Ensure output directories exist
# ─────────────────────────────────────────────────────────────
mkdir -p "${WORKSPACE}/.klodTalk/team/current"
mkdir -p "${WORKSPACE}/.klodTalk/out_messages"
mkdir -p "${WORKSPACE}/.klodTalk/history"
mkdir -p "${SKILLS_DIR}"

# ─────────────────────────────────────────────────────────────
# Run Claude as the orchestrator
# ─────────────────────────────────────────────────────────────
echo "=== Claude Team Orchestrator ==="
echo "Team: ${TEAM_NAME}"
echo "Model: ${CLAUDE_MODEL}"
echo "Branch: ${CURRENT_BRANCH}"
echo "Timeout: $((CLAUDE_TIMEOUT / 60)) minutes"
echo "================================"

CLAUDE_OUTPUT_FILE="${WORKSPACE}/.klodTalk/team/current/claude_orchestrator_output.json"
CLAUDE_EXIT=0
timeout "${CLAUDE_TIMEOUT}" claude \
    --model "${CLAUDE_MODEL}" \
    --dangerously-skip-permissions \
    --output-format json \
    -p "${PROMPT}" \
    > "${CLAUDE_OUTPUT_FILE}" || CLAUDE_EXIT=$?

if [[ ${CLAUDE_EXIT} -eq 124 ]]; then
    echo "ERROR: Orchestrator timed out after $((CLAUDE_TIMEOUT / 60)) minutes"
    # Write a timeout message if no output was produced
    if [[ ! -f "${WORKSPACE}/.klodTalk/out_messages/out_message.txt" ]]; then
        echo "The team orchestrator timed out before completing. Partial work may have been committed to branch ${CURRENT_BRANCH}." \
            > "${WORKSPACE}/.klodTalk/out_messages/out_message.txt"
    fi
fi

# ─────────────────────────────────────────────────────────────
# Verify required output files exist
# ─────────────────────────────────────────────────────────────
if [[ ! -f "${WORKSPACE}/.klodTalk/out_messages/out_message.txt" ]]; then
    echo "WARNING: No out_message.txt produced — creating fallback"
    echo "Team ${TEAM_NAME} completed with exit code ${CLAUDE_EXIT}. Check branch ${CURRENT_BRANCH} for changes." \
        > "${WORKSPACE}/.klodTalk/out_messages/out_message.txt"
fi

echo "=== Claude Team Orchestrator Complete (exit: ${CLAUDE_EXIT}) ==="
exit "${CLAUDE_EXIT}"
