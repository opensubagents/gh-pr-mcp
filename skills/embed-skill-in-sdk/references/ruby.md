# Embedding a skill in Ruby

SDK: [`anthropic`](https://platform.claude.com/docs/en/api/sdks/ruby) (Ruby 3.2+). Install: `gem install anthropic` or add `gem "anthropic"` to your Gemfile.

## Minimum-viable embed

```ruby
require "anthropic"
require "pathname"

def load_skill(skill_dir)
  md = Pathname.new(skill_dir).join("SKILL.md").read
  return md unless md.start_with?("---")
  # ---\n<frontmatter>\n---\n<body>
  _, _, body = md.split("---", 3)
  body.strip
end

client = Anthropic::Client.new

msg = client.messages.create(
  model: :"claude-opus-4-7",
  max_tokens: 1024,
  system: load_skill("./skills/docx"),
  messages: [{ role: "user", content: "Make me a quarterly status .docx" }],
)

puts msg.content.first.text
```

## With `references/` on demand

```ruby
read_skill_file = Anthropic::Tool.new(
  name: "read_skill_file",
  description: "Read a file from the skill's references/ or scripts/ directory.",
  input_schema: {
    type: "object",
    required: ["path"],
    properties: { path: { type: "string" } },
  },
)
# Pass `tools: [read_skill_file]` to messages.create and dispatch on stop_reason == "tool_use".
```

## With Sorbet types

The SDK ships Sorbet types — `Anthropic::Models::MessageCreateParams` etc. — for runtime type checks. The minimum-viable code above works with or without `sorbet-runtime`.

## See also

- `spec-summary.md`, `catalog.md`
- https://github.com/anthropics/anthropic-sdk-ruby
