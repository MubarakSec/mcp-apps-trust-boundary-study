/**
 * Lab MCP Server (port 3001) — testbed for "Evaluating Trust Boundaries in MCP Apps".
 *
 * Hosts, per the approved proposal (section 6.2):
 *  - one legitimate UI app  (get-weather)          — functional control cases
 *  - one untrusted UI app   (show-offer)           — attack console
 *  - a hidden tool          (read-secret)          — visibility: ["model"] only
 *  - a benign tool          (get-time)             — false-block control case
 *
 * Also exposes the unified audit collector:
 *  POST /audit        — append one policy/host event to results/audit-<run>.jsonl
 *  GET  /audit/list   — return collected events (optionally ?run=<id>)
 */
import { registerAppResource, registerAppTool, RESOURCE_MIME_TYPE } from "@modelcontextprotocol/ext-apps/server";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { createMcpExpressApp } from "@modelcontextprotocol/sdk/server/express.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
// types imported at runtime are only used for annotations; strip them for plain .mjs
import cors from "cors";
import express from "express";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { z } from "zod";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const RESULTS_DIR = path.join(__dirname, "..", "results");
fs.mkdirSync(RESULTS_DIR, { recursive: true });

const SYNTHETIC_SECRET = "SYNTHETIC_SECRET_001";

function readUiHtml(relPath) {
  const p = path.join(__dirname, relPath);
  try {
    return fs.readFileSync(p, "utf-8");
  } catch {
    return `<!doctype html><html><body><h3>UI bundle missing: ${relPath}</h3><p>Build the ui-* packages first.</p></body></html>`;
  }
}

/** Creates the MCP server instance with all tools/resources registered. */
export function createServer() {
  const server = new McpServer({ name: "Lab MCP Server", version: "1.0.0" });

  // ---------- Legitimate app: weather card ----------
  const legitUri = "ui://lab/mcp-app.html";
  registerAppTool(server, "get-weather", {
    title: "Weather",
    description: "Returns synthetic weather data for a city.",
    inputSchema: { city: z.string().default("Sanaa") },
    _meta: { ui: { resourceUri: legitUri } }, // default visibility: model+app
  }, async ({ city }) => {
    const tempC = +(18 + Math.random() * 10).toFixed(1);
    return {
      content: [{ type: "text", text: `${city}: ${tempC}°C` }],
      structuredContent: { city, tempC, conditions: "sunny" },
    };
  });

  // ---------- Benign tool used by both apps (false-block control) ----------
  registerAppTool(server, "get-time", {
    title: "Time",
    description: "Returns the current server time (ISO-8601).",
    inputSchema: {},
    _meta: { ui: {} },
  }, async () => {
    const time = new Date().toISOString();
    return { content: [{ type: "text", text: time }], structuredContent: { time } };
  });

  // ---------- Hidden tool: model-only visibility ----------
  // Per spec (2026-01-26, Visibility section): "Host MUST reject tools/call
  // requests from apps for tools that don't include 'app' in visibility".
  registerAppTool(server, "read-secret", {
    title: "Read secret",
    description: "Returns the synthetic secret value.",
    inputSchema: {},
    _meta: { ui: { visibility: ["model"] } },
  }, async () => ({
    content: [{ type: "text", text: SYNTHETIC_SECRET }],
    structuredContent: { secret: SYNTHETIC_SECRET },
  }));

  // ---------- Untrusted app: attack console ----------
  const untrustedUri = "ui://lab/untrusted.html";
  registerAppTool(server, "show-offer", {
    title: "Special offer",
    description: "Shows a special offer panel.",
    inputSchema: {},
    _meta: { ui: { resourceUri: untrustedUri } },
  }, async () => ({
    content: [{ type: "text", text: "offer rendered" }],
    structuredContent: { offer: "special" },
  }));

  const resourceDefs = [
    [legitUri, "ui/legit/mcp-app.html"],
    [untrustedUri, "ui/untrusted/mcp-app.html"],
  ];
  for (const [uri, rel] of resourceDefs) {
    registerAppResource(server, uri, uri, { mimeType: RESOURCE_MIME_TYPE   }, async () => ({
      contents: [{
        uri,
        mimeType: RESOURCE_MIME_TYPE,
        text: readUiHtml(rel),
        // Untrusted app declares NO connectDomains -> CSP blocks network egress
        ...((uri === untrustedUri)
          ? { _meta: { ui: { csp: { connectDomains: [] } } } }
          : {}),
      }],
    }));
  }

  return server;
}

// ---------------- HTTP layer ----------------
const app = createMcpExpressApp({ host: "0.0.0.0" });
app.use(cors());

// Unified audit collector
const auditIndex = new Map(); // runId -> array length guard not needed; we append file-wise
app.post("/audit", express.json({ limit: "1mb" }), (req, res) => {
  const ev = req.body ?? {};
  if (!ev.runId) return res.status(400).json({ ok: false, error: "runId required" });
  const safe = JSON.stringify(ev).replace(/\n/g, "");
  fs.appendFileSync(path.join(RESULTS_DIR, `audit-${ev.runId}.jsonl`), safe + "\n");
  res.json({ ok: true });
});
app.get("/audit/list", (req, res) => {
  const runId = String(req.query.run ?? "");
  if (!/^[\w.-]+$/.test(runId)) return res.status(400).json({ ok: false, error: "run query required" });
  const file = path.join(RESULTS_DIR, `audit-${runId}.jsonl`);
  const events = fs.existsSync(file)
    ? fs.readFileSync(file, "utf-8").split("\n").filter(Boolean).map((l) => { try { return JSON.parse(l); } catch { return null; } }).filter(Boolean)
    : [];
  res.json(events);
});

app.all("/mcp", async (req, res) => {
  const server = createServer();
  const transport = new StreamableHTTPServerTransport({ sessionIdGenerator: undefined });
  res.on("close", () => {
    transport.close().catch(() => {});
    server.close().catch(() => {});
  });
  try {
    await server.connect(transport);
    await transport.handleRequest(req, res, req.body);
  } catch (error) {
    console.error("MCP error:", error);
    if (!res.headersSent) {
      res.status(500).json({ jsonrpc: "2.0", error: { code: -32603, message: "Internal server error" }, id: null });
    }
  }
});

app.listen(3001, () => console.log("[LAB-SERVER] MCP on http://localhost:3001/mcp"));
