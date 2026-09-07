import { RESOURCE_MIME_TYPE, getToolUiResourceUri, type McpUiSandboxProxyReadyNotification, AppBridge, PostMessageTransport, type McpUiResourceCsp, type McpUiResourcePermissions, buildAllowAttribute, type McpUiUpdateModelContextRequest, type McpUiMessageRequest } from "@modelcontextprotocol/ext-apps/app-bridge";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { SSEClientTransport } from "@modelcontextprotocol/sdk/client/sse.js";
import { StreamableHTTPClientTransport } from "@modelcontextprotocol/sdk/client/streamableHttp.js";
import type { CallToolResult, Resource, Tool } from "@modelcontextprotocol/sdk/types.js";
import { getTheme, onThemeChange } from "./theme";
import { HOST_STYLE_VARIABLES } from "./host-styles";
import { loadPolicy, gateOpenLink, gateMessage, gateContext, gateToolVisibility, audit, setServerToolsForGate, type PolicyConfig } from "./policy-layer";

const SANDBOX_PROXY_BASE_URL = "http://localhost:8091/sandbox.html";
const IMPLEMENTATION = { name: "MCP Apps Host", version: "1.0.0" };

/** Read once at page load from URL search params (?policy=on&autoconsent=allow|deny&run=<id>) */
export const POLICY_CFG: PolicyConfig = loadPolicy();

export const log = {
  info: console.log.bind(console, "[HOST]"),
  warn: console.warn.bind(console, "[HOST]"),
  error: console.error.bind(console, "[HOST]"),
};

export interface ServerInfo {
  name: string;
  client: Client;
  tools: Map<string, Tool>;
  resources: Map<string, Resource>;
  appHtmlCache: Map<string, string>;
}

export async function connectToServer(serverUrl: URL): Promise<ServerInfo> {
  log.info("Connecting to server:", serverUrl.href);
  const client = await connectWithFallback(serverUrl);
  const name = client.getServerVersion()?.name ?? serverUrl.href;
  const toolsList = await client.listTools();
  const tools = new Map(toolsList.tools.map((tool) => [tool.name, tool]));
  log.info("Server tools:", Array.from(tools.keys()));
  const resourcesList = await client.listResources();
  const resources = new Map(resourcesList.resources.map((r) => [r.uri, r]));
  log.info("Server resources:", Array.from(resources.keys()));

  // Export tools metadata for policy tool-visibility gate
  setServerToolsForGate(tools as Map<string, { _meta?: Record<string, unknown> }>);

  return { name, client, tools, resources, appHtmlCache: new Map() };
}

async function connectWithFallback(serverUrl: URL): Promise<Client> {
  try {
    const client = new Client(IMPLEMENTATION);
    await client.connect(new StreamableHTTPClientTransport(serverUrl));
    log.info("Connected via Streamable HTTP transport");
    return client;
  } catch (streamableError) {
    log.info("Streamable HTTP failed:", streamableError);
  }
  try {
    const client = new Client(IMPLEMENTATION);
    await client.connect(new SSEClientTransport(serverUrl));
    log.info("Connected via SSE transport");
    return client;
  } catch (sseError) {
    throw new Error(`Could not connect with any transport. SSE error: ${sseError}`);
  }
}

interface UiResourceData {
  html: string;
  csp?: McpUiResourceCsp;
  permissions?: McpUiResourcePermissions;
}

export interface ToolCallInfo {
  serverInfo: ServerInfo;
  tool: Tool;
  input: Record<string, unknown>;
  resultPromise: Promise<CallToolResult>;
  appResourcePromise?: Promise<UiResourceData>;
}

export function hasAppHtml(toolCallInfo: ToolCallInfo): toolCallInfo is Required<ToolCallInfo> {
  return !!toolCallInfo.appResourcePromise;
}

export function callTool(
  serverInfo: ServerInfo,
  name: string,
  input: Record<string, unknown>,
): ToolCallInfo {
  log.info("Calling tool", name, "with input", input);
  const resultPromise = serverInfo.client.callTool({ name, arguments: input }) as Promise<CallToolResult>;
  const tool = serverInfo.tools.get(name);
  if (!tool) throw new Error(`Unknown tool: ${name}`);
  const toolCallInfo: ToolCallInfo = { serverInfo, tool, input, resultPromise };
  const uiResourceUri = getToolUiResourceUri(tool);
  if (uiResourceUri) {
    toolCallInfo.appResourcePromise = getUiResource(serverInfo, uiResourceUri);
  }
  return toolCallInfo;
}

