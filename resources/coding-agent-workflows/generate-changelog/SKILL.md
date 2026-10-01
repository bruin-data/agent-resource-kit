---
name: generate-changelog
description: Use when the user wants a customer-facing changelog, release notes, or a summary of recent changes, built from git history across one or more repositories in the current directory.
---

# Generate a changelog

**Status:** experimental · **Risk:** read-only

> Your project's release conventions win.

Generate a customer-facing changelog by analyzing all git repositories in the current working directory.

## Input

- **Time period**: Use `$ARGUMENTS` if provided, otherwise default to the past 2 weeks.
- **Repos**: All subdirectories in the current working directory that are git repositories.

`$ARGUMENTS` and the per-repo subagents in step 3 are Claude Code features. In
another agent, ask the user for the time period and analyse the repos one at a
time.

## Steps

### 1. Discover repos
List all subdirectories in the current working directory and identify which ones are git repositories.

### 2. Pull latest changes
Run `git pull --ff-only` in each repo to ensure they are up to date. Run these in parallel.

### 3. Analyze each repo in parallel
Launch a separate Agent (subagent_type: general-purpose) for **each repo** to analyze commits within the time period. Each agent should:

- Run `git log --since="<date>" --oneline` to list all commits in the period.
- For each commit (or group of related commits), run `git show <hash>` or `git diff <hash>~1 <hash>` to read the **actual code changes**. Commit messages are NOT reliable — always read the diffs. Look into the PR descriptions as well.
- Identify ONLY **user-facing changes**: new features, bug fixes users would notice, behavior changes, new commands/sources/destinations, UI changes, changed defaults, new settings, etc.
- **Ignore**: internal refactors, test-only changes, CI/CD changes, dependency bumps (unless they affect users, e.g. minimum version requirements), code cleanup that doesn't change behavior, documentation-only changes (unless documenting a new feature).
- For each change found, return:
  - A clear description of what changed **from the user's perspective**
  - The commit hash(es) involved
  - Category: "New Feature", "Improvement", "Bug Fix", or "Breaking Change"

### 4. Compile the changelog
Combine findings from all repos into a single, polished markdown changelog. Structure it as:

```markdown
# Changelog: <start date> to <end date>

## <Component or repo name>
- **Feature 1**: Description of the feature.
- **Feature 2**: Description of the feature.

## <Another component>
- **Feature 1**: Description of the feature.
- **Feature 2**: Description of the feature.
```

One heading per component the reader recognises, not one per repository. If two
repositories back a single product surface, merge them under that surface.

**Guidelines for writing**:
- Write for **customers**, not developers. Avoid internal codenames or implementation details.
- Group related changes across repos into single entries (e.g. if CLI + Cloud both added PostHog support, describe it once).
- Use clear, benefit-oriented language. Say what the user can now **do**, not what code was changed.
- Keep bug fix descriptions short (one line each).
- For breaking changes, always include what the user needs to do differently.
- Do NOT include commit hashes in the final changelog.
- Group a family of similar additions into one item rather than listing each.
- Skip plumbing that only exists to support something already listed.
- Do not use em dashes.
- Do not create dedicated sections for small features or improvements, group them as list items under a common heading.
- Skip internal-only surfaces: admin endpoints, staff tooling, internal APIs.

### 5. Write the file
Save the changelog as `CHANGELOG-<today's date in YYYY-MM-DD>.md` in the current working directory. Confirm the file path to the user.
