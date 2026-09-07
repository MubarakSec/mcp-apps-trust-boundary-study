import { Component, type ErrorInfo, type ReactNode, StrictMode, Suspense, use, useEffect, useMemo, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import { getToolUiResourceUri, McpUiToolMetaSchema } from "@modelcontextprotocol/ext-apps/app-bridge";
import type { Tool } from "@modelcontextprotocol/sdk/types.js";
import {
  callTool, connectToServer, hasAppHtml, initializeApp,
  loadSandboxProxy, log, newAppBridge, wrapOnCallTool,
  type ServerInfo, type ToolCallInfo, type ModelContext, type AppMessage,
  POLICY_CFG,
} from "./implementation";
import { resolveConsent } from "./policy-layer";
import { getTheme, toggleTheme, onThemeChange, type Theme } from "./theme";
import styles from "./index.module.css";

// ─── Source Badge (§6.3 rule 3: visible trust-boundary marker) ──────────

function SourceBadge() {
  if (!POLICY_CFG.enabled) return null;
  return (
    <div data-testid="source-badge" style={{
      background: "#fff3cd", border: "1px solid #ffc107", borderRadius: 4,
      padding: "6px 10px", fontSize: 12, color: "#856404", fontFamily: "sans-serif",
      marginBottom: 6, display: "flex", alignItems: "center", gap: 6,
    }}>
      <span style={{ fontSize: 18 }}>⚠</span>
      <span>
        <strong>Confidential UI.</strong> Rendered by an external MCP server.
        Proceed with caution.
      </span>
    </div>
  );
}

// ─── Consent Modal (shown when autoconsent is null) ─────────────────────

function ConsentModal() {
  const [detail, setDetail] = useState<{ id: string; channel: string; params: unknown } | null>(null);

  useEffect(() => {
    const handler = (e: Event) => {
      const d = (e as CustomEvent).detail;
      if (d?.id) setDetail(d);
    };
    window.addEventListener("policy:consent-request", handler as EventListener);
    return () => window.removeEventListener("policy:consent-request", handler as EventListener);
  }, []);

  if (!detail) return null;

  const decide = (allow: boolean) => {
    resolveConsent(detail.id, allow);
    setDetail(null);
  };

  const paramsPreview = JSON.stringify(detail.params ?? {}).slice(0, 200);

  return (
    <div data-testid="consent-modal" style={{
      position: "fixed", top: 0, left: 0, right: 0, bottom: 0,
      background: "rgba(0,0,0,0.5)", display: "flex", alignItems: "center",
      justifyContent: "center", zIndex: 99999,
    }}>
      <div style={{
        background: "#fff", borderRadius: 8, padding: 20, minWidth: 360,
        maxWidth: 480, boxShadow: "0 4px 24px rgba(0,0,0,0.2)",
      }}>
        <h3 style={{ margin: "0 0 10px", fontSize: 16 }}>🔒 Policy Consent Required</h3>
        <div style={{ fontSize: 13, marginBottom: 6 }}>
          <strong>Channel:</strong> {detail.channel}
        </div>
        <pre style={{
          fontSize: 11, background: "#f5f5f5", padding: 8, borderRadius: 4,
          maxHeight: 120, overflow: "auto", margin: "0 0 12px", whiteSpace: "pre-wrap",
        }}>{paramsPreview}</pre>
        <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}>
          <button data-testid="consent-deny" onClick={() => decide(false)}
                  style={{ padding: "6px 16px", borderRadius: 4, border: "1px solid #ccc", background: "#f5f5f5", cursor: "pointer" }}>
            Deny
          </button>
          <button data-testid="consent-allow" onClick={() => decide(true)}
                  style={{ padding: "6px 16px", borderRadius: 4, border: "none", background: "#2ecc71", color: "#fff", cursor: "pointer" }}>
            Allow
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── Test Status Panel (shows untrusted app status in host page) ────────

function TestStatusPanel({ policyEnabled }: { policyEnabled: boolean }) {
  const [status, setStatus] = useState("Ready");
  const [pendingId, setPendingId] = useState<string | null>(null);

  useEffect(() => {
    const handler = (e: Event) => {
      const detail = (e as CustomEvent).detail;
      if (detail?.channel) {
        setPendingId(detail.id);
        setStatus(`⏳ ${detail.channel} — user decision needed`);
      }
    };
    window.addEventListener("policy:consent-request", handler as EventListener);
    return () => window.removeEventListener("policy:consent-request", handler as EventListener);
  }, []);

  const handleConsent = (allow: boolean) => {
    if (!pendingId) return;
    resolveConsent(pendingId, allow);
    setStatus(allow ? "✅ User approved" : "❌ User denied");
    setPendingId(null);
  };

  const runAction = async (btnId: string) => {
    setStatus("⏳ waiting…");
    try {
      const outerFrame = document.querySelector("iframe") as HTMLIFrameElement | null;
      const innerFrame = outerFrame?.contentDocument?.querySelector("iframe") as HTMLIFrameElement | null;
      const btn = innerFrame?.contentDocument?.querySelector(`[data-testid="${btnId}"]`) as HTMLButtonElement | null;
      if (btn) { btn.click(); setStatus("clicked"); }
      else     { setStatus(`button ${btnId} not found`); }
    } catch (e: any) {
      setStatus(`error: ${String(e).slice(0, 120)}`);
    }
  };

  if (!policyEnabled) return null;

  return (
    <div data-testid="test-panel" style={{
      position: "fixed", bottom: 8, left: 8, zIndex: 99998,
      background: "#1a1a2e", color: "#0f0", fontFamily: "monospace", fontSize: 12,
      padding: 12, borderRadius: 6, minWidth: 320, border: "1px solid #333",
    }}>
      <div style={{ marginBottom: 6, fontWeight: "bold" }}>🔬 Policy Test Panel</div>
      <div style={{ marginBottom: 6 }}><strong>Status:</strong> <span data-testid="policy-status">{status}</span></div>
      {pendingId && (
        <div style={{ marginBottom: 6, display: "flex", gap: 6 }}>
          <button onClick={() => handleConsent(true)}
                  style={{ background: "#2ecc71", border: "none", color: "#fff", padding: "4px 10px", borderRadius: 4, cursor: "pointer" }}
                  data-testid="test-allow">✅ Allow</button>
          <button onClick={() => handleConsent(false)}
                  style={{ background: "#e74c3c", border: "none", color: "#fff", padding: "4px 10px", borderRadius: 4, cursor: "pointer" }}
                  data-testid="test-deny">❌ Deny</button>
        </div>
      )}
      <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
        {["btn-fetch","btn-link","btn-msg","btn-ctx","btn-read","btn-time"].map(id => (
          <button key={id} onClick={() => runAction(id)}
                  style={{ background: "#34495e", border: "1px solid #555", color: "#fff", padding: "2px 8px", borderRadius: 3, cursor: "pointer", fontSize: 11 }}>
            {id}
          </button>
        ))}
      </div>
    </div>
  );
}


// ─── Helpers ────────────────────────────────────────────────────────────

function isToolVisibleToModel(tool: { _meta?: Record<string, unknown> }): boolean {
  const result = McpUiToolMetaSchema.safeParse(tool._meta?.ui);
  if (!result.success) return true;
  const visibility = result.data.visibility;
  if (!visibility) return true;
  return visibility.includes("model");
}

function compareTools(a: Tool, b: Tool): number {
  const aHasUi = !!getToolUiResourceUri(a);
  const bHasUi = !!getToolUiResourceUri(b);
  if (aHasUi && !bHasUi) return -1;
  if (!aHasUi && bHasUi) return 1;
  return a.name.localeCompare(b.name);
}

function getToolDefaults(tool: Tool | undefined): string {
  if (!tool?.inputSchema?.properties) return "{}";
  const defaults: Record<string, unknown> = {};
  for (const [key, prop] of Object.entries(tool.inputSchema.properties)) {
    if (prop && typeof prop === "object" && "default" in prop) defaults[key] = (prop as any).default;
  }
  return Object.keys(defaults).length > 0 ? JSON.stringify(defaults, null, 2) : "{}";
}


// ─── Host ───────────────────────────────────────────────────────────────

interface HostProps { serversPromise: Promise<ServerInfo[]>; }
type ToolCallEntry = ToolCallInfo & { id: number };
let nextToolCallId = 0;

function getQueryParams() {
  const params = new URLSearchParams(window.location.search);
  return {
    server: params.get("server"),
    tool: params.get("tool"),
    call: params.get("call") === "true",
    hideThemeToggle: params.get("theme") === "hide",
  };
}

function ThemeToggle() {
  const [theme, setTheme] = useState<Theme>(getTheme);
  useEffect(() => onThemeChange(setTheme), []);
  return (
    <button className={styles.themeToggle} onClick={() => toggleTheme()}
            title={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}>
      {theme === "dark" ? "☀️" : "🌙"}
    </button>
  );
}

function Host({ serversPromise }: HostProps) {
  const [toolCalls, setToolCalls] = useState<ToolCallEntry[]>([]);
  const [destroyingIds, setDestroyingIds] = useState<Set<number>>(new Set());
  const queryParams = useMemo(() => getQueryParams(), []);
  const requestClose = (id: number) => setDestroyingIds(s => new Set(s).add(id));
  const completeClose = (id: number) => {
    setDestroyingIds(s => { const next = new Set(s); next.delete(id); return next; });
    setToolCalls(calls => calls.filter(c => c.id !== id));
  };

  return (
    <>
      {!queryParams.hideThemeToggle && <ThemeToggle />}
      <ConsentModal />
      <SourceBadge />
      {toolCalls.map(info => (
        <ToolCallInfoPanel key={info.id} toolCallInfo={info}
                           isDestroying={destroyingIds.has(info.id)}
                           onRequestClose={() => requestClose(info.id)}
                           onCloseComplete={() => completeClose(info.id)} />
      ))}
      <CallToolPanel serversPromise={serversPromise}
                     addToolCall={info => setToolCalls([...toolCalls, { ...info, id: nextToolCallId++ }])}
                     initialServer={queryParams.server}
                     initialTool={queryParams.tool}
                     autoCall={queryParams.call} />
      <TestStatusPanel policyEnabled={POLICY_CFG.enabled} />
    </>
  );
}


// ─── CallToolPanel ──────────────────────────────────────────────────────

interface CallToolPanelProps {
  serversPromise: Promise<ServerInfo[]>;
  addToolCall: (info: ToolCallInfo) => void;
  initialServer?: string | null;
  initialTool?: string | null;
  autoCall?: boolean;
}

function CallToolPanel({ serversPromise, addToolCall, initialServer, initialTool, autoCall }: CallToolPanelProps) {
  const [selectedServer, setSelectedServer] = useState<ServerInfo | null>(null);
  const [selectedTool, setSelectedTool] = useState("");
  const [inputJson, setInputJson] = useState("{}");
  const [hasAutoCalledRef] = useState({ called: false });
  const toolNames = selectedServer
    ? Array.from(selectedServer.tools.values()).filter(t => isToolVisibleToModel(t)).sort(compareTools).map(t => t.name)
    : [];
  const isValidJson = useMemo(() => { try { JSON.parse(inputJson); return true; } catch { return false; } }, [inputJson]);

  const handleServerSelect = (server: ServerInfo, preferredTool?: string) => {
    setSelectedServer(server);
    const vt = Array.from(server.tools.values()).filter(t => isToolVisibleToModel(t)).sort(compareTools);
    const tt = preferredTool && vt.some(t => t.name === preferredTool) ? preferredTool : vt[0]?.name ?? "";
    setSelectedTool(tt);
    setInputJson(getToolDefaults(server.tools.get(tt)));
  };
  const handleToolSelect = (toolName: string) => { setSelectedTool(toolName); setInputJson(getToolDefaults(selectedServer?.tools.get(toolName))); };
  const handleSubmit = (overrideServer?: ServerInfo, overrideTool?: string) => {
    const server = overrideServer ?? selectedServer;
    const tool = overrideTool ?? selectedTool;
    if (!server) return;
    addToolCall(callTool(server, tool, JSON.parse(inputJson)));
    const url = new URL(window.location.href);
    url.searchParams.set("server", server.name);
    url.searchParams.set("tool", tool);
    url.searchParams.set("call", "true");
    history.replaceState(null, "", url.toString());
  };

  return (
    <div className={styles.callToolPanel}>
      <form onSubmit={e => { e.preventDefault(); handleSubmit(); }}>
        <label>Server
          <Suspense fallback={<select disabled><option>Loading...</option></select>}>
            <ServerSelect serversPromise={serversPromise} onSelect={handleServerSelect}
                          initialServer={initialServer} initialTool={initialTool}
                          autoCall={autoCall && !hasAutoCalledRef.called}
                          onAutoCall={(s, t) => { hasAutoCalledRef.called = true; handleSubmit(s, t); }} />
          </Suspense>
        </label>
        <label>Tool
          <select className={styles.toolSelect} value={selectedTool} onChange={e => handleToolSelect(e.target.value)}>
            {selectedServer && toolNames.map(n => <option key={n} value={n}>{n}</option>)}
          </select>
        </label>
        <label>Input
          <textarea className={styles.toolInput} aria-invalid={!isValidJson} value={inputJson} onChange={e => setInputJson(e.target.value)} />
        </label>
        <button type="submit" disabled={!selectedTool || !isValidJson}>Call Tool</button>
      </form>
    </div>
  );
}

interface ServerSelectProps {
  serversPromise: Promise<ServerInfo[]>; onSelect: (server: ServerInfo, toolName?: string) => void;
  initialServer?: string | null; initialTool?: string | null;
  autoCall?: boolean; onAutoCall?: (server: ServerInfo, tool: string) => void;
}

function ServerSelect({ serversPromise, onSelect, initialServer, initialTool, autoCall, onAutoCall }: ServerSelectProps) {
  const servers = use(serversPromise);
  const [hasInitialized, setHasInitialized] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(0);
  useEffect(() => {
    if (hasInitialized || servers.length === 0) return;
    let idx = 0;
    if (initialServer) { const fi = servers.findIndex(s => s.name === initialServer); if (fi >= 0) idx = fi; }
    const server = servers[idx]; setSelectedIndex(idx);
    const vt = Array.from(server.tools.values()).filter(t => isToolVisibleToModel(t)).sort(compareTools);
    const tt = initialTool && vt.some(t => t.name === initialTool) ? initialTool : vt[0]?.name ?? "";
    onSelect(server, tt); setHasInitialized(true);
    if (autoCall && tt) onAutoCall?.(server, tt);
  }, [servers, hasInitialized, initialServer, initialTool, autoCall, onSelect, onAutoCall]);
  if (servers.length === 0) return <select disabled><option>No servers configured</option></select>;
  return (
    <select value={selectedIndex} onChange={e => { const i = Number(e.target.value); setSelectedIndex(i); onSelect(servers[i]); }}>
      {servers.map((s, i) => <option key={i} value={i}>{s.name}</option>)}
    </select>
  );
}


// ─── ToolCallInfoPanel ──────────────────────────────────────────────────

interface ToolCallInfoPanelProps { toolCallInfo: ToolCallInfo; isDestroying?: boolean; onRequestClose?: () => void; onCloseComplete?: () => void; }

function ToolCallInfoPanel({ toolCallInfo, isDestroying, onRequestClose, onCloseComplete }: ToolCallInfoPanelProps) {
  const isApp = hasAppHtml(toolCallInfo);
  useEffect(() => { if (isDestroying && !isApp) onCloseComplete?.(); }, [isDestroying, isApp, onCloseComplete]);
  return (
    <div className={styles.toolCallInfoPanel} style={isDestroying ? { opacity: 0.5, pointerEvents: "none" } : undefined}>
      <div className={styles.appHeader}>
        <span>{toolCallInfo.serverInfo.name}:<span className={styles.toolName}>{toolCallInfo.tool.name}</span></span>
        {onRequestClose && !isDestroying && <button className={styles.closeButton} onClick={onRequestClose} title="Close">×</button>}
      </div>
      <CollapsiblePanel icon="📥" label="Tool Input" content={JSON.stringify(toolCallInfo.input, null, 2)} />
      {isApp && <ErrorBoundary><Suspense fallback="Loading..."><AppIFramePanel toolCallInfo={toolCallInfo as Required<ToolCallInfo>} isDestroying={isDestroying} onTeardownComplete={onCloseComplete} /></Suspense></ErrorBoundary>}
      <ErrorBoundary><Suspense fallback="Loading result..."><ToolResultPanel toolCallInfo={toolCallInfo} /></Suspense></ErrorBoundary>
    </div>
  );
}


// ─── CollapsiblePanel ───────────────────────────────────────────────────

interface CollapsiblePanelProps { icon: string; label: string; content: string; badge?: string; defaultExpanded?: boolean; }
function CollapsiblePanel({ icon, label, content, badge, defaultExpanded = false }: CollapsiblePanelProps) {
  const [expanded, setExpanded] = useState(defaultExpanded);
  return (
    <div className={styles.collapsiblePanel} onClick={() => setExpanded(!expanded)} title={expanded ? "Click to collapse" : "Click to expand"}>
      <div className={styles.collapsibleHeader}>
        <span className={styles.collapsibleLabel}>{icon} {label}</span>
        <span className={styles.collapsibleSize}>{badge ?? `${content.length} chars`}</span>
        <span className={styles.collapsibleToggle}>{expanded ? "▼" : "▶"}</span>
      </div>
      {expanded ? <pre className={styles.collapsibleFull}>{content}</pre> : <div className={styles.collapsiblePreview}>{content.slice(0, 100)}{content.length > 100 ? "…" : ""}</div>}
    </div>
  );
}


// ─── AppIFramePanel ─────────────────────────────────────────────────────

interface AppIFramePanelProps { toolCallInfo: Required<ToolCallInfo>; isDestroying?: boolean; onTeardownComplete?: () => void; }

function AppIFramePanel({ toolCallInfo, isDestroying, onTeardownComplete }: AppIFramePanelProps) {
  const iframeRef = useRef<HTMLIFrameElement | null>(null);
  const appBridgeRef = useRef<ReturnType<typeof newAppBridge> | null>(null);
  const [modelContext, setModelContext] = useState<ModelContext | null>(null);
  const [messages, setMessages] = useState<AppMessage[]>([]);
  const [displayMode, setDisplayMode] = useState<"inline" | "fullscreen">("inline");

  useEffect(() => {
    const iframe = iframeRef.current!;
    toolCallInfo.appResourcePromise.then(({ csp, permissions }) => {
      loadSandboxProxy(iframe, csp, permissions).then((firstTime) => {
        if (firstTime) {
          const appBridge = newAppBridge(toolCallInfo.serverInfo, iframe, {
            onContextUpdate: setModelContext,
            onMessage: (msg) => setMessages(prev => [...prev, msg]),
            onDisplayModeChange: setDisplayMode,
          }, { containerDimensions: { maxHeight: 6000 }, displayMode: "inline" });
          appBridgeRef.current = appBridge;
          initializeApp(iframe, appBridge, toolCallInfo).then(() => {
            wrapOnCallTool(appBridge, toolCallInfo.serverInfo);
          });
        }
      });
    });
  }, [toolCallInfo]);

  useEffect(() => {
    if (!isDestroying) return;
    if (!appBridgeRef.current) { onTeardownComplete?.(); return; }
    appBridgeRef.current.teardownResource({}).catch(() => {}).finally(() => { onTeardownComplete?.(); });
  }, [isDestroying, onTeardownComplete]);

  const fmt = (c: { type: string; [key: string]: unknown }) => {
    switch (c.type) {
      case "text": return (c as any).text;
      case "image": return `<image: ${(c as any).mimeType ?? "unknown"}>`;
      default: return `<${c.type}>`;
    }
  };
  const contextText = modelContext?.content?.map(fmt).join("\n") ?? "";
  const contextJson = modelContext?.structuredContent ? JSON.stringify(modelContext.structuredContent, null, 2) : "";
  const fullContext = [contextText, contextJson].filter(Boolean).join("\n\n");
  const messagesText = messages.map(m => `[${m.role}] ${m.content.map(fmt).join("\n")}`).join("\n\n");
  const panelCls = displayMode === "fullscreen" ? `${styles.appIframePanel} ${styles.fullscreen}` : styles.appIframePanel;

  return (
    <div className={panelCls}>
      <iframe ref={iframeRef} />
      {messages.length > 0 && <CollapsiblePanel icon="💬" label="Messages" content={messagesText} badge={`${messages.length} message${messages.length > 1 ? "s" : ""}`} />}
      {modelContext && <CollapsiblePanel icon="📋" label="Model Context" content={fullContext} />}
    </div>
  );
}


// ─── ToolResultPanel ────────────────────────────────────────────────────

function ToolResultPanel({ toolCallInfo }: { toolCallInfo: ToolCallInfo }) {
  const result = use(toolCallInfo.resultPromise);
  return <CollapsiblePanel icon="📤" label="Tool Result" content={JSON.stringify(result, null, 2)} />;
}


// ─── ErrorBoundary ──────────────────────────────────────────────────────

class ErrorBoundary extends Component<{ children: ReactNode }, { hasError: boolean; error: unknown }> {
  state = { hasError: false, error: undefined as unknown };
  static getDerivedStateFromError(error: unknown) { return { hasError: true, error }; }
  componentDidCatch(error: unknown, errorInfo: ErrorInfo) { log.error("Caught:", error, errorInfo.componentStack); }
  render() { return this.state.hasError ? <div className={styles.error}><strong>ERROR:</strong> {String(this.state.error)}</div> : this.props.children; }
}


// ─── Mount ──────────────────────────────────────────────────────────────

async function connectToAllServers(): Promise<ServerInfo[]> {
  const res = await fetch("/api/servers");
  const urls = (await res.json()) as string[];
  const results = await Promise.allSettled(urls.map(u => connectToServer(new URL(u))));
  const servers: ServerInfo[] = [];
  for (const r of results) if (r.status === "fulfilled") servers.push(r.value);
  if (servers.length === 0 && urls.length > 0) throw new Error(`Failed to connect to any servers (${urls.length} attempted)`);
  return servers;
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <ErrorBoundary>
      <Host serversPromise={connectToAllServers()} />
    </ErrorBoundary>
  </StrictMode>,
);
