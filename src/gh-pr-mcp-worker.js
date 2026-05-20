// gh-pr-mcp-worker.js — Cloudflare Worker exposing gh-pr-mcp tools over MCP Streamable HTTP.
// Stateless: caller passes a GitHub bearer token per tool call (or set as Worker secret GH_TOKEN).
// Endpoint: POST / with a JSON-RPC body; supports initialize, tools/list, tools/call.

const TOOLS = [
  {
    name: "gh_open_pr",
    description:
      "Atomically open a GitHub PR: get base ref → create blobs → tree → commit → branch ref → POST /pulls. " +
      "All edits commit together so the validator sees a complete tree.",
    inputSchema: {
      type: "object",
      properties: {
        token: { type: "string", description: "GitHub bearer token with repo scope (omit to use Worker secret GH_TOKEN)" },
        repo: { type: "string", description: "owner/repo, e.g. opensubagents/opensubagents" },
        base: { type: "string", description: "base branch (e.g. main)", default: "main" },
        branch: { type: "string", description: "new branch name" },
        title: { type: "string" },
        body: { type: "string", default: "" },
        message: { type: "string", description: "commit message" },
        edits: {
          type: "array",
          description: "list of {path, content} pairs",
          items: {
            type: "object",
            properties: { path: { type: "string" }, content: { type: "string" } },
            required: ["path", "content"],
          },
        },
      },
      required: ["repo", "branch", "title", "message", "edits"],
    },
  },
];

async function gh(token, method, path, body) {
  const r = await fetch(`https://api.github.com${path}`, {
    method,
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: "application/vnd.github+json",
      "User-Agent": "gh-pr-mcp-worker/0.1.0",
      "Content-Type": "application/json",
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  const text = await r.text();
  let data;
  try { data = JSON.parse(text); } catch { data = text; }
  if (!r.ok) throw new Error(`gh ${method} ${path}: ${r.status} ${text}`);
  return data;
}

async function openPr(args, env) {
  const token = args.token || env.GH_TOKEN;
  if (!token) throw new Error("no token: pass {token: '...'} or set Worker secret GH_TOKEN");
  const { repo, branch, title, message, edits } = args;
  const base = args.base || "main";
  const body = args.body || "";

  const baseRef = await gh(token, "GET", `/repos/${repo}/git/ref/heads/${base}`);
  const baseSha = baseRef.object.sha;
  const baseCommit = await gh(token, "GET", `/repos/${repo}/git/commits/${baseSha}`);
  const baseTreeSha = baseCommit.tree.sha;

  const treeEntries = [];
  for (const e of edits) {
    const blob = await gh(token, "POST", `/repos/${repo}/git/blobs`, { content: e.content, encoding: "utf-8" });
    treeEntries.push({ path: e.path, mode: "100644", type: "blob", sha: blob.sha });
  }
  const tree = await gh(token, "POST", `/repos/${repo}/git/trees`, { base_tree: baseTreeSha, tree: treeEntries });
  const commit = await gh(token, "POST", `/repos/${repo}/git/commits`, { message, tree: tree.sha, parents: [baseSha] });
  await gh(token, "POST", `/repos/${repo}/git/refs`, { ref: `refs/heads/${branch}`, sha: commit.sha });
  const pr = await gh(token, "POST", `/repos/${repo}/pulls`, { title, body, head: branch, base });

  return { url: pr.html_url, number: pr.number, branch, commit_sha: commit.sha };
}

function jrpc(id, payload) {
  return new Response(JSON.stringify({ jsonrpc: "2.0", id, ...payload }), {
    headers: { "Content-Type": "application/json" },
  });
}

export default {
  async fetch(request, env) {
    if (request.method === "GET") {
      return new Response(
        "gh-pr-mcp-worker — POST JSON-RPC to /. Methods: initialize, tools/list, tools/call.\n",
        { headers: { "Content-Type": "text/plain" } }
      );
    }
    if (request.method !== "POST") return new Response("405", { status: 405 });
    let body;
    try { body = await request.json(); } catch { return jrpc(null, { error: { code: -32700, message: "parse error" } }); }
    const { method, params, id } = body;

    if (method === "initialize") {
      return jrpc(id, {
        result: {
          protocolVersion: "2024-11-05",
          serverInfo: { name: "gh-pr-mcp", version: "0.1.0" },
          capabilities: { tools: {} },
        },
      });
    }
    if (method === "tools/list") return jrpc(id, { result: { tools: TOOLS } });
    if (method === "tools/call") {
      const { name, arguments: args } = params || {};
      try {
        if (name === "gh_open_pr") {
          const result = await openPr(args || {}, env || {});
          return jrpc(id, { result: { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] } });
        }
        return jrpc(id, { error: { code: -32601, message: `unknown tool: ${name}` } });
      } catch (err) {
        return jrpc(id, { error: { code: -32000, message: String(err && err.message || err) } });
      }
    }
    return jrpc(id, { error: { code: -32601, message: `unknown method: ${method}` } });
  },
};
