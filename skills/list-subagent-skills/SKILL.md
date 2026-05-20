---
name: list-subagent-skills
description: "Use when the user asks about their custom subagent skills, the subagentskills repo, or how to fetch markdown documentation. Triggers: 'list subagent skills', 'what custom skills', 'show my skills', 'subagentskills inventory', and any question about sitemap entry points or .md / index.md URL conventions. Also routes to the four-skill managed-agents reference CRUD set, the llms-crud API navigator, github-issues-prs, and rss-to-kimball-postgres. Use BEFORE web_fetch on any docs.claude.com, code.claude.com, support.claude.com, anthropic.com, claude.com, platform.claude.com, or developers.cloudflare.com URL — this skill carries the suffix rules."
license: Proprietary
compatibility: "claude.ai web/mobile chat on Max 20x with Claude Opus 4.x. Inventory + doc-source rules for the subagentskills/ repo."
metadata:
  author: subagentcowork
  version: "0.4.0"
  spec: https://agentskills.io/specification
  surface: claude.ai
  model_family: claude-opus-4
  vendor_manifests: vendor/
---

# List Subagent Skills + Doc-Source Rules

User-authored skills under `subagentskills/`, plus URL conventions for fetching Anthropic/Cloudflare docs as markdown.

## Skills

Nine custom skills, grouped by what they're for. The list below is the **packaging-time** inventory; the next-best-thing-to-runtime check is one shell command:

```bash
ls -1 /mnt/skills/user/ 2>/dev/null
```

When the user asks "what skills do I have", run that first and reconcile with the prose below. Anything in `/mnt/skills/user/` not listed below is a newer addition (good — mention it as such). Anything listed below but missing from the directory was uninstalled (mention as "no longer mounted in this session"). The prose categorization is durable; the file-system list is authoritative.

### Meta — skill inventory

- **`list-default-skills`** — Anthropic-shipped skill inventory (the `/mnt/skills/public/` and `/mnt/skills/examples/` set).
- **`list-subagent-skills`** — this skill. Custom skills + doc-source rules.

### Managed Agents reference — CRUD set + API navigator

The four-skill set keeps `platform.claude.com/docs/en/managed-agents/` content local so questions are answered from disk, not from `web_fetch`.

- **`create-reference-managed-agents`** — fetch and cache one or more of the 20 conceptual `/managed-agents/` docs into `/home/claude/refs/managed-agents/`. Triggers on "cache", "fetch", "load", "preload".
- **`read-reference-managed-agents`** — answer questions from the cached docs without re-fetching. Triggers on "how does multiagent work", "what's a session thread", any managed-agents concept question.
- **`update-reference-managed-agents`** — re-fetch one or more cached docs, overwriting the local copy with the current version. Triggers on "refresh", "pull latest", "check for changes".
- **`delete-reference-managed-agents`** — clear specific topics or the whole cache. Triggers on "clear", "purge", "forget".

Companion for the API surface (different namespace, different topology):

- **`llms-crud`** — URL navigator for `platform.claude.com/docs/en/api/beta/` (sessions, agents, environments, vaults, files, memory stores, etc.). Carries the CRUD-verbs × resource-tree topology and dedupes the 10× SDK-language mirror copies in `llms.txt`. Use BEFORE `web_fetch` on any `/managed-agents/` or `/api/beta/` URL.

### Standalone tooling

- **`github-issues-prs`** — work with GitHub issues, PRs, diffs, and release notes inside chat without a terminal or `gh` CLI. Triggers on a bare `github.com` URL, diff syntax, PR/issue jargon ("LGTM", "WIP", "draft"), or asks to "review this PR" / "draft a PR description" / "write release notes" / "triage this issue".
- **`rss-to-kimball-postgres`** — decompose any RSS / Atom feed into a Kimball-style dimensional model (fact tables, SCD dimensions, event tables) targeting Postgres 16, with a bash-driven dev loop. Profiles the feed first, then designs the simplest schema that fits. Triggers on RSS-to-Postgres, "Kimball this feed", star schema language, or pasted `rss.xml` URLs paired with warehouse intent.

## Doc-source rules

**Anthropic Mintlify sites — append `.md` to path:**
`docs.claude.com`, `code.claude.com`, `support.claude.com`, `agentskills.io`, `platform.claude.com`.

```
https://code.claude.com/docs/en/deep-links     →  add .md
https://code.claude.com/docs/en/deep-links.md
```

**Cloudflare developer docs — append `/index.md` to directory:**
```
https://developers.cloudflare.com/agents/claude-code/
https://developers.cloudflare.com/agents/claude-code/index.md
```

**English-only:** stick to `/en/` paths.

## Vendor URL manifests

`vendor/<name>/urls.md` per vendor: `anthropics`, `agentskills`, `cloudflare`, `modelcontextprotocol`, `redis`, `github`, `graphql`. Consult the manifest to find the canonical URL, then apply the suffix rule.

## How to respond

State surface, list relevant skills (group, not all 9 unless asked), jump to the relevant rule + manifest. End with: "For Anthropic-shipped skills, see `list-default-skills`."

When the user asks for a specific concern, route to the most-fit skill rather than dumping the whole inventory:

- managed-agents docs question → `read-reference-managed-agents` (or `create-` if not cached)
- managed-agents API endpoint → `llms-crud`
- GitHub URL or PR/issue/diff text → `github-issues-prs`
- RSS / feed / dimensional modeling → `rss-to-kimball-postgres`
- "what skills do I have" → return the grouped inventory above

## Quick launch (Claude Code v2.1.91+)

```
claude-cli://open?repo=subagentcowork/subagentskills&q=Read%20SKILL.md%20in%20the%20list-subagent-skills%20skill%20and%20list%20my%20custom%20skills.
```

```
claude-cli://open?repo=subagentcowork/subagentskills&q=Fetch%20a%20page%20from%20Anthropic%20or%20Cloudflare%20docs%20as%20markdown.%20Use%20the%20.md%20or%20%2Findex.md%20suffix%20rule%20from%20list-subagent-skills%2FSKILL.md.
```

```
claude-cli://open?repo=subagentcowork/subagentskills&q=Run%20the%20evals%20at%20evals%2Fevals.json%20for%20this%20skill%2C%20comparing%20with-skill%20vs%20without-skill%2C%20then%20write%20benchmark.json.
```

## See also

- Spec: https://agentskills.io/specification
- Companion: `list-default-skills`
- Deep-link reference: https://code.claude.com/docs/en/deep-links.md