async function getUiResource(serverInfo: ServerInfo, uri: string): Promise<UiResourceData> {
  log.info("Reading UI resource:", uri);
  const resource = await serverInfo.client.readResource({ uri });
  if (!resource) throw new Error(`Resource not found: ${uri}`);
  if (resource.contents.length !== 1) throw new Error(`Unexpected contents count: ${resource.contents.length}`);
  const content = resource.contents[0];
  if (content.mimeType !== RESOURCE_MIME_TYPE) throw new Error(`Unsupported MIME type: ${content.mimeType}`);
  const html = "blob" in content ? atob(content.blob) : content.text;
  const contentMeta = (content as any)._meta || (content as any).meta;
  const listingResource = serverInfo.resources.get(uri);
  const listingMeta = (listingResource as any)?._meta;
  const uiMeta = contentMeta?.ui ?? listingMeta?.ui;
  return { html, csp: uiMeta?.csp, permissions: uiMeta?.permissions };
}

export function loadSandboxProxy(
  iframe: HTMLIFrameElement,
  csp?: McpUiResourceCsp,
  permissions?: McpUiResourcePermissions,
): Promise<boolean> {
  if (iframe.src) return Promise.resolve(false);
  iframe.setAttribute("sandbox", "allow-scripts allow-same-origin allow-forms");
  const allowAttribute = buildAllowAttribute(permissions);
  if (allowAttribute) iframe.setAttribute("allow", allowAttribute);
  const readyNotification: McpUiSandboxProxyReadyNotification["method"] =
    "ui/notifications/sandbox-proxy-ready";
  const readyPromise = new Promise<boolean>((resolve) => {
    const listener = ({ source, data }: MessageEvent) => {
      if (source === iframe.contentWindow && data?.method === readyNotification) {
        log.info("Sandbox proxy loaded")
        window.removeEventListener("message", listener);
        resolve(true);
      }
    };
    window.addEventListener("message", listener);
  });
  const sandboxUrl = new URL(SANDBOX_PROXY_BASE_URL);
  if (csp) sandboxUrl.searchParams.set("csp", JSON.stringify(csp));
  log.info("Loading sandbox proxy...", csp ? `(CSP: ${JSON.stringify(csp)})` : "");
  iframe.src = sandboxUrl.href;
  return readyPromise;
}

export async function initializeApp(
  iframe: HTMLIFrameElement,
  appBridge: AppBridge,
  { input, resultPromise, appResourcePromise }: Required<ToolCallInfo>,
): Promise<void> {
  const appInitializedPromise = hookInitializedCallback(appBridge);
  await appBridge.connect(
    new PostMessageTransport(iframe.contentWindow!, iframe.contentWindow!),
  );
  const { html, csp, permissions } = await appResourcePromise;
  await appBridge.sendSandboxResourceReady({ html, csp, permissions });
  log.info("Waiting for MCP App to initialize...");
  await appInitializedPromise;
  log.info("MCP App initialized");
  log.info("Sending tool call input to MCP App:", input);
  appBridge.sendToolInput({ arguments: input });
  resultPromise.then(
    (result) => { log.info("Sending tool call result to MCP App:", result); appBridge.sendToolResult(result); },
    (error)  => { log.error("Tool call failed, sending cancellation to MCP App:", error); appBridge.sendToolCancelled({ reason: error instanceof Error ? error.message : String(error) }); },
  );
}

function hookInitializedCallback(appBridge: AppBridge): Promise<void> {
  const oninitialized = appBridge.oninitialized;
  return new Promise<void>((resolve) => {
    appBridge.oninitialized = (...args) => {
      resolve();
      appBridge.oninitialized = oninitialized;
      appBridge.oninitialized?.(...args);
    };
  });
}

export type ModelContext = McpUiUpdateModelContextRequest["params"];
export type AppMessage = McpUiMessageRequest["params"];

export interface AppBridgeCallbacks {
  onContextUpdate?: (context: ModelContext | null) => void;
  onMessage?: (message: AppMessage) => void;
  onDisplayModeChange?: (mode: "inline" | "fullscreen") => void;
}

export interface AppBridgeOptions {
  containerDimensions?: { maxHeight?: number; width?: number } | { height: number; width?: number };
  displayMode?: "inline" | "fullscreen";
}

/**
 * Creates AppBridge with policy layer gating all sensitive channels when policy=on.
 * In baseline mode (policy=off) the original handlers run unmodified.
 */
