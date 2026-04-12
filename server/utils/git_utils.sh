#!/bin/bash
# Git utility functions for KlodTalk team pipeline.
# Source this file from pipeline scripts running inside /workspace.

# Get current branch name.
git_get_branch() {
    git rev-parse --abbrev-ref HEAD 2>/dev/null
}

# List files changed between base branch and HEAD.
# Usage: git_get_changed_files <base_branch>
git_get_changed_files() {
    local base_branch="$1"
    git diff --name-only "origin/${base_branch}...HEAD" 2>/dev/null
}

# Stage all changes and commit with a message.
# Usage: git_commit <message>
# 'git add .' stages everything under /workspace (the container's workspace
# mount).  Host filesystem isolation is provided by Docker — this script runs
# inside the container, so there is no access to files outside /workspace.
git_commit() {
    local message="$1"
    git -C /workspace add . 2>&1
    git commit -m "${message}" 2>&1 || echo "[git_utils] Nothing to commit or commit failed"
}

# Amend the last commit to include a multi-line body.
# Usage: git_amend_with_body <body_text>
# The existing commit subject line is preserved; body_text is appended.
git_amend_with_body() {
    local body="$1"
    local subject
    subject=$(git -C /workspace log -1 --format="%s" 2>/dev/null)
    if [[ -z "${subject}" ]]; then
        echo "[git_utils] git_amend_with_body: no commits found, skipping amend"
        return 1
    fi
    git -C /workspace commit --amend --no-verify -m "${subject}

${body}" 2>&1 || echo "[git_utils] Amend failed"
}

# Configure local git identity (run once per session if needed).
# Usage: git_configure_identity [name] [email]
git_configure_identity() {
    local name="${1:-Claude Bot}"
    local email="${2:-claude@bot.local}"
    git config user.name  "${name}"
    git config user.email "${email}"
}

# Collect branch information for all repos (or single repo).
# Output: human-readable string; empty if no git repo present.
#   Single-repo:  "branch_name"
#   Multi-repo:   "repo/path: branch\nrepo2/path: branch2"
#   No git:       ""
git_collect_repo_branches() {
    if [[ -n "${REPOS_JSON:-}" ]] && [[ "${REPOS_JSON}" != "[]" ]]; then
        python3 -c "
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
" 2>/dev/null || true
    elif git -C /workspace rev-parse --git-dir >/dev/null 2>&1; then
        git -C /workspace rev-parse --abbrev-ref HEAD 2>/dev/null || true
    fi
}
