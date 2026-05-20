# Embedding a skill in C#

SDK: [`Anthropic.SDK`](https://platform.claude.com/docs/en/api/sdks/csharp) (.NET Standard 2.0+). Install: `dotnet add package Anthropic.SDK`.

## Minimum-viable embed

```csharp
using Anthropic.SDK;
using Anthropic.SDK.Messaging;
using System.IO;
using System.Threading.Tasks;

static string LoadSkill(string skillDir)
{
    var md = File.ReadAllText(Path.Combine(skillDir, "SKILL.md"));
    if (md.StartsWith("---"))
    {
        // ---\n<frontmatter>\n---\n<body>
        var parts = md.Split(new[] { "\n---\n" }, 2, System.StringSplitOptions.None);
        if (parts.Length == 2) return parts[1].Trim();
    }
    return md;
}

var client = new AnthropicClient();
var skillBody = LoadSkill("./skills/docx");

var response = await client.Messages.GetClaudeMessageAsync(new MessageParameters
{
    Model = AnthropicModels.ClaudeOpus4_7,
    MaxTokens = 1024,
    System = new List<SystemMessage> { new SystemMessage(skillBody) },
    Messages = new List<Message>
    {
        new Message(RoleType.User, "Make me a quarterly status .docx"),
    },
});

System.Console.WriteLine(response.FirstMessage?.Text);
```

## With `IChatClient` (Microsoft.Extensions.AI integration)

```csharp
IChatClient chatClient = new AnthropicClient().Messages.AsChatClient();
// Standard IChatClient surface; system prompt set via ChatOptions.Instructions.
```

## With `references/` on demand

Define a `Tool` (`Anthropic.SDK.Common.Tool`) whose function accepts a path string; resolve it against `skillDir` with a traversal check.

## See also

- `spec-summary.md`, `catalog.md`
- https://github.com/anthropics/anthropic-sdk-csharp
