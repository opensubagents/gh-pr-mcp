# Embedding a skill in Java

SDK: [`anthropic-java`](https://platform.claude.com/docs/en/api/sdks/java) (Java 8+, also works for Kotlin and Scala). Install:

```xml
<dependency>
  <groupId>com.anthropic</groupId>
  <artifactId>anthropic-java</artifactId>
  <version>LATEST</version>
</dependency>
```

## Minimum-viable embed

```java
import com.anthropic.client.AnthropicClient;
import com.anthropic.client.okhttp.AnthropicOkHttpClient;
import com.anthropic.models.messages.Message;
import com.anthropic.models.messages.MessageCreateParams;
import com.anthropic.models.messages.Model;

import java.nio.file.Files;
import java.nio.file.Path;

public class EmbedSkill {

    static String loadSkill(Path skillDir) throws Exception {
        String md = Files.readString(skillDir.resolve("SKILL.md"));
        if (md.startsWith("---")) {
            String[] parts = md.split("(?m)^---$", 3);
            if (parts.length >= 3) return parts[2].strip();
        }
        return md;
    }

    public static void main(String[] args) throws Exception {
        AnthropicClient client = AnthropicOkHttpClient.fromEnv();

        MessageCreateParams params = MessageCreateParams.builder()
            .model(Model.CLAUDE_OPUS_4_7)
            .maxTokens(1024)
            .system(loadSkill(Path.of("./skills/docx")))
            .addUserMessage("Make me a quarterly status .docx")
            .build();

        Message msg = client.messages().create(params);
        msg.content().forEach(block -> block.text().ifPresent(t -> System.out.println(t.text())));
    }
}
```

## Async with CompletableFuture

```java
AnthropicClientAsync client = AnthropicOkHttpClientAsync.fromEnv();
client.messages().create(params).thenAccept(msg -> {
    msg.content().forEach(b -> b.text().ifPresent(t -> System.out.println(t.text())));
});
```

## With `references/` on demand

Same tool-use loop as the other languages — define a `read_skill_file` tool, plug into `MessageCreateParams.builder().addTool(...)`, recurse on `stop_reason == TOOL_USE`. Sanitize the path to prevent traversal outside `skillDir`.

## Kotlin / Scala

The Java SDK works as-is. In Kotlin you can drop the explicit builder pattern and use a DSL helper if you prefer.

## See also

- `spec-summary.md`, `catalog.md`
- https://github.com/anthropics/anthropic-sdk-java
