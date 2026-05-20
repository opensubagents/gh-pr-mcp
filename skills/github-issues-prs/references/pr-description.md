# Drafting a pull request description

A good PR description answers, in order: *why is this change happening, what does it do, how should the reviewer approach it.* Reviewers read top-to-bottom and bail when they have what they need, so front-load the important stuff.

## Inputs to gather

- **The diff** (or the user's description of what they changed).
- **The linked issue or context**, if there is one — what problem is this solving?
- **Repo conventions.** Look for `.github/PULL_REQUEST_TEMPLATE.md` (or `pull_request_template.md` at repo root) via `web_fetch` — if the repo has one, follow it. Some repos enforce specific sections, sign-offs, or checkboxes.
- **The user's commit messages**, if shared — they often contain the "why" that should land in the description.

## Default structure

If there's no template, use this:

```markdown
## What

One short paragraph: what this PR changes, in plain language. Not a file list. Not a play-by-play of the diff. The thing a reviewer needs to hold in their head.

## Why

The motivating problem or goal. Link the issue if there is one ("Fixes #123"). If this is a follow-up to prior work, link the prior PR.

## How

The approach, especially if it's non-obvious. Alternatives you considered and why you didn't take them. Anything tricky about the implementation.

## Test plan

How you verified this works. Specific commands, scenarios, manual steps, or test files added. If there are things you couldn't easily test, name them.

## Notes for reviewers

Optional. Where to start reading, what's mechanical vs. intentional, what feedback you're looking for.
```

Sections you don't need can be omitted. A one-line bug fix might just have **What** and **Test plan** and that's fine.

## Conventional Commits / linked issues

Many repos use Conventional Commits (`feat:`, `fix:`, `chore:`, `refactor:`) in PR titles. If the user's existing commits or recent PRs in the repo follow this, mirror it.

For linking issues, prefer GitHub's auto-close keywords if appropriate: `Fixes #123`, `Closes #456`. If the PR addresses an issue but doesn't fully resolve it, use `Refs #123` instead — auto-closing an issue prematurely is a common annoyance.

## What to leave out

- A line-by-line walkthrough of the diff. The diff is right there.
- Apologies for the size or messiness.
- Speculative future work that has nothing to do with this PR. Open a separate issue if you want to track it.
- Boilerplate sections with "N/A" everywhere. Cut sections that don't apply.

## Output

Produce the description as a markdown artifact, formatted for direct paste into the GitHub PR body.

If the user is updating an existing PR description (rather than writing the first one), preserve any sections they want to keep — ask before rewriting wholesale.
