---
name: read-reference-managed-agents
description: "Answer questions about Claude Managed Agents concepts (sessions, threads, vaults, permission policies, multiagent, define-outcomes, memory stores, environments, files, github, webhooks, dreams, etc.) by reading from the 20 `.md` reference files bundled inside this skill. Use whenever the user asks how a managed-agents concept works, names any topic in the /docs/en/managed-agents/ namespace, or follows up on something previously discussed from these docs. Prefer this over web_fetch — the canonical docs ship with the skill."
license: Proprietary
compatibility: "claude.ai web/mobile chat (or any environment with file `view` access). Bundled references at `references/` cover the 20 conceptual /managed-agents/ docs as snapshotted on the date listed in SNAPSHOT.md. No network required."
metadata:
  author: subagentcowork
  version: "2.1.0"
  surface: claude.ai
  scope: managed-agents-conceptual-docs
  snapshot: "2026-05-09"
---

# read-reference-managed-agents

Answer Managed Agents questions from the 20 bundled reference docs in `references/`. Cold start is zero — no fetch, no cache build, no init.

## Why v2 ships the docs

v1 fetched at runtime, costing one `web_fetch` per topic per fresh sandbox. v2 bundles the 20 conceptual docs from `platform.claude.com/docs/en/managed-agents/` directly under `references/`, with a pre-built `manifest.md` outline and machine-readable `manifest.tsv` carrying line ranges for every H1/H2/H3 section. Reading is a local file `view`, not a network round-trip.

The companion skill `update-reference-managed-agents` is the only network-touching half of the set; it overwrites files in `references/` (or an overlay at `/home/claude/refs/managed-agents/`, depending on environment writability) when the user asks for a refresh.

## Self-steering routine — do this in one turn

When a question lands that maps to managed-agents content, run all five steps in the same turn before writing the answer. Don't split across turns.

0. **Check for an overlay.** If the companion `update-reference-managed-agents` skill has run in this sandbox, fresher copies of the docs live at `/home/claude/refs/managed-agents/<topic>.md`. Run `ls /home/claude/refs/managed-agents/ 2>/dev/null` once at the start of the turn. For any file present there, prefer it over the bundled `references/<topic>.md` for steps 2–3. The bundled `manifest.tsv` line ranges still apply unless the overlay has been re-built (line drift after a re-fetch is ISSUE-4 in the session manifest); when in doubt, scan the overlay file by header text rather than line range.
1. **Scan the outline.** `view references/manifest.md`. ~5KB, gives you every section across all 20 files in a glance.
2. **Locate the section.** `grep` (or scan) `references/manifest.tsv` for header text matching the question. Each row is `file <TAB> level <TAB> header <TAB> start_line <TAB> end_line`.
3. **Open the slice, not the file.** `view <chosen-path>/<file>.md` with `view_range=[start_line, end_line]` from the matched row, where `<chosen-path>` is the overlay path if present, otherwise `references`. Open the whole file only when the question is broad ("what does the overview say about X?") or the section is short.
4. **Answer with citation.** Cite as `file.md § Section`. Quote sparingly; paraphrase carefully — fidelity to the doc is the whole point of bundling it. If the overlay was used, note "(refreshed copy)" in the citation so the user knows it's not the bundled snapshot.

If the question spans topics, repeat steps 2–3 per topic. If after step 2 nothing in the manifest looks relevant, the topic is genuinely outside scope — see "Out of scope" below.

## Worked example — single turn

User: "what's the difference between a session thread and the primary thread?"

Turn:
- `view references/manifest.md` → see `multi-agent.md` has a `## Threads` H2 and a `### Primary thread events` H3.
- `grep -i thread references/manifest.tsv` confirms `multi-agent.md  H2  Threads  L84  L156`.
- `view references/multi-agent.md` with `view_range=[84, 156]`.
- Answer, citing `multi-agent.md § Threads`: primary thread = condensed view across all threads in the session; session threads = individual agent activity, one per delegated agent. Tool permission events from non-coordinator agents cross-post to the primary thread with `session_thread_id`.

The whole sequence is three tool calls plus the response. No turn is wasted on "let me first check if this is cached."

## When to view the whole file vs. a slice

- **Slice** (default): you have a specific section header from the manifest. Use the row's `start_line` / `end_line`.
- **Whole file**: the question is the file's topic itself ("walk me through how vaults work"), or sections are tightly interlinked and the file is small (< 200 lines per `wc -l`).
- **Multiple slices from one file**: separate `view` calls per slice are fine; cheaper than reading the whole file when both sections are short.

