---
name: github-issues-prs
description: Work with GitHub issues, pull requests, diffs, and release notes inside claude.ai chat — without a terminal or the gh CLI. Use this skill whenever the user shares a github.com URL (issue, PR, commit, file), pastes an issue body, PR description, code review thread, or unified diff, or asks to draft/review/triage/summarize anything related to GitHub. Trigger on phrases like "review this PR", "draft a PR description", "write release notes from these merged PRs", "triage this issue", "summarize the discussion on issue #123", "is this diff sane", "write me a follow-up comment on this thread", or even just a bare GitHub URL. Also use when the user wants to compare what a PR description claims vs. what the diff actually changes, write reproduction steps for a bug report, or generate a copy-pasteable code review. Use this skill even if the user doesn't say the words "GitHub" or "skill" — the presence of github.com URLs, diff syntax (lines starting with +/-), or PR/issue jargon (LGTM, WIP, draft, milestone, assignee) is enough.
---

# GitHub Issues & Pull Requests (claude.ai chat)

This skill helps the user work with GitHub issues and PRs from inside claude.ai chat. The user is on the web/mobile chat interface — not Claude Code, not Claude Code on the web. That changes what's available, so the first thing to internalize is what you can and can't do here.

## What's actually available in claude.ai chat

- **`web_fetch`** works on public github.com URLs. This is the workhorse. The user can also paste content directly.
- **"Add from GitHub"** (+ menu) lets the user attach files or whole repos as context.
- **GitHub MCP connector** — *if* the user has connected one (check their connectors list before assuming). When present, you can list issues, post comments, etc. directly. When absent, output is copy-pasteable artifacts only.
- **No `gh` CLI**, no shell access to GitHub credentials, no GitHub proxy. Don't pretend otherwise.
- **No automatic posting back to GitHub** without an MCP connector. The deliverable is text/markdown the user pastes themselves.

If a task genuinely needs API access the user doesn't have (e.g., "post this comment on issue #42 for me"), say so plainly and offer the copy-pasteable version instead. Don't fabricate a tool call.

## URL forms worth knowing

`web_fetch` returns rendered page content. The form of the URL changes what you get:

| You want | URL pattern |
|---|---|
| Issue with comments | `https://github.com/{owner}/{repo}/issues/{N}` |
| PR overview (description, conversation, files-changed list) | `https://github.com/{owner}/{repo}/pull/{N}` |
| **The diff itself** | `https://github.com/{owner}/{repo}/pull/{N}.diff` |
| Diff with commit metadata (author, message, timestamps) | `https://github.com/{owner}/{repo}/pull/{N}.patch` |
| A specific commit's diff | `https://github.com/{owner}/{repo}/commit/{sha}.diff` |
| A file at a specific ref | `https://raw.githubusercontent.com/{owner}/{repo}/{ref}/{path}` |
| Compare two refs | `https://github.com/{owner}/{repo}/compare/{base}...{head}.diff` |

For PR review, you almost always want **both** the overview URL (for context, description, prior discussion) and the `.diff` URL (for the actual changes). The HTML overview page truncates large diffs; the `.diff` form gives you the whole thing.

If `web_fetch` fails (private repo, rate limit, deleted), say so and ask the user to paste the content instead. Don't loop on retries.

## Core workflows

The skill has a handful of canonical jobs. Pick the one that matches the user's ask, then use the corresponding reference file for detailed structure:

| Task | Reference |
|---|---|
| Reviewing a PR | `references/pr-review.md` |
| Drafting a PR description | `references/pr-description.md` |
| Triaging or writing an issue | `references/issue-workflows.md` |
| Generating release notes / changelog from merged PRs | `references/release-notes.md` |
| Drafting comments / replies on a thread | `references/comment-drafting.md` |

Read the relevant reference file *before* producing the deliverable. They're short and contain format conventions that matter (e.g., what good review comments look like, what reviewers expect to see in a PR description).

For a request that doesn't fit cleanly into any of those — "summarize this 80-comment issue thread", "compare what the description claims vs. what the diff actually changes", "translate this stack trace into a reproducer" — work from first principles using the general guidance below.

## General guidance

**Read before you write.** When given a URL, fetch it before drafting anything. If given a diff, read the whole diff. Don't summarize from the description alone — descriptions lie (or drift, or are stale), and the user often wants you precisely *because* they suspect a gap between description and reality.

**Be specific about file/line references.** "There's a potential issue in the auth code" is useless. "In `src/auth/session.ts:47`, the new check happens after the cookie is set, so a malformed token still produces a Set-Cookie header" is useful. Reviewers and authors both work in coordinates — file paths, line numbers, function names. Use them.

**Output as artifacts when the user will copy-paste back to GitHub.** PR descriptions, review comments, issue bodies, release notes — these are standalone documents. Put them in a markdown artifact so the user can grab the whole thing cleanly. For shorter inline answers ("is this PR ready to merge?"), prose in chat is fine.

**Quote sparingly and exactly.** When citing a specific line of code or a specific sentence from the description, quote it verbatim and short. Don't paraphrase code. Don't reproduce huge swaths of the diff back at the user — they have it.

**Be honest about uncertainty.** If you can't tell from the diff whether a change is correct (e.g., it depends on call sites you can't see, or runtime behavior, or test fixtures not in the PR), say so. Phrase it as a question for the author, not a confident verdict. "Does `processBatch` get called with `null` anywhere? If so, this `length` access will throw" is better than "This will throw on null input."

**Match the project's voice.** If the repo uses formal commit-message conventions (Conventional Commits, sign-offs, issue templates), follow them. If the user pastes prior PR descriptions or comments from the repo, mirror their tone — a casual side project gets casual review prose, a regulated-industry codebase gets clinical precision.

## When the user shares only a URL

A bare github.com URL is a request to read-and-react. Default behavior:

1. Fetch it.
2. Briefly say what it is (one sentence: "This is PR #234, 'Add rate limiting to /api/login', open, 14 files changed").
3. Ask what they want — review, summary, draft a comment, something else. **Don't dump a full review unprompted unless the user explicitly asked for one.** Many people share URLs as "look at this with me, I'll tell you what I want" rather than "give me everything you've got."

Exception: if the surrounding chat context makes the ask obvious ("can you review this? <url>"), skip the clarifying question and proceed.

## When MCP is available

If the user has a GitHub MCP connector turned on, you can list issues, fetch PRs, post comments, etc. through real tool calls instead of `web_fetch` + copy-paste. Prefer the MCP path when available — it's faster and avoids round-tripping through the user's clipboard. Still produce the artifact for review *before* posting; humans should approve their own GitHub comments.

If the user keeps asking you to do things that require write access and there's no MCP connector, mention once that connecting GitHub via Settings → Connectors would let you post directly. Don't keep mentioning it.

## What this skill is not for

- Running `git` commands locally — they don't have a shell here.
- Compiling/testing the code in a PR — no code execution against arbitrary repos in chat. (If the user uploads files and the change is self-contained, the analysis tool can sometimes help, but that's a different skill.)
- Replacing actual code review by a teammate. Frame your output as "a draft to refine" or "a first pass", not "the review."
