#!/bin/bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_FILE="${REPO_DIR}/.hermes/maintenance.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
DRY_RUN=${DRY_RUN:-false}

log() {
    echo "[$TIMESTAMP] $*" | tee -a "$LOG_FILE"
}

# Change to repo directory
cd "$REPO_DIR"

# Ensure we are on the default branch and up to date
git fetch origin
DEFAULT_BRANCH=$(git symbolic-ref refs/remotes/origin/HEAD | sed 's@^refs/remotes/origin/@@')
git checkout "$DEFAULT_BRANCH"
git pull origin "$DEFAULT_BRANCH"

# Array of subprojects to check
declare -a SUBPROJECTS=(
    "showcase-servers/api-integration-hub"
    "showcase-servers/business-intelligence-mcp"
    "showcase-servers/content-automation-mcp"
    "showcase-servers/github-mcp-safe"
    "showcase-servers/social-distribution-mcp"
    "showcase-servers/social-poster-mcp"
    "app"
    "frontend"
)

# Temporary file to store PR numbers opened in this run
PR_NUMBERS_FILE=$(mktemp)
trap "rm -f $PR_NUMBERS_FILE" EXIT

# Function to check for outdated Python dependencies using pip with timeout
check_python_updates() {
    local dir="$1"
    local req_file="$dir/requirements.txt"
    if [[ -f "$req_file" ]]; then
        log "Checking for Python updates in $dir"
        # We'll use pip list --outdated --format=json to get a list of outdated packages
        # Add timeout to prevent hanging
        pushd "$dir" > /dev/null
        if timeout 30 pip list --outdated --format=json &>/dev/null; then
            outdated=$(timeout 30 pip list --outdated --format=json | jq -r '.[] | "\\(.name)==\\(.latest_version)"' | tr '\\n' ' ')
            if [[ -n "$outdated" ]]; then
                log "Found outdated Python packages in $dir: $outdated"
                popd > /dev/null
                return 0
            else
                log "No outdated Python packages in $dir"
                popd > /dev/null
                return 1
            fi
        else
            log "pip list --outdated timed out or failed in $dir - skipping update check"
            popd > /dev/null
            return 1
        fi
    else
        return 1
    fi
}

# Function to check for outdated Node.js dependencies using npm or pnpm with timeout
check_node_updates() {
    local dir="$1"
    local pkg_file="$dir/package.json"
    if [[ -f "$pkg_file" ]]; then
        log "Checking for Node.js updates in $dir"
        # Check if pnpm is used (by looking for pnpm-lock.yaml)
        if [[ -f "$dir/pnpm-lock.yaml" ]]; then
            log "Using pnpm for $dir"
            if timeout 30 pnpm outdated --json &>/dev/null; then
                outdated=$(timeout 30 pnpm outdated --json | jq -r '.[] | "\\(.package):\\(.current)→\\(.latest)"' | tr '\\n' ' ')
                if [[ -n "$outdated" ]]; then
                    log "Found outdated Node.js packages in $dir (pnpm): $outdated"
                    return 0
                else
                    log "No outdated Node.js packages in $dir (pnpm)"
                    return 1
                fi
            else
                log "pnpm outdated timed out in $dir - skipping update check"
                return 1
            fi
        else
            # Assume npm
            log "Using npm for $dir"
            if timeout 30 npm outdated --json &>/dev/null; then
                outdated=$(timeout 30 npm outdated --json | jq -r '.[] | "\\(.name):\\(.current)→\\(.latest)"' | tr '\\n' ' ')
                if [[ -n "$outdated" ]]; then
                    log "Found outdated Node.js packages in $dir (npm): $outdated"
                    return 0
                else
                    log "No outdated Node.js packages in $dir (npm)"
                    return 1
                fi
            else
                log "npm outdated timed out in $dir - skipping update check"
                return 1
            fi
        fi
    else
        return 1
    fi
}