## Out of scope — what this skill does NOT cover

The 20 bundled docs are conceptual `/managed-agents/` only. The following are out of scope:

- **API reference endpoints** (`/api/beta/sessions/*`, request/response shapes). Use the `llms-crud` skill, which web_fetches `.md` URLs under `/api/beta/`.
- **Messages API**, tool-use docs, Claude Code, Claude.ai consumer docs. Different namespaces, different skills.
- **SDK language mirrors** (`/api/python/`, `/api/typescript/`, etc.). Out of scope for the same reason.

When a question lands outside the 20, tell the user, name the right tool, and stop. Do not invent content. Do not paraphrase from training-data memory dressed up as the docs.

## Topic routing cheatsheet

Common phrasing → likely file:

| User says | Read this |
|---|---|
| "how do I create a session" / session lifecycle | `sessions.md` |
| "event stream format" / "session.* events" | `events-and-streaming.md` |
| "multiagent" / "coordinator" / "session threads" | `multi-agent.md` |
| "permission policies" / "always_ask" / "tool confirmation" | `permission-policies.md` |
| "define an outcome" / "rubric" / "grader" | `define-outcomes.md` |
| "vault" / "credentials" / "MCP OAuth" | `vaults.md` |
| "memory store" / "memory tool persistence" | `memory.md` |
| "agent skills" (in managed-agents context) | `skills.md` |
| "container" / "/mnt/session/" | `cloud-containers.md` |
| "environments" | `environments.md` |
| "GitHub access" / "GitHub PAT" | `github.md` |
| "webhooks" | `webhooks.md` |
| "files" (in managed-agents context) | `files.md` |
| "dreams" / async pipelines | `dreams.md` |
| "MCP connector" (in managed-agents context) | `mcp-connector.md` |
| getting started | `quickstart.md`, `onboarding.md` |
| agent definition fields | `agent-setup.md` |
| inventory / first-look | `overview.md` |
| pre-installed packages, tools list | `tools.md`, `cloud-containers.md` |

When the cheatsheet is ambiguous, fall back to the manifest — it always wins.

## Staleness handling

`SNAPSHOT.md` records the fetch date for the bundled docs. If the question hinges on something likely to have shipped *after* that date — new event types, new beta header values, recently-announced endpoints — mention the snapshot date in the answer and suggest `update-reference-managed-agents` to refresh before relying on it.

Don't be paranoid: settled topics (overview structure, define-outcomes shape, basic session lifecycle) don't churn week to week. Reserve staleness flags for plausibly-changed surface area.

## Outcomes — what a good run looks like

A response from this skill is good when:

1. **Cold start is zero.** No `web_fetch`, no "let me cache this first." The bundled refs are the cache.
2. **One turn answers.** The four-step routine above completes in a single turn. The user does not see "checking…" interstitials.
3. **The cited section actually contains the claim.** Open the section before claiming what's in it. If the slice doesn't support the claim, widen the view or pick a different section — don't paper over it.
4. **Quotes are accurate and short.** Paraphrase by default; quote only when wording is load-bearing.
5. **Out-of-scope is named, not faked.** "That's API reference, not in this skill — try `llms-crud` for `/api/beta/sessions.md`."
6. **Stale-risk is flagged.** When the topic is likely to have moved, say so and offer `update-`.

## What never to do

- **Never invent.** If the manifest doesn't list it, the cache doesn't have it. Say so.
- **Never `web_fetch` from inside this skill.** Read-only. Refreshes belong to `update-reference-managed-agents`.
- **Never paraphrase into something subtly different.** The bundle exists so the user gets the docs verbatim.
- **Never skip the manifest.** Opening files at random wastes tokens and risks missing the right section.
- **Never split the routine across turns.** Manifest → grep → slice → answer all happen in one turn.

## Refreshing the manifest after `update-`

If a sibling skill has overwritten any reference file, regenerate the manifest:

```bash
python3 scripts/build_manifest.py references/
```

This rewrites `references/manifest.md` and `references/manifest.tsv` with the current line ranges. It only reads from `references/` and only writes the two manifest files; doc files are untouched.

## File inventory

20 conceptual docs + 2 manifests + this SKILL.md + SNAPSHOT.md + scripts/build_manifest.py.

Bundled topics: `overview, quickstart, onboarding, agent-setup, define-outcomes, tools, skills, mcp-connector, multi-agent, sessions, events-and-streaming, environments, cloud-containers, permission-policies, vaults, files, memory, github, webhooks, dreams`.
