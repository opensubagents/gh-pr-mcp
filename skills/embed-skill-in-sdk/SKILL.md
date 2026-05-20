---
name: embed-skill-in-sdk
description: "Wire an Agent Skill (per the agentskills.io open format) into a self-hosted Claude-API application. Covers all 7 official Anthropic SDKs (Python, TypeScript, Java, Go, Ruby, C#, PHP) plus raw cURL. TRIGGER when the user asks how to embed/load/mount/use a skill in their own app, pastes a SKILL.md and asks how to plug it in, asks about the skill runtime contract for an Anthropic SDK, says 'use the docx/pdf/xlsx skill in my Python service', or wants to know the difference between SDK-side embedding and the Skills Management API. SKIP when authoring a new skill (use skill-creator), installing into Claude Code or claude.ai (use install-api-skill), or general non-skill SDK usage (use claude-api)."
license: MIT
---

# embed-skill-in-sdk

Bridges the Agent Skills open format (agentskills.io) with the Anthropic Client SDKs. Given a skill folder and a target SDK language, this skill tells you exactly how to load `SKILL.md` into the system prompt, expose `references/` for on-demand reads, and register `scripts/` as tools.

## Routing

1. **Identify the target SDK language** from project files: `requirements.txt`/`pyproject.toml` → Python; `package.json`/`tsconfig.json` → TypeScript; `pom.xml`/`build.gradle` → Java; `go.mod` → Go; `Gemfile` → Ruby; `*.csproj` → C#; `composer.json` → PHP. If multiple, ask which.
2. **Identify the skill source**: a local folder, a path inside `anthropics/skills`, or the `agentskills/agentskills/skills-ref/` reference set. See `references/catalog.md`.
3. **Inspect the skill structure** with `scripts/inspect-skill.py <skill-dir>` — emits a JSON manifest (name, frontmatter, references, scripts, total size) so the per-language emission has real paths to reference.
4. **Read the relevant `references/<language>.md`** and emit the code.

## References

- `references/spec-summary.md` — the SKILL.md format, frontmatter contract, references/scripts/assets semantics, progressive disclosure
- `references/catalog.md` — known skill sources (anthropics/skills 17 + agentskills skills-ref)
- `references/{python,typescript,java,go,ruby,csharp,php,curl}.md` — per-language embed pattern

## What this skill does NOT do

| Want | Use this instead |
|---|---|
| Author a new skill from scratch | `skill-creator` |
| Install a skill into Claude Code / Claude Desktop / claude.ai | `install-api-skill` |
| General Messages API / Managed Agents reference | `claude-api` |
| Build an MCP server (tools, not skills) | `mcp-builder` |
| Migrate to a newer Claude model | `/claude-api migrate` |

## Output shape

Always emit working code in the user's target language. Cite the canonical SDK URL from `https://platform.claude.com/docs/en/api/sdks/{lang}` so the user can verify versions and platform support. Default model: `claude-opus-4-7`. Default thinking mode: `{type: "adaptive"}` per the claude-api skill's defaults.