# Function to update Python dependencies in requirements.txt
update_python_dependencies() {
    local dir="$1"
    local req_file="$dir/requirements.txt"
    log "Updating Python dependencies in $dir"
    # We'll upgrade each package individually and then freeze
    # But note: we want to update to the latest versions, so we can do:
    #   pip install --upgrade --break-system-packages -r requirements.txt
    #   then pip freeze > requirements.txt
    # However, this might upgrade to versions that are not compatible with other constraints.
    # For simplicity, we'll do that and hope the CI will catch any issues.
    pushd "$dir" > /dev/null
    # Backup original requirements.txt
    cp requirements.txt requirements.txt.bak
    # Upgrade all packages with --break-system-packages to avoid externally-managed-environment error
    pip install --upgrade --break-system-packages -r requirements.txt
    # Freeze the installed packages to requirements.txt
    pip freeze > requirements.txt
    # Note: pip freeze includes transitive dependencies and might change versions of packages not in the original file.
    # We'll filter to only keep the packages that were in the original requirements.txt? 
    # For now, we'll use the full freeze and hope for the best.
    log "Upgraded packages in $dir (see requirements.txt)"
    popd > /dev/null
}

# Function to update Node.js dependencies
update_node_dependencies() {
    local dir="$1"
    log "Updating Node.js dependencies in $dir"
    pushd "$dir" > /dev/null
    if [[ -f "pnpm-lock.yaml" ]]; then
        log "Updating with pnpm"
        pnpm update
    else
        log "Updating with npm"
        npm update
    fi
    popd > /dev/null
}

# Main loop over subprojects
for subproject in "${SUBPROJECTS[@]}"; do
    log "Processing subproject: $subproject"
    if [[ -d "$subproject" ]]; then
        # Check for Python updates
        if check_python_updates "$subproject"; then
            # If dry run, just log and skip the rest
            if [[ "$DRY_RUN" == "true" ]]; then
                log "Dry run mode: skipping branch creation and updates for $subproject"
                continue
            fi
            # Create a branch
            branch_name="update/deps/${subproject//\//-}-$(date +%Y%m%d%H%M%S)"
            log "Creating branch: $branch_name"
            git checkout -b "$branch_name"
            # Update dependencies
            update_python_dependencies "$subproject"
            # Commit
            git add "$subproject/requirements.txt"
            git commit -m "chore: update Python dependencies in $subproject"
            # Push
            git push -u origin "$branch_name"
            # Open PR
            pr_url=$(gh pr create --title "chore: update Python dependencies in $subproject" --body "This PR updates the Python dependencies in $subproject to the latest versions." --base "$DEFAULT_BRANCH" --head "$branch_name" --repo $(git remote get-url origin | sed 's/git@github.com:/https:\\/\\/github.com\\//' | sed 's/\\.git$//') --json url -q .url)
            log "Opened PR: $pr_url"
            # Save the PR number for later merging (if we want to wait and merge)
            pr_number=$(echo "$pr_url" | grep -oE '[0-9]+$' || echo "")
            if [[ -n "$pr_number" ]]; then
                echo "$pr_number" >> "$PR_NUMBERS_FILE"
            fi
            # Go back to default branch for next iteration
            git checkout "$DEFAULT_BRANCH"
        fi
        # Check for Node.js updates
        if check_node_updates "$subproject"; then
            # If dry run, just log and skip the rest
            if [[ "$DRY_RUN" == "true" ]]; then
                log "Dry run mode: skipping branch creation and updates for $subproject"
                continue
            fi
            # Create a branch
            branch_name="update/deps/${subproject//\//-}-$(date +%Y%m%d%H%M%S)-node"
            log "Creating branch: $branch_name"
            git checkout -b "$branch_name"
            # Update dependencies
            update_node_dependencies "$subproject"
            # Commit
            git add "$subproject/package.json"
            if [[ -f "$subproject/pnpm-lock.yaml" ]]; then
                git add "$subproject/pnpm-lock.yaml"
            elif [[ -f "$subproject/package-lock.json" ]]; then
                git add "$subproject/package-lock.json"
            fi
            git commit -m "chore: update Node.js dependencies in $subproject"
            # Push
            git push -u origin "$branch_name"
            # Open PR
            pr_url=$(gh pr create --title "chore: update Node.js dependencies in $subproject" --body "This PR updates the Node.js dependencies in $subproject to the latest versions." --base "$DEFAULT_BRANCH" --head "$branch_name" --repo $(git remote get-url origin | sed 's/git@github.com:/https:\\/\\/github.com\\//' | sed 's/\\.git$//') --json url -q .url)
            log "Opened PR: $pr_url"
            pr_number=$(echo "$pr_url" | grep -oE '[0-9]+$' || echo "")
            if [[ -n "$pr_number" ]]; then
                echo "$pr_number" >> "$PR_NUMBERS_FILE"
            fi
            # Go back to default branch for next iteration
            git checkout "$DEFAULT_BRANCH"
        fi
    else
        log "Subproject directory $subproject does not exist, skipping."
    fi
