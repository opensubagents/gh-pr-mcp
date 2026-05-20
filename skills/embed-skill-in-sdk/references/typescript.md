# Embedding a skill in TypeScript

SDK: [`@anthropic-ai/sdk`](https://platform.claude.com/docs/en/api/sdks/typescript) (TS 4.9+, Node.js 20+). Install: `npm i @anthropic-ai/sdk`.

## Minimum-viable embed

```typescript
import Anthropic from "@anthropic-ai/sdk";
import { readFileSync } from "node:fs";
import { join } from "node:path";

function loadSkill(skillDir: string): string {
  const md = readFileSync(join(skillDir, "SKILL.md"), "utf8");
  if (md.startsWith("---")) {
    // ---\n<frontmatter>\n---\n<body>
    const [, , body] = md.split(/^---$/m);
    return body.trim();
  }
  return md;
}

const client = new Anthropic();
const msg = await client.messages.create({
  model: "claude-opus-4-7",
  max_tokens: 1024,
  system: loadSkill("./skills/docx"),
  messages: [{ role: "user", content: "Make me a quarterly status .docx" }],
});
console.log(msg.content[0].type === "text" ? msg.content[0].text : "");
```

## With `references/` loaded on demand

```typescript
import { resolve } from "node:path";

const readSkillFile = {
  name: "read_skill_file",
  description: "Read a file from the skill's references/ or scripts/ directory.",
  input_schema: {
    type: "object",
    required: ["path"],
    properties: { path: { type: "string" } },
  },
};

function handleTool(skillDir: string, name: string, args: any): string {
  if (name !== "read_skill_file") throw new Error(`unknown tool: ${name}`);
  const target = resolve(skillDir, args.path);
  if (!target.startsWith(resolve(skillDir))) return "error: path escapes skill directory";
  return readFileSync(target, "utf8");
}
```

Pass `tools: [readSkillFile]` and loop while `response.stop_reason === "tool_use"`.

## With prompt caching

```typescript
const msg = await client.messages.create({
  model: "claude-opus-4-7",
  max_tokens: 1024,
  system: [
    { type: "text", text: loadSkill("./skills/docx"),
      cache_control: { type: "ephemeral" } },
  ],
  messages: [{ role: "user", content: "..." }],
});
```

## Browser / Deno / Bun

Same SDK, same API. For browser usage you must proxy via your backend (don't ship the API key client-side). Skill file loading needs `fetch` instead of `readFileSync`.

## See also

- `spec-summary.md`, `catalog.md`
- claude-api skill's `typescript/` reference for tool-use loop boilerplate
