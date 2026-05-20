# Drafting comments and replies on GitHub threads

Most "write me a comment for this thread" requests fall into a few shapes. They share a common principle: **the comment should move the thread forward.** A comment that doesn't change what happens next is noise.

## Common shapes

### Replying to a code review on your own PR

The author's job in PR-comment replies is to answer questions, push back where they disagree, and make small fixes invisible. Conventions:

- Address each comment individually, threaded under that review comment in GitHub. So produce *one short reply per comment*, not a single wall of text.
- For "I'll fix it" cases: a short acknowledgment is fine — `"Good catch, fixed."` Don't write a paragraph.
- For pushback: explain *why* concisely. "I'd rather keep this approach because X. Happy to revisit if Y." Disagreeing well is a skill — don't be defensive, do be specific.
- For "I don't understand the comment": ask for clarification rather than guessing. "Do you mean {interpretation A} or {interpretation B}?"
- For substantive issues that turn into design discussions: it's often better to take the discussion to a meeting/issue/sync chat and post a summary back, rather than nest a 12-comment design debate inside line-comments.

### Replying to a PR you're reviewing

Before posting a follow-up review comment, check whether your earlier concern was addressed. If yes, say so explicitly: "Thanks, this addresses the issue." That closes the loop for the author. If not, explain what's still open and what would resolve it.

### Replying to an issue thread

Common patterns:

- **Triage reply** — "Thanks for filing. Could you share {missing info}? In particular, {specific question}."
- **Acknowledgment** — "Confirmed reproducing on {versions}. Tracking internally; will update here when there's progress."
- **Closing** — "Closing as fixed in #{PR}; please reopen if you still see this on {version}."
- **Duplicate** — "This looks like a dup of #{number}. Closing in favor of that — feel free to add details there."

Be polite even when the issue is poorly written. Reporters often don't know what info is needed; asking nicely gets it.

### Asking for review

A short, specific ping. "@person — when you have a minute, could you take a look at the {area} changes? Mainly want eyes on {file or concern}." Tell the reviewer where to focus; that's a kindness and gets you faster review.

### Following up on a stale PR/issue

If something has gone quiet, a gentle nudge that adds new information beats "any update?". Examples:

- "Bumping this — happy to make changes, just let me know what direction you want."
- "FYI this is now blocking {downstream thing}; let me know if there's anything I can do to help unstick."
- "If this doesn't fit roadmap right now I'm happy to close — let me know."

## Tone

- **Match the thread.** Casual project, casual reply. Formal codebase, formal reply. Don't show up in business prose to a friendly OSS hangout.
- **Direct, kind, brief.** Most GitHub comments should be 1–4 sentences. Reviewers and authors both have other PRs to look at.
- **First person, normal voice.** "I think this might..." rather than performative humility ("I sincerely apologize for the inconvenience...").
- **No throat-clearing.** Skip "I just wanted to say" and "Sorry for the late reply" boilerplate. Get to the point.
- **No emoji unless the thread already has them.** Some teams emoji freely; others don't. Match.

## Output

For a single reply: short prose in chat is fine; the user just needs the words. Inline code in backticks if relevant.

For a multi-comment review reply (where the user has many points to respond to at once), produce a numbered or bulleted list, each item labeled with which review comment it's replying to:

```markdown
**On `auth.ts:47`:** Fixed in latest commit.

**On `session.ts:92`:** I'd actually rather keep the early return here because {reason}. Happy to revisit if you feel strongly.

**On the test file:** Good idea — added a case for the null path.
```

The user will copy each chunk into the corresponding GitHub comment thread.

## What not to write

- A wall-of-text reply that addresses six things in one comment. Split it.
- Defensive paragraphs explaining why a critique is unfair. If you disagree, say so in one sentence and offer the specific counter-evidence.
- Promises you might not keep ("I'll have this done by end of day"). Either commit specifically or don't commit.
- Re-arguing decisions that were already made elsewhere. If a maintainer closed an issue saying "out of scope", it's not productive to reopen the debate in a comment.
