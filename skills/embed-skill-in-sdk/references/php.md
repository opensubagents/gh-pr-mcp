# Embedding a skill in PHP

SDK: [`anthropic-php`](https://platform.claude.com/docs/en/api/sdks/php) (PHP 8.1+). Install: `composer require anthropic-ai/sdk`.

## Minimum-viable embed

```php
<?php
require __DIR__ . "/vendor/autoload.php";

use Anthropic\Anthropic;

function loadSkill(string $skillDir): string {
    $md = file_get_contents($skillDir . "/SKILL.md");
    if (str_starts_with($md, "---")) {
        // ---\n<frontmatter>\n---\n<body>
        $parts = explode("\n---\n", $md, 2);
        if (count($parts) === 2) return trim($parts[1]);
    }
    return $md;
}

$client = Anthropic::factory()->fromEnv()->make();

$response = $client->messages()->create([
    "model" => "claude-opus-4-7",
    "max_tokens" => 1024,
    "system" => loadSkill("./skills/docx"),
    "messages" => [
        ["role" => "user", "content" => "Make me a quarterly status .docx"],
    ],
]);

echo $response->content[0]->text;
```

## With `references/` on demand

Add a `tools` entry to the messages payload; loop while `$response->stop_reason === "tool_use"`. Sanitize the requested path with `realpath()` and check it stays under the skill root.

## See also

- `spec-summary.md`, `catalog.md`
- https://github.com/anthropics/anthropic-sdk-php
