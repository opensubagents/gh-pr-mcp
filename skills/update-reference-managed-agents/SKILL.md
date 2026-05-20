---
name: update-reference-managed-agents
description: "Re-fetch one or more managed-agents markdown docs already in the /home/claude/refs/managed-agents/ cache, overwriting the local copy with the current version from platform.claude.com. Use when the user says 'refresh', 'update', 'pull latest', 'check for changes', or notes that cached info looks stale. Optionally diff old vs new and report what changed. For docs that aren't yet cached, defer to create-reference-managed-agents."
license: Proprietary
compatibility: "claude.ai web/mobile chat with code execution. Operates on /home/claude/refs/managed-agents/."
metadata:
  author: subagentcowork
  version: "0.1.0"
  surface: claude.ai
  scope: managed-agents-conceptual-docs
---

# update-reference-managed-agents

Re-fetch cached managed-agents docs to bring them in sync with `platform.claude.com`. The *update* half of the CRUD set.

## Why this exists separately from `create-`

Mechanically, "update" is just "fetch and overwrite" — the same thing `create-` does. They're separate skills for two reasons:

1. **Intent clarity.** "Update sessions.md" carries a different mental model than "create sessions.md": the user expects something already exists, expects a comparison, and may want to know whether anything actually changed.
2. **Default scope differs.** `create-` defaults to a single named topic; `update-` defaults to "everything that's currently cached", because refreshing a stale cache wholesale is a common operation.

Both skills end up calling `web_fetch` against the same canonical URL pattern. If you accidentally reach for `create-` to refresh, the result is fine; the user just won't get a diff.

## Source URL pattern

Same as `create-`:

```
https://platform.claude.com/docs/en/managed-agents/<topic>.md
```

The 20 valid topics are: overview, quickstart, onboarding, agent-setup, define-outcomes, tools, skills, mcp-connector, multi-agent, sessions, events-and-streaming, environments, cloud-containers, permission-policies, vaults, files, memory, github, webhooks, dreams.

## Workflow

1. **Determine targets.**
   - User named specific topics → those.
   - User said "all", "everything", "refresh the cache" → every topic listed in `.manifest.tsv`.
   - User said "stale ones" → use manifest timestamps; default cutoff is older than 7 days, but ask if the user implies a different threshold.

2. **For each target:**
   a. Confirm the file is currently cached (else punt to `create-`; updating something that doesn't exist is creating it).
   b. Save the current bytes to a temporary path: `cp /home/claude/refs/managed-agents/<topic>.md /tmp/<topic>.before.md`.
   c. `web_fetch` the canonical URL.
   d. Write the new body to `/home/claude/refs/managed-agents/<topic>.md`, overwriting.
   e. Update the manifest entry's timestamp (overwrite the existing line; don't append a duplicate).
   f. `diff /tmp/<topic>.before.md /home/claude/refs/managed-agents/<topic>.md`.
   g. Summarize the diff: unchanged / minor edit / substantive change. For substantive changes, surface the new sections by name; don't dump the whole diff inline unless the user asked.

3. **Report.** Per-topic outcome: "unchanged" / "updated (added section X, removed section Y)" / "fetch failed: <reason>". Don't bury failures.

## Diff summarization heuristics

- `diff` returns no output → unchanged. Say so concisely.
- A few lines changed → "minor edit" — note the line count and the affected section header(s).
- A whole new heading appeared / a heading disappeared → "substantive change". Name the headings.
- The whole doc was rewritten → "rewritten". Suggest the user re-read it.

The point is to give the user signal without dumping noise. They can always view the diff themselves; this skill's report is the *summary*.

## Anti-patterns

- **Don't update an uncached topic.** That's the `create-` skill's job. Tell the user.
- **Don't append manifest lines.** Update the existing line for the topic. The manifest is current-state, not history.
- **Don't web_fetch in parallel.** Same rate-limit reasoning as `create-`. Sequential.
- **Don't claim "no changes" without actually running diff.** If the fetch returned a different byte count, there were changes — surface them.
- **Don't fetch SDK mirrors or non-`/managed-agents/` paths.** Out of scope.

## Worked example

User: "refresh sessions and multi-agent — I think they updated the thread events"

1. Confirm both are cached. ✓
2. Snapshot both to /tmp.
3. `web_fetch` `sessions.md` → write → diff. Result: unchanged.
4. `web_fetch` `multi-agent.md` → write → diff. Result: substantive change — new section "Tool permissions and custom tools" with cross-thread routing detail.
5. Update manifest timestamps for both.
6. Report: "sessions.md unchanged. multi-agent.md updated — new section 'Tool permissions and custom tools' covers cross-thread routing of tool_confirmation/custom_tool_result events. Want me to summarize that section?"
