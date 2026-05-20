# Skill catalog — where to pull skills from

## anthropics/skills (17 reference skills, MIT)

`https://github.com/anthropics/skills`. The canonical Anthropic-authored set. All bundled with Claude Code; available via `npx skills add` or `/plugin install <name>@anthropic-agent-skills`.

| Skill | Purpose |
|---|---|
| algorithmic-art | p5.js generative art, flow fields, particles |
| brand-guidelines | Anthropic brand colors + typography |
| canvas-design | .png / .pdf design pieces |
| claude-api | Build/debug/optimize Claude API apps, model migration |
| doc-coauthoring | Co-authoring docs, proposals, specs |
| docx | Word documents |
| frontend-design | Production frontend UI components |
| internal-comms | Status reports, FAQs, incident reports |
| mcp-builder | Build MCP servers |
| pdf | PDF read/edit/merge/split/OCR |
| pptx | PowerPoint slides |
| skill-creator | Author + eval new skills |
| slack-gif-creator | Slack-optimized animated GIFs |
| theme-factory | Style artifacts with preset/custom themes |
| web-artifacts-builder | Multi-component claude.ai HTML artifacts |
| webapp-testing | Playwright UI testing |
| xlsx | Spreadsheets |

Fetch a single skill:

```bash
git clone --depth=1 --filter=blob:none --no-checkout https://github.com/anthropics/skills.git _ax
cd _ax && git sparse-checkout init --no-cone
echo "skills/<name>/" > .git/info/sparse-checkout && git checkout
```

## agentskills/agentskills (spec + reference SDK)

`https://github.com/agentskills/agentskills`. The spec repo. Carries the reference Python SDK and example skills under `skills-ref/`. Apache-2.0 for code; CC-BY-4.0 for docs.

Use this as the authoritative source for the SKILL.md format, validation rules, and the Python reference loader you can copy into your own app.

## Your own skills

If you've authored skills with `skill-creator` (or copied from one of the above), they live in your project at any of:

- `~/.claude/skills/` (Claude Code, user scope)
- `<project>/.claude/skills/` (Claude Code, project scope)
- `<your-app>/skills/` (self-hosted via this skill)

The self-hosted case is what `embed-skill-in-sdk` exists for.

## Cross-source pattern

When the user names a skill without saying which source, search in order: project-local → user-scope → anthropics/skills catalog → agentskills/skills-ref. First hit wins.
