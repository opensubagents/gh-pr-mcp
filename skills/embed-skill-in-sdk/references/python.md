# Embedding a skill in Python

SDK: [`anthropic`](https://platform.claude.com/docs/en/api/sdks/python) (Python 3.9+). Install: `pip install anthropic`.

## Minimum-viable embed (SKILL.md → system prompt)

```python
from anthropic import Anthropic
from pathlib import Path

def load_skill(skill_dir: str | Path) -> str:
    """Read SKILL.md from a skill folder, strip the frontmatter, return the body."""
    md = Path(skill_dir).joinpath("SKILL.md").read_text(encoding="utf-8")
    if md.startswith("---"):
        # ---\n<frontmatter>\n---\n<body>
        _, _, body = md.split("---", 2)
        return body.strip()
    return md

client = Anthropic()
msg = client.messages.create(
    model="claude-opus-4-7",
    max_tokens=1024,
    system=load_skill("./skills/docx"),
    messages=[{"role": "user", "content": "Make me a quarterly status .docx"}],
)
print(msg.content[0].text)
```

## With `references/` loaded on demand

When SKILL.md tells the LLM "read references/<name>.md when X happens", expose a tool that lets it do so. Standard tool-use loop:

```python
read_skill_file = {
    "name": "read_skill_file",
    "description": "Read a file from the skill's references/ or scripts/ directory.",
    "input_schema": {
        "type": "object",
        "required": ["path"],
        "properties": {"path": {"type": "string", "description": "Relative to skill root, e.g. references/foo.md"}},
    },
}

def handle_tool(skill_dir: Path, tool_name: str, args: dict) -> str:
    if tool_name == "read_skill_file":
        # Defense: prevent path traversal outside skill_dir
        target = (skill_dir / args["path"]).resolve()
        if not str(target).startswith(str(skill_dir.resolve())):
            return "error: path escapes skill directory"
        return target.read_text(encoding="utf-8")
    raise ValueError(f"unknown tool: {tool_name}")
```

Plug the tool into `client.messages.create(..., tools=[read_skill_file])` and loop while `response.stop_reason == "tool_use"`.

## With `scripts/` as executable tools

For each script in `scripts/`, wrap it as a tool that subprocess-invokes it. Pass the LLM-supplied arguments via stdin or argv depending on what the script expects. Sandbox: run in a temp dir, drop privileges, enforce timeouts.

## With prompt caching (recommended for any non-trivial skill)

The `system` block is a perfect cache breakpoint — skills are stable across many requests:

```python
msg = client.messages.create(
    model="claude-opus-4-7",
    max_tokens=1024,
    system=[
        {"type": "text", "text": load_skill("./skills/docx"),
         "cache_control": {"type": "ephemeral"}},
    ],
    messages=[{"role": "user", "content": "..."}],
)
```

## See also

- `spec-summary.md` — the format
- `catalog.md` — where to pull skills from
- Per-language reference for the `claude-api` skill if you also need streaming, batches, or Managed Agents