export function newAppBridge(
  serverInfo: ServerInfo,
  iframe: HTMLIFrameElement,
  callbacks?: AppBridgeCallbacks,
  options?: AppBridgeOptions,
): AppBridge {
  const serverCapabilities = serverInfo.client.getServerCapabilities();
  const appBridge = new AppBridge(serverInfo.client, IMPLEMENTATION, {
    openLinks: {},
    serverTools: serverCapabilities?.tools,
    serverResources: serverCapabilities?.resources,
    updateModelContext: { text: {} },
  }, {
    hostContext: {
      theme: getTheme(),
      platform: "web",
      styles: { variables: HOST_STYLE_VARIABLES },
      containerDimensions: options?.containerDimensions ?? { maxHeight: 6000 },
      displayMode: options?.displayMode ?? "inline",
      availableDisplayModes: ["inline", "fullscreen"],
    },
  });

  onThemeChange((newTheme) => {
    log.info("Theme changed:", newTheme);
    appBridge.sendHostContextChange({ theme: newTheme });
  });

  const iframeResizeObserver = new ResizeObserver(([entry]) => {
    const width = Math.round(entry.contentRect.width);
    if (width > 0) appBridge.sendHostContextChange({ containerDimensions: { width, maxHeight: 6000 } });
  });
  iframeResizeObserver.observe(iframe);
  const prevOnclose = appBridge.onclose;
  appBridge.onclose = () => { iframeResizeObserver.disconnect(); prevOnclose?.(); };

  // ── Policy-gated handlers ──────────────────────────────────────────────
  appBridge.onmessage = async (params, _extra) => {
    const d = await gateMessage(params as Record<string, unknown>, POLICY_CFG);
    audit(POLICY_CFG, "ui/message", d.allowed ? "allow" : "deny", d.reason, d.consented, d.elapsedMs).catch(() => {});
    if (!d.allowed) throw new Error(`Policy denied: ${d.reason}`);
    log.info("Message from MCP App:", params);
    callbacks?.onMessage?.(params);
    return {};
  };

  appBridge.onopenlink = async (params, _extra) => {
    const d = await gateOpenLink(params as { url: string }, POLICY_CFG);
    audit(POLICY_CFG, "ui/open-link", d.allowed ? "allow" : "deny", d.reason, d.consented, d.elapsedMs).catch(() => {});
    if (!d.allowed) return { isError: true } as any;
    log.info("Open link request:", params);
    window.open(params.url, "_blank", "noopener,noreferrer");
    return {};
  };

  appBridge.onloggingmessage = (params) => { log.info("Log message from MCP App:", params); };

  appBridge.onupdatemodelcontext = async (params) => {
    const d = await gateContext(params as Record<string, unknown>, POLICY_CFG);
    audit(POLICY_CFG, "ui/update-model-context", d.allowed ? "allow" : "deny", d.reason, d.consented, d.elapsedMs).catch(() => {});
    if (!d.allowed) throw new Error(`Policy denied: ${d.reason}`);
    log.info("Model context update from MCP App:", params);
    const hasContent    = params.content && params.content.length > 0;
    const hasStructured = params.structuredContent && Object.keys(params.structuredContent).length > 0;
    callbacks?.onContextUpdate?.(hasContent || hasStructured ? params : null);
    return {};
  };

  appBridge.onsizechange = async ({ width, height }) => {
    const style = getComputedStyle(iframe);
    const isBorderBox = style.boxSizing === "border-box";
    const from: Keyframe = {};
    const to: Keyframe = {};
    if (width !== undefined) {
      if (isBorderBox) width += parseFloat(style.borderLeftWidth) + parseFloat(style.borderRightWidth);
      from.minWidth = `${iframe.offsetWidth}px`;
      iframe.style.minWidth = to.minWidth = `min(${width}px, 100%)`;
    }
    if (height !== undefined) {
      if (isBorderBox) height += parseFloat(style.borderTopWidth) + parseFloat(style.borderBottomWidth);
      from.height = `${iframe.offsetHeight}px`;
      iframe.style.height = to.height = `${height}px`;
    }
    iframe.animate([from, to], { duration: 300, easing: "ease-out" });
  };

  appBridge.onrequestdisplaymode = async (params) => {
    const newMode = params.mode === "fullscreen" ? "fullscreen" : "inline";
    appBridge.sendHostContextChange({ displayMode: newMode });
    callbacks?.onDisplayModeChange?.(newMode);
    return { mode: newMode };
  };

  return appBridge;
}

/**
 * Wrap oncalltool AFTER connect() so tools/call visibility gate is enforced.
 * Must be called after initializeApp() which internally calls bridge.connect().
 */
export function wrapOnCallTool(appBridge: AppBridge, _serverInfo: ServerInfo) {
  const original = (appBridge as any).oncalltool;
  if (typeof original !== "function") {
    log.warn("oncalltool is not a function after connect — skipping visibility gate");
    return;
  }
  (appBridge as any).oncalltool = async (params: any, extra: any) => {
    const name = params?.name ?? "";
    const d = gateToolVisibility(name, POLICY_CFG);
    audit(POLICY_CFG, "tools/call", d.allowed ? "allow" : "deny", d.reason, d.consented, d.elapsedMs).catch(() => {});
    if (!d.allowed) throw new Error(`Policy denied: tool '${name}' is not visible to apps`);
    return original(params, extra);
  };
}
