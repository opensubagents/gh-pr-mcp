# Reviewing a pull request

## Inputs to gather

Before drafting any review, you want:

1. **The PR overview** (`https://github.com/{owner}/{repo}/pull/{N}`) — description, conversation, files-changed list, current status.
2. **The diff** (`https://github.com/{owner}/{repo}/pull/{N}.diff`) — the actual changes.
3. **Linked issues**, if the description references "fixes #123" or "closes #456" — fetch those too. Knowing the original problem changes how you read the solution.
4. **Surrounding code**, only when needed. If a change touches `auth/session.ts` and you can't tell whether the new behavior is consistent with how the rest of the auth module works, fetch that file at the PR's head ref. Don't fetch everything; fetch on demand.

If you can't get any of these (private repo, rate limit), ask the user to paste them.

## What to look for

Review is mostly about asking *did this change actually do what it claims, and is the way it did it sensible?* Concretely:

- **Description ↔ diff alignment.** Does the diff actually do what the description says? Is anything in the diff that the description doesn't mention? Surprises are usually problems.
- **Bugs.** Off-by-ones, null/undefined access, race conditions, mishandled errors, resource leaks, infinite loops, broken edge cases. Be concrete — point at file:line.
- **Security.** New auth/permission logic, untrusted input flowing into queries/commands, secrets in code or logs, cookie/session handling, CORS, CSRF.
- **Tests.** Are there tests for the new behavior? Do they actually exercise it (not just instantiate it)? Are the assertions meaningful or trivially true?
- **API/contract changes.** Does this change a function signature, response shape, env var, or schema in a way callers need to know about? If yes, is that called out?
- **Style and consistency.** Does the new code look like surrounding code? Naming, error-handling patterns, logging conventions. Don't nitpick whitespace.
- **Scope creep.** PRs that do five things are harder to review and revert. Worth flagging.
- **Dead/unused code, leftover debug prints, commented-out blocks, TODOs without context.**

You don't have to comment on all of these every time. Pick what's actually worth saying.

## Output format

Produce a markdown artifact with this shape:

```markdown
## Summary
One paragraph: what this PR does, in your own words, based on the diff (not the description). If the description and diff diverge, say so here.

## Recommendation
**Approve** / **Request changes** / **Comment** — with one line of reason.

## Comments

### `path/to/file.ext`
- **Line 47:** Concrete observation. Why it matters. Suggested fix if obvious.
- **Line 92:** ...

### `path/to/other-file.ext`
- ...

## Questions for the author
- Things you can't tell from the diff alone.
- Phrased so the author can answer briefly.

## Nits (optional)
Truly minor things — naming preferences, comment phrasing. Mark them as nits so the author knows they're not blocking.
```

If there's nothing for a section, omit it.

## Tone

Direct, kind, reasoned. The author worked on this; assume good faith. Explain *why* a thing is a problem, not just that it is. Avoid:

- "This is wrong." → say what's wrong and why.
- "Refactor this." → say what about the structure makes future changes hard.
- Excessive softening ("I'm sorry but maybe possibly could you perhaps...") — it wastes the author's time and reads as evasive.

A good comment makes the author's next move obvious: "do X" or "answer Y" or "decide between A/B".

## Suggested-change blocks

For small, specific fixes, consider GitHub's suggested-change syntax — the author can apply it with one click:

````markdown
```suggestion
const result = await fetchUser(id);
if (!result) return null;
```
````

Use these for fixes that fit in 1–10 lines and are obviously correct. Don't use them for larger restructuring; that should be a conversation.

## When the diff is huge

If the PR is very large (thousands of lines, many files), don't try to review every line — you'll dilute the signal. Instead:

1. Read the description and the test files first; they tell you what the author thinks they did.
2. Skim file-by-file; flag the 3–5 files that look highest-risk and review those carefully.
3. Note that the PR is large enough that a careful review needs more time/eyes, and suggest splitting it if appropriate.

Be honest about coverage: "I focused on the auth and session changes; I didn't review the generated migration files or the vendored deps in `third_party/`."
