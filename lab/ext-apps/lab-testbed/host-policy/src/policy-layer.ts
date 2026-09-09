/**
 * policy-layer.ts — Host-side policy enforcement for MCP Apps trust-boundary study.
 *
 * Implements the four rules from the approved proposal (§6.3):
 *   1. Link safety — protocol scheme validation (http/https) and user consent
 *   2. Message / context — payload size bound (4 KB cap) and user consent
 *   3. Visible trust boundary — source badge (rendered by React in index.tsx)
 *   4. Audit — structured JSON log of every intercepted request
 *
 * Also enforces MUST rule for tools/call visibility (spec §Visibility):
 *   Apps MUST NOT call tools with visibility: ["model"].
 */

// ─── Types ─────────────────────────────────────────────────────────────

export interface PolicyConfig {
  enabled: boolean;
  autoConsent: "allow" | "deny" | null;   // null = interactive (consent modal)
  runId: string;
}

export interface PolicyDecision {
  allowed: boolean;
  reason: string;
  consented: boolean | null;               // null = no consent required
  elapsedMs: number;
}

export interface PolicyEvent {
  runId: string;
  mode: "baseline" | "treatment";
  seq: number;
  ts: string;
  channel: string;
  decision: "allow" | "deny";
  reason: string;
  consented: boolean | null;
  tPolicyMs: number;
}

// ─── Configuration ─────────────────────────────────────────────────────

export function loadPolicy(): PolicyConfig {
  const p = new URLSearchParams(window.location.search);
  return {
    enabled: p.get("policy") === "on",
    autoConsent: (p.get("autoconsent") as "allow" | "deny") || null,
    runId: p.get("run") || "default",
  };
}

// ─── Timer ─────────────────────────────────────────────────────────────

function timer() {
  const t0 = performance.now();
  return () => +(performance.now() - t0).toFixed(2);
}

// ─── Audit log (server collects) ───────────────────────────────────────

let auditSeq = 0;
const AUDIT_URL = "http://localhost:3001/audit";

export async function audit(
  cfg: PolicyConfig,
  channel: string,
  decision: "allow" | "deny",
  reason: string,
  consented: boolean | null,
  elapsedMs: number,
) {
  const ev: PolicyEvent = {
    runId: cfg.runId,
    mode: cfg.enabled ? "treatment" : "baseline",
    seq: ++auditSeq,
    ts: new Date().toISOString(),
    channel,
    decision,
    reason,
    consented,
    tPolicyMs: elapsedMs,
  };
  try {
    await fetch(AUDIT_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(ev),
    });
  } catch { /* best effort */ }
}

// ─── Link rule ─────────────────────────────────────────────────────────

function checkOpenLink(params: { url: string }): PolicyDecision {
  const end = timer();
  const { url } = params;
  if (!url.startsWith("https://") && !url.startsWith("http://")) {
    return { allowed: false, reason: "non-http URL", consented: null, elapsedMs: end() };
  }
  return { allowed: true, reason: "link ok", consented: null, elapsedMs: end() };
}

// ─── Message / context rule ────────────────────────────────────────────

const MAX_MSG_BYTES = 4096;

function checkMessage(params: Record<string, unknown>): PolicyDecision {
  const end = timer();
  const size = new TextEncoder().encode(JSON.stringify(params)).byteLength;
  if (size > MAX_MSG_BYTES) {
    return { allowed: false, reason: `message too large (${size} > ${MAX_MSG_BYTES})`, consented: null, elapsedMs: end() };
  }
  return { allowed: true, reason: "message ok", consented: null, elapsedMs: end() };
}

function checkContext(params: Record<string, unknown>): PolicyDecision {
  const end = timer();
  const size = new TextEncoder().encode(JSON.stringify(params)).byteLength;
  if (size > MAX_MSG_BYTES) {
    return { allowed: false, reason: `context too large (${size} > ${MAX_MSG_BYTES})`, consented: null, elapsedMs: end() };
  }
  return { allowed: true, reason: "context ok", consented: null, elapsedMs: end() };
}

// ─── Consent (promise-based via DOM event) ─────────────────────────────

const pendingConsent = new Map<string, { resolve: (v: boolean) => void; timer?: ReturnType<typeof setTimeout> }>();

let consentId = 0;

