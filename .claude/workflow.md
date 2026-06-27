# Development Workflow

This repository uses GitHub Issues as the product backlog and OpenSpec as the source of truth for implementation specifications.

## Implementing an issue

Given a GitHub Issue number:

1. Read the GitHub Issue completely.
2. Create a feature branch: `feature/<issue-number>-<slug>`
3. Create an OpenSpec change: `openspec/changes/issue-<issue-number>-<slug>/`
   > Change names must start with a letter (`openspec status` rejects digit-leading names).
4. Write or update:
   - `proposal.md`
   - `tasks.md`
   - spec deltas (when behavior changes)
5. Do not begin implementation until the proposal and tasks exist.
6. Update `tasks.md` as work progresses.
7. Keep changes focused on the issue scope.
8. If new requirements emerge, stop and propose updating the issue and spec rather than implementing them implicitly.

## Before opening a Pull Request

- Acceptance criteria are satisfied.
- Tests pass (`pytest evals/callback_tests/tests/ -v`).
- Linter passes (`agents-cli lint --config gecx-config.json` — 0 errors, 0 warnings).
- OpenSpec validates.
- `tasks.md` reflects the completed work.
- PR description includes:
  - `Closes #<issue-number>`
  - OpenSpec change path

## After merge

Archive the OpenSpec change.
