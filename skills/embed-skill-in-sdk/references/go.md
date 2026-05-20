# Embedding a skill in Go

SDK: [`anthropic-sdk-go`](https://platform.claude.com/docs/en/api/sdks/go) (Go 1.23+). Install: `go get github.com/anthropics/anthropic-sdk-go`.

## Minimum-viable embed

```go
package main

import (
    "context"
    "fmt"
    "os"
    "path/filepath"
    "strings"

    "github.com/anthropics/anthropic-sdk-go"
)

func loadSkill(skillDir string) (string, error) {
    b, err := os.ReadFile(filepath.Join(skillDir, "SKILL.md"))
    if err != nil {
        return "", err
    }
    md := string(b)
    if strings.HasPrefix(md, "---") {
        // ---\n<frontmatter>\n---\n<body>
        parts := strings.SplitN(md, "\n---\n", 2)
        if len(parts) == 2 {
            return strings.TrimSpace(parts[1]), nil
        }
    }
    return md, nil
}

func main() {
    client := anthropic.NewClient()
    body, err := loadSkill("./skills/docx")
    if err != nil {
        fmt.Fprintln(os.Stderr, err)
        os.Exit(1)
    }

    resp, err := client.Messages.New(context.Background(), anthropic.MessageNewParams{
        Model:     anthropic.F(anthropic.ModelClaudeOpus4_7),
        MaxTokens: anthropic.F(int64(1024)),
        System: anthropic.F([]anthropic.TextBlockParam{
            anthropic.NewTextBlock(body),
        }),
        Messages: anthropic.F([]anthropic.MessageParam{
            anthropic.NewUserMessage(anthropic.NewTextBlock("Make me a quarterly status .docx")),
        }),
    })
    if err != nil {
        fmt.Fprintln(os.Stderr, err)
        os.Exit(1)
    }
    for _, blk := range resp.Content {
        if blk.Type == "text" {
            fmt.Println(blk.Text)
        }
    }
}
```

## Context-based cancellation

Pass any `context.Context` to `Messages.New` — first arg. Use `context.WithTimeout` for request budgets.

## With `references/` on demand

Add a `Tool` to `MessageNewParams.Tools` whose schema accepts a relative path; the loop reads on demand and resolves against `skillDir`, rejecting any path that escapes.

## See also

- `spec-summary.md`, `catalog.md`
- https://github.com/anthropics/anthropic-sdk-go