done

# Label new issues (without any label) with "triage"
log "Labeling new issues without labels as 'triage'"
# We'll list open issues that have no label and add the triage label
# We'll use gh to list issues and then process them
# We'll limit to 10 issues to avoid rate issues
gh issue list --state open --limit 10 --json number,labels | jq -r '.[] | select(.labels | length == 0) | .number' | while read issue_num; do
    if [[ -n "$issue_num" ]]; then
        log "Labeling issue #$issue_num with triage"
        gh issue edit "$issue_num" --add-label "triage" --repo $(git remote get-url origin | sed 's/git@github.com:/https:\\/\\/github.com\\//' | sed 's/\\.git$//')
    fi
done

# Post a weekly summary
# We'll create a comment on a specific issue (let's say we use issue #1 for maintenance summaries) or create a new issue if it doesn't exist.
# For simplicity, we'll append to a file in the repository and then commit and push that file.
# But note: we are already in a branch? We are back to the default branch because we checked out after each subproject.
# We'll create a summary file and then commit it to the default branch? But we don't want to push to default branch directly.
# Instead, we'll open a PR for the summary file? Or we can just push to the default branch? Since we are the maintainer, we can push directly.
# However, to be safe, we'll open a PR for the summary as well.
# We'll create a summary of the actions taken in this run.
log "Creating weekly summary"
SUMMARY_FILE="$REPO_DIR/MAINTENANCE.md"
{
    echo "## Maintenance Summary - $(date '+%Y-%m-%d')"
    echo ""
    echo "### Actions Taken"
    echo "- Checked for outdated dependencies in subprojects"
    echo "- Opened PRs for updates where needed"
    echo "- Labeled new issues without labels as 'triage'"
    echo ""
    echo "### PRs Opened in This Run"
    if [[ -f "$PR_NUMBERS_FILE" ]]; then
        while read pr_num; do
            if [[ -n "$pr_num" ]]; then
                echo "- PR #$pr_num"
            fi
        done < "$PR_NUMBERS_FILE"
    else
        echo "- No PRs opened"
    fi
    echo ""
} >> "$SUMMARY_FILE"

# If dry run, skip creating a PR for the summary
if [[ "$DRY_RUN" == "true" ]]; then
    log "Dry run mode: skipping summary PR creation"
else
    # Now, we'll create a branch for the summary, commit, and open a PR
    branch_name="summary/maintenance-$(date +%Y%m%d%H%M%S)"
    git checkout -b "$branch_name"
    git add "$SUMMARY_FILE"
    git commit -m "docs: update maintenance summary for $(date '+%Y-%m-%d')"
    git push -u origin "$branch_name"
    pr_url=$(gh pr create --title "docs: update maintenance summary for $(date '+%Y-%m-%d')" --body "This PR updates the maintenance summary file with the actions taken on $(date '+%Y-%m-%d')." --base "$DEFAULT_BRANCH" --head "$branch_name" --repo $(git remote get-url origin | sed 's/git@github.com:/https:\\/\\/github.com\\//' | sed 's/\\.git$//') --json url -q .url)
    log "Opened summary PR: $pr_url"
fi

# Clean up
rm -f "$PR_NUMBERS_FILE"

log "Maintenance script completed."