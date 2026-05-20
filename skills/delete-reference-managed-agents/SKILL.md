---
name: delete-reference-managed-agents
description: "Remove one or more cached managed-agents markdown docs from /home/claude/refs/managed-agents/ and clean up the manifest. Use when the user says 'clear', 'delete', 'remove', 'evict', 'purge', 'forget', or 'reset the cache' for a specific topic or for the whole cache. For destructive whole-cache wipes, confirm before deleting unless the user used emphatic language."
license: Proprietary
compatibility: "claude.ai web/mobile chat with code execution. Operates on /home/claude/refs/managed-agents/."
metadata:
  author: subagentcowork
  version: "0.1.0"
  surface: claude.ai
  scope: managed-agents-conceptual-docs
---

# delete-reference-managed-agents

Evict cached managed-agents docs. The *delete* half of the CRUD set.

## Why this exists

The cache is local and ephemeral, but it's not free: every cached doc takes up working set the user doesn't want to think about. Reasons to delete:

- The user is done with a topic and wants to declutter.
- A doc fetched once turned out to be irrelevant.
- The user wants a clean slate before bulk-recreating with `create-`.
- The cache feels stale and the user prefers wiping over per-topic `update-`.

This skill exists separately so the destructive verb stays explicit. Confusing "delete" with "update" or "create" is bad. Routing through a skill named `delete-` makes the intent unambiguous.

## Workflow

1. **Determine targets.**
   - User named specific topics → those.
   - User said "all", "everything", "the whole cache", "wipe", "reset" → every cached file plus the manifest itself.

2. **For named-topic deletes:**
   - `rm /home/claude/refs/managed-agents/<topic>.md`.
   - Remove the corresponding line from `.manifest.tsv` (don't leave dangling manifest entries).
   - Report what was deleted.

3. **For whole-cache wipes:**
   - If the user's wording is unambiguous ("delete everything", "wipe the cache", "reset"), proceed.
   - If the wording is ambiguous ("clean up", "I'm done"), ask once: "Delete all N cached files? `rm -rf /home/claude/refs/managed-agents/`?" Wait for confirmation.
   - Then `rm -rf /home/claude/refs/managed-agents/`.
   - Report what was removed (count + total bytes).

4. **Idempotency.** If the user asks to delete a topic that isn't cached, say so plainly — don't error, don't pretend it succeeded. "sessions.md wasn't cached; nothing to delete."

## Anti-patterns

- **Don't delete files outside `/home/claude/refs/managed-agents/`.** This skill's blast radius is exactly that one directory. If a path-like argument escapes it (`..`, absolute paths elsewhere, etc.), refuse.
- **Don't run `rm -rf` on a parent directory by accident.** Always anchor at `/home/claude/refs/managed-agents/`.
- **Don't auto-confirm an `rm -rf` of the whole cache.** Even though the cache is reproducible (just rerun `create-`), wiping is still a destructive verb the user should explicitly own.
- **Don't leave the manifest out of sync.** A line in `.manifest.tsv` for a file that no longer exists is a lie. Either update the line or, for whole-cache wipes, delete the manifest along with everything else.
- **Don't suggest the user `web_fetch` the deleted content "just in case" before deleting.** If they wanted to keep it, they wouldn't be asking to delete it. Trust the user.

## Worked examples

### Single topic

User: "delete the sessions one, I don't need it anymore"

1. Target: `sessions.md`.
2. `rm /home/claude/refs/managed-agents/sessions.md`.
3. Remove `sessions\t…` line from `.manifest.tsv`.
4. Report: "Deleted sessions.md (12.4KB). Cache now has N other topics."

### Wipe (unambiguous)

User: "reset the whole cache"

1. `ls /home/claude/refs/managed-agents/` → 8 files + manifest, total 187KB.
2. Word "reset" + "whole cache" → unambiguous.
3. `rm -rf /home/claude/refs/managed-agents/`.
4. Report: "Wiped cache: 8 files, 187KB removed. Use create-reference-managed-agents to repopulate."

### Wipe (needs confirmation)

User: "clean up the refs"

1. `ls /home/claude/refs/managed-agents/` → 8 files, 187KB.
2. "Clean up" is ambiguous — could mean delete all, could mean delete just the stale ones, could mean trim manifest cruft.
3. Ask: "Delete all 8 cached files (187KB total) and the manifest? Or do you mean something narrower like deleting docs older than X days?"
4. Proceed only on explicit confirmation.

### Idempotent miss

User: "remove dreams"

1. Target: `dreams.md`. Check cache: not present.
2. Report: "dreams.md isn't cached. Nothing to delete."
