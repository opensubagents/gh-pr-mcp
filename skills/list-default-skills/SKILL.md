---
name: list-default-skills
description: "Use this skill whenever the user asks what skills, capabilities, tools, or built-in abilities are available in this claude.ai chat session. Triggers on phrases like 'list skills', 'what skills do you have', 'what can you do', 'show me your tools', 'available capabilities', 'what's installed', or 'inventory'. Also use this when the user wants to know which Anthropic-shipped skills are mounted, the difference between public and example skills, or which skill handles a specific file type (docx, pdf, pptx, xlsx). Do NOT use this for the user's own custom skills — use list-subagent-skills for those."
license: Proprietary
compatibility: "claude.ai web/mobile chat on Max 20x with Claude Opus 4.x. Snapshot of mounted skills at /mnt/skills/{public,examples}/."
metadata:
  author: subagentcowork
  version: "0.2.0"
  spec: https://agentskills.io/specification
  surface: claude.ai
  model_family: claude-opus-4
---

# List Default Skills

Anthropic-shipped skills mounted in a claude.ai chat session.

## Public (`/mnt/skills/public/`)

`docx`, `pdf`, `pptx`, `xlsx` — create/edit Office files.
`pdf-reading` — extract from PDFs.
`file-reading` — router for uploaded files.
`frontend-design` — production web UIs.
`product-self-knowledge` — Anthropic product facts.

## Examples (`/mnt/skills/examples/`)

`doc-coauthoring`, `web-artifacts-builder`, `skill-creator`, `theme-factory`,
`mcp-builder`, `internal-comms`, `canvas-design`, `brand-guidelines`,
`slack-gif-creator`, `algorithmic-art`.

## How to respond

State surface (claude.ai/Max 20x/Opus 4.x), then list grouped by mount path. Don't invent skills not in this list. End with: "For user-authored skills, see `list-subagent-skills`."

## Quick launch (Claude Code v2.1.91+)

```
claude-cli://open?repo=subagentcowork/subagentskills&q=Read%20SKILL.md%20in%20the%20list-default-skills%20skill%20and%20give%20me%20the%20inventory.
```

## Verify

`view /mnt/skills/public/<name>/SKILL.md` — confirm a skill is actually mounted before quoting it.

## See also

- Spec: https://agentskills.io/specification
- Companion: `list-subagent-skills`
- Deep-link reference: https://code.claude.com/docs/en/deep-links.md
