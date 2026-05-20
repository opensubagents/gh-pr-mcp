---
name: install-api-skill
description: "Install Anthropic's official `claude-api` Agent Skill into the current chat sandbox by sparse-cloning it from github.com/anthropics/skills and copying it to /home/claude/skills/claude-api/, so future turns in this conversation can read it on demand. TRIGGER aggressively whenever the user says 'install claude-api', 'add the claude-api skill', 'cp this skill into chat', 'make claude-api available here', references `npx skills add ... --skill claude-api`, references `/plugin install claude-api@anthropic-agent-skills`, or asks to set up the Claude API / Anthropic SDK / Managed Agents skill in this chat. Also use this when the user wants to migrate Claude model versions (4.5→4.6, 4.6→4.7) inside this chat — the cloned skill carries the `/claude-api migrate` flow. Do not answer with install instructions from memory; run the steps in this skill instead."
---

# install-claude-api

Install the `claude-api` skill from `github.com/anthropics/skills` into this chat's filesystem at `/home/claude/skills/claude-api/`, then treat it as if it were a mounted skill — i.e., view its `SKILL.md` whenever a Claude-API / Anthropic-SDK / Managed-Agents / model-migration task comes up later in the conversation.

## Canonical install paths (for Claude Code / Skills-aware hosts)

If the user is **not** in a claude.ai web/mobile chat, prefer the official commands:

```bash
npx skills add https://github.com/anthropics/skills --skill claude-api
```

Or as a Claude Code plugin:

```text
/plugin marketplace add anthropics/skills
/plugin install claude-api@anthropic-agent-skills
```

Stop here in those environments — those commands register the skill in the host's auto-discovery list, which is the real install.

## Install path for **this** chat sandbox (claude.ai web/mobile/desktop)

In a claude.ai chat the `<available_skills>` list is platform-controlled and read-only; `npx skills add` is unavailable. The equivalent is a sparse `git clone` + `cp` into the chat's writable home, plus a commitment to consult the skill manually.

Run this in one `bash_tool` call:

```bash
mkdir -p /home/claude/skills && \
cd /home/claude/skills && \
git clone --depth=1 --filter=blob:none --sparse https://github.com/anthropics/skills.git _anthropic-skills && \
cd _anthropic-skills && \
git sparse-checkout set skills/claude-api && \
mv skills/claude-api /home/claude/skills/claude-api && \
cd /home/claude/skills && \
rm -rf _anthropic-skills && \
head -5 /home/claude/skills/claude-api/SKILL.md
```

Verify the layout:

```bash
ls /home/claude/skills/claude-api/
# expect: SKILL.md  LICENSE.txt  python/  typescript/  java/  go/  ruby/  csharp/  php/  curl/  shared/
```

## After install

Tell the user, briefly:
1. Skill is at `/home/claude/skills/claude-api/`.
2. It persists only for this chat's container lifetime — resets on new conversation.
3. When they ask any Claude-API-shaped task later (SDK code, prompt caching, streaming, tool use, batch, Managed Agents, `/claude-api migrate ...`), `view /home/claude/skills/claude-api/SKILL.md` first and follow its language-detection + file-reading instructions before answering.

That's the install.
