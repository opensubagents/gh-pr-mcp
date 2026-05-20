# Embedding a skill via raw cURL

No SDK — the bedrock. Useful for shell scripting, debugging, and any language that lacks an official SDK (Rust, Swift, Elixir, …).

## Minimum-viable embed

```bash
#!/usr/bin/env bash
set -euo pipefail

SKILL_DIR="./skills/docx"

# Strip frontmatter from SKILL.md — keep everything after the second `---` line
SKILL_BODY=$(awk '/^---$/{c++; next} c==2' "$SKILL_DIR/SKILL.md")

curl https://api.anthropic.com/v1/messages \
    --silent --show-error \
    -H "x-api-key: $ANTHROPIC_API_KEY" \
    -H "anthropic-version: 2023-06-01" \
    -H "content-type: application/json" \
    --data "$(jq -n \
        --arg model "claude-opus-4-7" \
        --argjson max_tokens 1024 \
        --arg system "$SKILL_BODY" \
        --arg prompt "Make me a quarterly status .docx" \
        '{model: $model, max_tokens: $max_tokens, system: $system,
          messages: [{role: "user", content: $prompt}]}')"
```

## With prompt caching

Wrap the system as a block array with `cache_control`:

```bash
--arg system_text "$SKILL_BODY" \
'{model: $model, max_tokens: $max_tokens,
  system: [{type: "text", text: $system_text, cache_control: {type: "ephemeral"}}],
  messages: [{role: "user", content: $prompt}]}'
```

## With `references/` on demand

Add a `tools` array to the payload describing `read_skill_file`. When the response's `stop_reason` is `tool_use`, re-call `/v1/messages` appending the assistant turn + a user turn with `tool_result` content. Standard tool-use loop, just in shell.

## See also

- `spec-summary.md`, `catalog.md`
- https://platform.claude.com/docs/en/api/sdks/cli for the official `ant` CLI which wraps this
