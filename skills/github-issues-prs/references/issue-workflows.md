# Issue workflows

This file covers a few related jobs: writing a new issue, triaging an existing one, and summarizing long threads.

## Writing a new issue

The thing that separates a useful bug report from a useless one is reproducibility. Push for it.

### Bug reports

```markdown
## Summary
One sentence: what's broken.

## Steps to reproduce
1. Concrete, numbered steps. Include exact inputs.
2. ...
3. ...

## Expected behavior
What should happen.

## Actual behavior
What does happen. Include error messages verbatim, stack traces in code blocks.

## Environment
- OS / browser / runtime version (whatever's relevant)
- Version of the project (commit, tag, or release)
- Anything else that might matter (locale, network, recent changes)

## Notes
Optional. What you've already tried, related issues, hypotheses.
```

If the user gives you a vague bug report ("it crashes sometimes") and asks you to file it, ask what they actually saw before drafting. A bug report you can't reproduce is a bug report that won't get fixed.

### Feature requests

```markdown
## Problem
The user-facing problem or friction. Avoid jumping to a solution.

## Proposed approach (optional)
If you have one in mind, but be open to alternatives.

## Alternatives considered
Why other approaches don't work as well.

## Additional context
Use cases, related discussion, prior art.
```

The "describe the problem before the solution" framing matters — well-scoped feature requests are easier to evaluate.

## Triaging an issue

When the user shares an issue and asks you to triage it:

1. Read the issue body and the comments. Long threads often have crucial context buried in comment 14.
2. Identify the core question: is this a bug, feature, support question, or duplicate?
3. Suggest:
   - **Labels** appropriate to the repo's conventions, if you can infer them. (Look at other recent issues to see what labels are in use.)
   - **Severity / priority**, with reasoning.
   - **Likely owner area** — which subsystem, team, or CODEOWNERS group should see this.
   - **Reproducibility status** — is it reproducible from the report, or does it need more info?
   - **Possible duplicates** — if the user mentions related issues or you spot likely overlaps.
4. If info is missing, draft the clarifying questions to ask the reporter.

Output as a brief markdown artifact with a triage block:

```markdown
## Triage: #{number} — {title}

**Type:** bug | feature | support | duplicate
**Severity:** ...
**Area:** ...
**Reproducible:** yes / no — needs {what}

### Suggested labels
`label-1`, `label-2`

### Action
What should happen next, in one or two sentences.

### Questions for the reporter (if any)
- ...
```

## Summarizing a long thread

When the user shares an issue with many comments and wants a summary:

1. Read the whole thread, not just the OP and the most recent comment.
2. Identify:
   - The original problem
   - How understanding evolved (what was tried, what was learned)
   - The current state — is this resolved? Stuck? Waiting on someone?
   - Decisions made, with the comment they were made in
   - Open questions
3. Output a brief summary that respects the reader's time:

```markdown
## Issue #{number}: {title}

**Status:** open / closed / stalled — {one-line status}

### What's going on
2–4 sentence summary of the actual problem and why it's interesting.

### Timeline
- **{Comment N, @user}:** key turn in the discussion
- **{Comment M, @user}:** ...

### Current state
What's true now. What's been ruled out. Who's working on what.

### Open questions
- ...
```

Don't reproduce comments verbatim except for short, load-bearing quotes. The point is to save the reader from having to read the thread.

## Output

All issue artifacts are markdown the user pastes into GitHub. Match the repo's templates if they exist (look in `.github/ISSUE_TEMPLATE/`).
