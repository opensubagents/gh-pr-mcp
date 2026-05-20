# gh-pr-mcp

Minimum-viable MCP server: **edit some files → open a PR**. Three tools, one persistent token, raw HTTP to GitHub's git data API. No `gh` CLI, no `git` binary, no shell-outs.

## What it replaces

The whole flow from the previous chat session (apt install gh → device flow → clone → branch → sed → commit → push → gh pr create → token scrubbing) collapses to **one MCP tool call**:

```json
{
  "name": "gh_open_pr",
  "arguments": {
    "repo": "opensubagents/opensubagents",
    "branch": "docs/v2-readme-prose-bump-to-10",
    "title": "docs(v2-research): bump README prose from 8 to 10 prompt files",
    "body": "Four prose references...",
    "message": "docs(v2-research): bump README prose 8 → 10",
    "edits": [
      { "path": ".claude/agents-research/v2/README.md", "content": "# V2 research prompts\n\n> 10 prompt files for ..." }
    ]
  }
}
```

The atomic primitive inside is a 6-call sequence to GitHub's git data API: base ref → blobs (one per edit) → tree (base + blobs) → commit → branch ref → pulls. One commit, one PR.

## One-time auth (device flow)

```
gh_auth_device_start  → returns "open github.com/login/device, enter code ABCD-1234"
[human approves in browser]
gh_auth_device_finish → polls 60 s, saves token to ~/.gh-pr-mcp-token
```

After that, every subsequent `gh_open_pr` call uses the saved token without further interaction. The token lives at `$GH_PR_MCP_TOKEN_PATH` (default `~/.gh-pr-mcp-token`, mode 0600). To revoke, delete the file and visit https://github.com/settings/applications.

The OAuth client_id defaults to gh CLI's published one (`178c6fc778ccc68e1d6a`) — good enough for development. For production, register your own GitHub OAuth App and set `GH_DEVICE_CLIENT_ID`.

## Install

### In Claude Code

```bash
git clone <this repo> ~/gh-pr-mcp && cd ~/gh-pr-mcp && npm i
claude mcp add gh-pr -- npx tsx ~/gh-pr-mcp/src/gh-pr-mcp.ts
```

Restart `claude` once. The 3 tools appear under `gh-pr`.

### In Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "gh-pr": {
      "command": "npx",
      "args": ["tsx", "/abs/path/to/gh-pr-mcp/src/gh-pr-mcp.ts"]
    }
  }
}
```

### As a remote MCP (claude.ai mobile / web)

The stdio server above doesn't ship to claude.ai directly. To bridge:

- **Wrap in Workers** — port `openPr` to `fetch()`-style streamable HTTP (the GitHub calls are already `fetch`), store the token in Workers KV instead of disk, expose `/mcp` per the MCP streamable-HTTP spec. Deploys via `wrangler deploy`. Then add `https://<your-worker>.workers.dev/mcp` as a custom connector in claude.ai.
- **Wrap in Docker + `mcp-proxy`** — run this binary in a container, front it with [`sparfenyuk/mcp-proxy`](https://github.com/sparfenyuk/mcp-proxy) which exposes stdio MCP servers over SSE / streamable HTTP.

Either way, the code in `src/gh-pr-mcp.ts` is the load-bearing core; the transport is the wrapper.

## Tool surface

| Tool | Purpose | When called |
|---|---|---|
| `gh_auth_device_start` | Begin OAuth device flow, return user_code + URL | Once per machine (or after token revocation) |
| `gh_auth_device_finish` | Poll for the access token, save to disk | Once, immediately after the human approves |
| `gh_open_pr` | Bundle file edits → one commit → one PR | Every PR |

## Why edits are full file contents, not diffs

The git data API takes blobs, not patches. The orchestrator (Claude, in this case) already knows the post-edit state of each file — it just generated it. Patches would force a round-trip to compute them. Passing full contents is the shorter path.

For very large files where this is wasteful, the right extension is a separate `gh_open_pr_via_patch` tool that takes unified diff and uses GitHub's REST contents API or three-way merge — out of scope for v0.1.

## What this deliberately omits

- **Diff editing** — see above
- **Branch updates / force-pushes** — v0.1 creates new branches only; reusing an existing branch errors out
- **Multi-repo / monorepo coordination** — one repo per call
- **Review requests, labels, assignees** — caller can use the `body` to `@mention`; structured review APIs come in v0.2 if useful
- **Webhook / event handling** — read-only programmatic surface for now

These are all small additions to the same `Server.setRequestHandler` block. The point of v0.1 is to make the bare minimum case (the chat session you and I just walked through) take one tool call.
