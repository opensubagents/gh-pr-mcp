---
name: create-reference-managed-agents
description: "Fetch and cache one or more conceptual /managed-agents/ markdown docs from platform.claude.com into the chat's local filesystem so subsequent questions are answered from cache instead of repeated web_fetches. Use when the user says 'cache', 'fetch', 'load', 'pull', 'preload', 'add to cache', 'create a reference', or names a managed-agents topic and wants its content brought local. Pair with read-reference-managed-agents (answer from cache), update-reference-managed-agents (re-fetch), and delete-reference-managed-agents (clear)."
license: Proprietary
compatibility: "claude.ai web/mobile chat with code execution. Cache lives in /home/claude/refs/managed-agents/ and persists for the lifetime of the chat sandbox."
metadata:
  author: subagentcowork
  version: "0.1.0"
  surface: claude.ai
  scope: managed-agents-conceptual-docs
---

# create-reference-managed-agents

Fetch managed-agents conceptual markdown docs and cache them locally so the rest of the chat can read them from disk.

## Why this exists

Without a cache, every question about Managed Agents costs another `web_fetch`. The 20 conceptual docs at `platform.claude.com/docs/en/managed-agents/` change rarely within a session, so fetching once and reading from disk is faster, cheaper, and lets you cite specific files reliably. This skill is the *write* half of the CRUD set.

## Scope — what this skill caches

**In scope (exactly 20 topics).** The conceptual `/managed-agents/` docs only:

```
overview              quickstart           onboarding           agent-setup
define-outcomes       tools                skills               mcp-connector
multi-agent           sessions             events-and-streaming environments
cloud-containers      permission-policies  vaults               files
memory                github               webhooks             dreams
```

**Out of scope.** Anything else, including: `/api/beta/...` reference endpoints (use `llms-crud` for those), Messages API docs (`/build-with-claude/...`), tool-use docs (`/agents-and-tools/...`), Claude Code docs (`code.claude.com/...`). If the user asks to cache one of those, decline and point to the right place.

## URL pattern

Every fetch goes to:

```
https://platform.claude.com/docs/en/managed-agents/<topic>.md
```

The trailing `.md` is mandatory — `platform.claude.com` is a Mintlify host and the canonical machine-readable URL is the `.md` variant. Drop it and you get the rendered HTML wrapper.

## Cache layout

Files are written to `/home/claude/refs/managed-agents/<topic>.md`. Create the directory if missing (`mkdir -p`). Overwriting is allowed — re-running `create` for the same topic is equivalent to `update`.

Alongside each file, append a one-line manifest entry to `/home/claude/refs/managed-agents/.manifest.tsv`:

```
<topic>\t<iso8601-fetch-timestamp>\t<source-url>
```

The manifest is the truth source for "what's cached". `read-` and `delete-` skills consult it.

## Workflow

1. **Validate the topic.** If the user names something not in the 20-topic list above, stop and tell them it's out of scope. Do not invent URLs.
2. **Fetch with `web_fetch`** at the canonical URL. If it fails, surface the error verbatim — do not fall back to a different URL.
3. **Write the body to `/home/claude/refs/managed-agents/<topic>.md`.** Use the response body exactly as returned; no reformatting.
4. **Append manifest entry.** ISO 8601 UTC timestamp.
5. **Report.** Tell the user which topics were cached, file sizes, and the manifest path. Don't dump the markdown content — that's `read-`'s job.

## Bulk mode

If the user says "all", "everything", "all 20", or "the whole set", loop over all 20 topics. Fetches are sequential (web_fetch is rate-limited; don't try to parallelize). Show a progress line per topic so a partial failure is obvious.

## Anti-patterns

- **Don't fetch SDK language mirrors.** `/api/python/...`, `/api/typescript/...`, etc. are out of scope; `llms-crud` covers them lazily on demand.
- **Don't fetch without `.md`.** The HTML wrapper is wasteful and inconsistent.
- **Don't paraphrase the cached content into the manifest.** The manifest is metadata only — topic, timestamp, URL.
- **Don't silently skip a failed fetch.** If 3/20 fail in bulk mode, list the three by name at the end.

## Worked example

User: "cache sessions and multi-agent for me"

1. Validate: both are in the 20-topic list. ✓
2. `web_fetch https://platform.claude.com/docs/en/managed-agents/sessions.md` → write to `/home/claude/refs/managed-agents/sessions.md`
3. Append manifest line.
4. `web_fetch https://platform.claude.com/docs/en/managed-agents/multi-agent.md` → write to `/home/claude/refs/managed-agents/multi-agent.md`
5. Append manifest line.
6. Report: "Cached sessions (12.4KB) and multi-agent (28.1KB). Manifest at /home/claude/refs/managed-agents/.manifest.tsv. Use read-reference-managed-agents to query."
