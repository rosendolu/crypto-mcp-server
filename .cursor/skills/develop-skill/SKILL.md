---
name: develop-skill
description: Implements a controlled Git workflow: create a feature branch from `main`, push all commits to that branch as a single PR to `main`, run a `code-review` using the project `code-review` skill, then fix all review findings (Critical / Suggestion / Nice-to-have) and push updates to the same PR until it is ready.
---

# Develop Skill

## Instructions

This skill is used to implement a new change in this repo while enforcing:

- Branching: always start from `main` and develop on a `feature/<short-description>` branch.
- PR scope: exactly one PR to `main` per development cycle (multiple commits are allowed, but they must stay on the same branch/PR).
- Review loop: after the PR is opened, perform a code review using the `code-review` skill, then fix all findings before concluding.

### Phase 1: Prepare branch from `main`

1. Ensure the repo has the latest `main`:
   - `git fetch origin`
   - `git switch main` (or `git checkout main`)
   - `git pull --ff-only origin main`
2. Create a feature branch:
   - Convert the user’s change description into a short slug (letters/numbers/hyphens only; no spaces).
   - Branch name format: `feature/<short-description>`
   - If the branch already exists locally or remotely, pick a unique suffix (e.g. `-2`, `-3`).
3. Switch to the feature branch from `main`:
   - `git switch -c feature/<short-description>`
   - (Optional but recommended) `git push -u origin HEAD` after the first commit is ready.

### Phase 2: Implement the change (single PR)

1. Implement the requested change on the feature branch only.
2. Do not start a second PR while this development cycle’s PR is open.
3. Commit changes on the same branch (multiple commits are fine).
4. Before opening the PR:
   - Confirm you are still on the same `feature/<short-description>` branch.
   - Confirm `git diff`/`git status` matches the intended scope.

### Phase 3: Push branch and open PR to `main`

1. Push the feature branch:
   - `git push -u origin HEAD`
2. Open exactly one PR from the feature branch to `main` using GitHub CLI:
   - `gh pr create --base main --head feature/<short-description> --title "<PR title>" --body "<PR body>"`
3. Use a clear PR title derived from the user’s request.
4. If the PR is already open for the branch, reuse it and do not create a duplicate PR.

### Phase 4: Code review loop (must reference `code-review`)

1. Perform code review using the `code-review` skill:
   - Use its required output structure: `Summary`, then `Critical`, `Suggestion`, `Nice-to-have`, followed by `Test plan` and `Recommendation`.
2. Interpret review findings:
   - Fix all issues reported under `Critical`, `Suggestion`, and `Nice-to-have`.
3. Iterate until review findings are resolved:
   - Make fixes on the same feature branch.
   - Commit fixes.
   - Push updates to the same branch so the open PR reflects the changes.
4. Only conclude after the PR’s review findings are addressed (at minimum: no remaining Critical/Suggestion/Nice-to-have items).

### Phase 5: Close-out

After the loop completes, provide:

- A short summary of the final changes made after review.
- The PR link/identifier.
- A confirmation that all `code-review` findings were fixed and pushed to the same PR.

## Notes / Guardrails

- If the user requests an additional unrelated change while the PR is open, treat it as a new development cycle: start a new feature branch and a new PR (do not mix unrelated scope into the current PR).
- If `gh` is not configured or PR creation fails, ask the user for permission to fall back to manual PR instructions.