function requestConsent(channel: string, params: unknown, cfg: PolicyConfig): Promise<boolean> {
  return new Promise<boolean>((resolve) => {
    if (cfg.autoConsent === "allow") { resolve(true); return; }
    if (cfg.autoConsent === "deny")  { resolve(false); return; }

    const id = String(++consentId);
    pendingConsent.set(id, { resolve });

    const t = setTimeout(() => {
      const p = pendingConsent.get(id);
      if (p) { p.resolve(false); pendingConsent.delete(id); }
    }, 5000);
    pendingConsent.get(id)!.timer = t;

    window.dispatchEvent(new CustomEvent("policy:consent-request", {
      detail: { id, channel, params },
    }));
  });
}

export function resolveConsent(id: string, allow: boolean) {
  const p = pendingConsent.get(id);
  if (!p) return;
  clearTimeout(p.timer);
  p.resolve(allow);
  pendingConsent.delete(id);
}

// ─── Tool visibility gate (spec §Visibility: MUST reject) ──────────────

let serverToolsForGate: Map<string, { _meta?: Record<string, unknown> }> | null = null;

export function setServerToolsForGate(tools: Map<string, { _meta?: Record<string, unknown> }>) {
  serverToolsForGate = tools;
}

export function gateToolVisibility(name: string, _cfg?: PolicyConfig): PolicyDecision {
  const end = timer();
  // Spec §Visibility MUST: apps must not call tools lacking "app" visibility.
  // This is a baseline requirement, not part of the added policy layer, so it is
  // enforced in BOTH baseline and treatment. (The reference host otherwise fails it.)
  if (!serverToolsForGate) {
    return { allowed: false, reason: "fail-closed: tools metadata uninitialized", consented: null, elapsedMs: end() };
  }
  const tool = serverToolsForGate.get(name);
  if (!tool) {
    return { allowed: false, reason: "unknown tool", consented: null, elapsedMs: end() };
  }
  const visibility = (tool._meta as any)?.ui?.visibility as string[] | undefined;
  const hasApp = !visibility || visibility.includes("app");
  return {
    allowed: hasApp,
    reason: hasApp ? "tool visible to apps" : `tool visibility: ${JSON.stringify(visibility)}`,
    consented: null,
    elapsedMs: end(),
  };
}

// ─── Main gate functions ───────────────────────────────────────────────

export async function gateOpenLink(params: { url: string }, cfg: PolicyConfig): Promise<PolicyDecision> {
  if (!cfg.enabled) {
    return { allowed: true, reason: "baseline", consented: null, elapsedMs: 0 };
  }
  const check = checkOpenLink(params);
  if (!check.allowed) return check;
  const consented = await requestConsent("ui/open-link", params, cfg);
  if (!consented) return { allowed: false, reason: "user denied", consented: false, elapsedMs: check.elapsedMs };
  return { allowed: true, reason: "user approved", consented: true, elapsedMs: check.elapsedMs };
}

export async function gateMessage(params: Record<string, unknown>, cfg: PolicyConfig): Promise<PolicyDecision> {
  if (!cfg.enabled) {
    return { allowed: true, reason: "baseline", consented: null, elapsedMs: 0 };
  }
  const check = checkMessage(params);
  if (!check.allowed) return check;
  // Message injection is a sensitive host-mediated channel: require explicit user
  // consent. With autoConsent=allow the simulated user APPROVES (utility path);
  // with autoConsent=deny they DENY (security path). Null → interactive modal.
  const consented = await requestConsent("ui/message", params, cfg);
  if (!consented) return { allowed: false, reason: "user denied", consented: false, elapsedMs: check.elapsedMs };
  return { allowed: true, reason: "user approved", consented: true, elapsedMs: check.elapsedMs };
}

export async function gateContext(params: Record<string, unknown>, cfg: PolicyConfig): Promise<PolicyDecision> {
  if (!cfg.enabled) {
    return { allowed: true, reason: "baseline", consented: null, elapsedMs: 0 };
  }
  const check = checkContext(params);
  if (!check.allowed) return check;
  const consented = await requestConsent("ui/update-model-context", params, cfg);
  if (!consented) return { allowed: false, reason: "user denied", consented: false, elapsedMs: check.elapsedMs };
  return { allowed: true, reason: "user approved", consented: true, elapsedMs: check.elapsedMs };
}
