# Agent Skills format (agentskills.io summary)

Open spec maintained by Anthropic + community contributors, Apache-2.0. The canonical source is https://agentskills.io and https://github.com/agentskills/agentskills.

## Folder layout

```
<skill-name>/
├── SKILL.md              # required — frontmatter + body
├── references/           # optional — Markdown docs, loaded on demand
├── scripts/              # optional — executable code (Python, shell, JS, etc.)
└── assets/               # optional — templates, fonts, images, used in output
```

## SKILL.md frontmatter

```yaml
---
name: my-skill                          # required, matches dir name
description: One-line plus triggers     # required, this is THE trigger surface
license: MIT                            # optional but recommended
compatibility: ["python>=3.9"]          # optional, free-form
---
```

The `description` is what the host LLM sees in its `<available_skills>` block. It's the only thing always-loaded; everything else is progressive disclosure.

## Progressive disclosure (three levels)

| Level | What loads | When |
|---|---|---|
| 1. Metadata | `name`, `description` | Always in the LLM's context |
| 2. Body | `SKILL.md` markdown body | When the skill triggers |
| 3. Bundled | `references/`, `scripts/`, `assets/` | Only when SKILL.md tells the LLM to read them |

This is the load-bearing design choice: a skill can be huge on disk (hundreds of pages of `references/`) but cheap in context (just the description + body).

## Discovery

A host (Claude Code, Claude Desktop, claude.ai, or your own SDK-driven app) finds skills by:

1. **Scanning** a directory for `SKILL.md` files
2. **Reading a manifest** (Skills Management API on the Claude API account, or a config file in the host)
3. **Direct mount** (the host hardcodes a path)

The skill itself doesn't care which — it just needs to be reachable on the filesystem at runtime.

## Frontmatter validation rules (from agentskills/agentskills/skills-ref)

- `name` is alphanumeric + dashes, matches directory name
- `description` is ≤ 1024 characters, no `<` or `>` characters
- Reserved sections: `## Hard rules`, `## Boundaries` (some host validators enforce these)

## Authoring vs. embedding

The split this skill makes:

- **Authoring**: writing a new skill. Use `skill-creator`. Out of scope here.
- **Embedding**: integrating an *existing* skill into your own Claude-API-powered app. That's what `embed-skill-in-sdk` covers.
