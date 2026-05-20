#!/usr/bin/env node
/**
 * gh-pr-mcp — minimum-viable MCP server for "edit some files, open a PR".
 *
 * Three tools, no shell-outs, no git binary, no gh CLI:
 *   1. gh_auth_device_start   — one-time interactive bootstrap. Returns user_code + URL.
 *   2. gh_auth_device_finish  — call once the user has approved at github.com/login/device.
 *   3. gh_open_pr             — declarative: { repo, base, branch, title, body, edits } -> PR url.
 *
 * gh_open_pr atomically: gets base ref → creates blobs → builds tree → creates commit → creates
 * branch ref → opens PR. Single commit, single round-trip from the caller.
 *
 * Token persists at $GH_PR_MCP_TOKEN_PATH (default ~/.gh-pr-mcp-token, mode 0600).
 * Client_id defaults to gh CLI's public OAuth App (178c6fc778ccc68e1d6a) — override via
 * $GH_DEVICE_CLIENT_ID to use your own GitHub OAuth App.
 *
 * Run:  npx tsx gh-pr-mcp.ts          # stdio transport for Claude Code / Claude Desktop
 *
 * Wire into Claude Code:
 *   claude mcp add gh-pr -- npx tsx /abs/path/to/gh-pr-mcp.ts
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { readFile, writeFile, chmod, mkdir } from "node:fs/promises";
import { homedir } from "node:os";
import { dirname } from "node:path";

const CLIENT_ID = process.env.GH_DEVICE_CLIENT_ID ?? "178c6fc778ccc68e1d6a";
const TOKEN_PATH = process.env.GH_PR_MCP_TOKEN_PATH ?? `${homedir()}/.gh-pr-mcp-token`;
const GH = "https://api.github.com";
const UA = "gh-pr-mcp/0.1";

// ───────────────────────── token persistence ─────────────────────────

const tokenStore = {
  async load(): Promise<string | null> {
    try { return (await readFile(TOKEN_PATH, "utf8")).trim() || null; }
    catch { return null; }
  },
  async save(token: string): Promise<void> {
    await mkdir(dirname(TOKEN_PATH), { recursive: true });
    await writeFile(TOKEN_PATH, token, "utf8");
    await chmod(TOKEN_PATH, 0o600);
  },
};

// In-memory device-flow state, keyed by user_code so the finish tool can find it.
const pendingDeviceCodes = new Map<string, { device_code: string; expires_at: number }>();

// ───────────────────────── tiny REST helper ─────────────────────────

async function gh(method: string, path: string, token: string, body?: unknown) {
  const r = await fetch(`${GH}${path}`, {
    method,
    headers: {
      "Authorization": `Bearer ${token}`,
      "Accept": "application/vnd.github+json",
      "X-GitHub-Api-Version": "2022-11-28",
      "User-Agent": UA,
      ...(body ? { "Content-Type": "application/json" } : {}),
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!r.ok) throw new Error(`${method} ${path} → ${r.status}: ${await r.text()}`);
  return r.json() as Promise<any>;
}

// ───────────────────────── the load-bearing primitive ─────────────────────────
//
// Atomically: base ref → blobs → tree → commit → branch ref → PR.
// One commit holds every edit; one PR points at it.
//
// edits[i].content is the FULL new file contents as UTF-8 text. To delete a file, omit it
// (the new tree only includes paths you pass).
//
async function openPr(args: {
  repo: string;       // "owner/name"
  base: string;       // default branch usually "main"
  branch: string;     // new branch name, e.g. "fix/typo"
  title: string;
  body: string;
  message: string;    // commit message
  edits: { path: string; content: string }[];
}) {
  const token = await tokenStore.load();
  if (!token) throw new Error("No token. Run gh_auth_device_start → gh_auth_device_finish first.");

  // 1. Resolve base ref → commit sha → tree sha
  const baseRef = await gh("GET", `/repos/${args.repo}/git/ref/heads/${args.base}`, token);
  const baseCommit = await gh("GET", `/repos/${args.repo}/git/commits/${baseRef.object.sha}`, token);

  // 2. Create one blob per edit. Use base64 to keep utf8-clean and binary-safe.
  const blobs = await Promise.all(args.edits.map(async (e) => {
    const blob = await gh("POST", `/repos/${args.repo}/git/blobs`, token, {
      content: Buffer.from(e.content, "utf8").toString("base64"),
      encoding: "base64",
    });
    return { path: e.path, mode: "100644" as const, type: "blob" as const, sha: blob.sha };
  }));

  // 3. New tree on top of base tree
  const tree = await gh("POST", `/repos/${args.repo}/git/trees`, token, {
    base_tree: baseCommit.tree.sha,
    tree: blobs,
  });

  // 4. New commit pointing at new tree, parented to base
  const commit = await gh("POST", `/repos/${args.repo}/git/commits`, token, {
    message: args.message,
    tree: tree.sha,
    parents: [baseRef.object.sha],
  });

  // 5. Create the branch ref
  await gh("POST", `/repos/${args.repo}/git/refs`, token, {
    ref: `refs/heads/${args.branch}`,
    sha: commit.sha,
  });

  // 6. Open the PR
  const pr = await gh("POST", `/repos/${args.repo}/pulls`, token, {
    title: args.title,
    body: args.body,
    head: args.branch,
    base: args.base,
  });

  return { url: pr.html_url, number: pr.number, commit: commit.sha };
}

// ───────────────────────── MCP wiring ─────────────────────────

const server = new Server(
  { name: "gh-pr-mcp", version: "0.1.0" },
  { capabilities: { tools: {} } },
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: "gh_auth_device_start",
      description:
        "Start a GitHub OAuth device-flow login. Returns a user_code the human enters at " +
        "github.com/login/device. Call gh_auth_device_finish with the same user_code once " +
        "they've approved. One-time setup; the token then persists across MCP server restarts.",
      inputSchema: {
        type: "object",
        properties: {
          scope: {
            type: "string",
            default: "repo",
            description: "OAuth scopes. 'repo' is enough to open PRs in private repos.",
          },
        },
      },
    },
    {
      name: "gh_auth_device_finish",
      description:
        "Complete the device flow started by gh_auth_device_start. Polls GitHub for the " +
        "access token once the user has approved at github.com/login/device. Stores the token " +
        "on disk at $GH_PR_MCP_TOKEN_PATH for reuse.",
      inputSchema: {
        type: "object",
        properties: { user_code: { type: "string", description: "The code returned by start." } },
        required: ["user_code"],
      },
    },
    {
      name: "gh_open_pr",
      description:
        "Open a pull request in one tool call. Bundles N file edits into a single commit on a " +
        "new branch, then opens the PR. Use ABSOLUTE file contents (not diffs) — the tool " +
        "writes whatever you pass as the entire new file body.",
      inputSchema: {
        type: "object",
        required: ["repo", "branch", "title", "body", "message", "edits"],
        properties: {
          repo:    { type: "string", description: "owner/name, e.g. opensubagents/opensubagents" },
          base:    { type: "string", default: "main", description: "Branch to PR against." },
          branch:  { type: "string", description: "New branch name to push the edits as." },
          title:   { type: "string" },
          body:    { type: "string", description: "PR description in Markdown." },
          message: { type: "string", description: "Commit message." },
          edits: {
            type: "array",
            minItems: 1,
            items: {
              type: "object",
              required: ["path", "content"],
              properties: {
                path:    { type: "string", description: "Path relative to repo root." },
                content: { type: "string", description: "Full new file body as UTF-8 text." },
              },
            },
          },
        },
      },
    },
  ],
}));

server.setRequestHandler(CallToolRequestSchema, async (req) => {
  const name = req.params.name;
  const args = (req.params.arguments ?? {}) as any;

  if (name === "gh_auth_device_start") {
    const r = await fetch("https://github.com/login/device/code", {
      method: "POST",
      headers: { "Accept": "application/json", "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({ client_id: CLIENT_ID, scope: args.scope ?? "repo" }),
    });
    if (!r.ok) throw new Error(`device/code → ${r.status}: ${await r.text()}`);
    const d = await r.json() as any;
    pendingDeviceCodes.set(d.user_code, {
      device_code: d.device_code,
      expires_at: Date.now() + d.expires_in * 1000,
    });
    return {
      content: [{
        type: "text",
        text: `Open ${d.verification_uri} and enter code: ${d.user_code}\n` +
              `Then call gh_auth_device_finish with user_code="${d.user_code}". ` +
              `Code expires in ${d.expires_in}s.`,
      }],
    };
  }

  if (name === "gh_auth_device_finish") {
    const state = pendingDeviceCodes.get(args.user_code);
    if (!state) throw new Error(`Unknown user_code. Call gh_auth_device_start first.`);
    if (Date.now() > state.expires_at) {
      pendingDeviceCodes.delete(args.user_code);
      throw new Error("Device code expired. Restart with gh_auth_device_start.");
    }
    // Poll up to 60 seconds, 5s interval (GitHub's recommended).
    for (let i = 0; i < 12; i++) {
      const r = await fetch("https://github.com/login/oauth/access_token", {
        method: "POST",
        headers: { "Accept": "application/json", "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams({
          client_id: CLIENT_ID,
          device_code: state.device_code,
          grant_type: "urn:ietf:params:oauth:grant-type:device_code",
        }),
      });
      const j = await r.json() as any;
      if (j.access_token) {
        await tokenStore.save(j.access_token);
        pendingDeviceCodes.delete(args.user_code);
        return { content: [{ type: "text", text: `Authorized. Token saved to ${TOKEN_PATH}.` }] };
      }
      if (j.error && j.error !== "authorization_pending" && j.error !== "slow_down") {
        throw new Error(`Device flow failed: ${j.error}${j.error_description ? ` — ${j.error_description}` : ""}`);
      }
      await new Promise((res) => setTimeout(res, 5_000));
    }
    throw new Error("Still pending after 60s. Approve at github.com/login/device, then call gh_auth_device_finish again.");
  }

  if (name === "gh_open_pr") {
    const result = await openPr({
      repo: args.repo,
      base: args.base ?? "main",
      branch: args.branch,
      title: args.title,
      body: args.body,
      message: args.message,
      edits: args.edits,
    });
    return {
      content: [{
        type: "text",
        text: `PR #${result.number}: ${result.url}\nCommit: ${result.commit}`,
      }],
    };
  }

  throw new Error(`Unknown tool: ${name}`);
});

await server.connect(new StdioServerTransport());
