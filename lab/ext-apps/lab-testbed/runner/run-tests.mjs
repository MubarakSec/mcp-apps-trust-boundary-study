#!/usr/bin/env npx tsx
/**
 * Playwright test runner for "Evaluating Trust Boundaries in MCP Apps".
 *
 * Produces structured JSONL results in ../results/ and a summary file.
 *
 * Usage:
 *   npx tsx lab-testbed/runner/run-tests.mjs [--mode baseline|treatment] [--run <id>]
 */
import { chromium } from "playwright-core";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const RESULTS_DIR = path.join(__dirname, "..", "results");
const RECEIVER_URL = "http://localhost:9999";

fs.mkdirSync(RESULTS_DIR, { recursive: true });

const ARGS = process.argv.slice(2);
const getArg = (name) => { const i = ARGS.indexOf(name); return i >= 0 ? ARGS[i + 1] : null; };
const MODE    = getArg("--mode") ?? "baseline";       // baseline | treatment
const RUN_ID  = getArg("--run")  ?? `${MODE}-${Date.now()}`;
const AUTOCONSENT = getArg("--autoconsent") ?? (MODE === "treatment" ? "deny" : "");

const MODES = ["baseline", "treatment"];
if (!MODES.includes(MODE)) { console.error("Invalid --mode:", MODE); process.exit(1); }

const OUT_FILE      = path.join(RESULTS_DIR, `events-${RUN_ID}.jsonl`);
const RECEIVER_FILE = path.join(RESULTS_DIR, `receiver-${RUN_ID}.jsonl`);
const SUMMARY_FILE  = path.join(RESULTS_DIR, `summary-${RUN_ID}.md`);

const IS_POLICY = MODE === "treatment";
// Treatment runs with a simulated user decision. "deny" measures the security
// reduction (sensitive actions blocked); "allow" measures that legitimate,
// user-approved channels still function (utility preserved).
const POLICY_PARAMS = IS_POLICY ? `&policy=on&autoconsent=${AUTOCONSENT}` : "";

// Helper: URL to host page with specific tool auto-called
function hostUrl(tool) {
  return `http://localhost:8090/?server=Lab%20MCP%20Server&tool=${encodeURIComponent(tool)}&call=true${POLICY_PARAMS}&run=${RUN_ID}`;
}

// Reset receiver before each case
async function resetReceiver() {
  try { await fetch(`${RECEIVER_URL}/hits`, { method: "DELETE" }); } catch {}
  try { await fetch(`${RECEIVER_URL}/reset`, { method: "POST" }); } catch {}
}

async function getReceiverHits() {
  try {
    const r = await fetch(`${RECEIVER_URL}/hits`);
    return r.ok ? await r.json() : [];
  } catch { return []; }
}

async function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

// Write event to JSONL
function writeEvent(ev) {
  const line = JSON.stringify({ ...ev, runId: RUN_ID, mode: MODE, ts: new Date().toISOString() }) + "\n";
  fs.appendFileSync(OUT_FILE, line);
}

// ─── Test Cases ─────────────────────────────────────────────────────────

async function runTests() {
  console.log(`\n╔══════════════════════════════════════════════╗`);
  console.log(`║  MCP Apps Trust Boundary — ${MODE.toUpperCase().padEnd(16)}║`);
  console.log(`║  runId: ${RUN_ID.padEnd(37)}║`);
  console.log(`╚══════════════════════════════════════════════╝\n`);

  const browser = await chromium.launch({ headless: true, channel: "chromium" });
  const context = await browser.newContext();
  const results = [];

  // ─── T1: Legitimate app function preservation ──────────────────────────
  {
    console.log("T1: Legitimate app — weather refresh");
    const page = await context.newPage();
    await page.goto(hostUrl("get-weather"), { waitUntil: "domcontentloaded", timeout: 20000 });
    await sleep(2000);

    // Check the legit app iframe rendered and shows weather data
    const outerFrame = page.frameLocator("iframe").first();
    const innerFrame = outerFrame.frameLocator("iframe").first();

    let status = "";
    try {
      status = await innerFrame.locator("[data-testid=weather-status]").textContent({ timeout: 6000 }) ?? "";
    } catch { status = "FRAME_NOT_FOUND"; }

    const ok = status.includes("°C") && !status.includes("Error");
    writeEvent({ case: "T1", name: "legit-function", channel: "tools/call", expected: "allow", status: ok ? "allow" : "deny", detail: status.slice(0, 200) });
    results.push({ case: "T1", name: "legit-function", pass: ok, detail: status.slice(0, 100) });
    console.log(`  → ${ok ? "PASS" : "FAIL"} | status: ${status.slice(0, 80)}\n`);
    await page.close();
  }

  // ─── T2: Hidden tool visibility enforcement ────────────────────────────
  {
    console.log("T2: Hidden tool (read-secret) visibility enforcement");
    await resetReceiver();
    const page = await context.newPage();
    await page.goto(hostUrl("show-offer"), { waitUntil: "domcontentloaded", timeout: 20000 });
    await sleep(2000);

    const outerFrame = page.frameLocator("iframe").first();
    const innerFrame = outerFrame.frameLocator("iframe").first();

    let status = "";
    try {
      // Click the "Read Hidden Secret" button
      await innerFrame.locator("[data-testid=btn-read]").click({ timeout: 4000 });
      await sleep(2000);
      status = await innerFrame.locator("[data-testid=status]").textContent({ timeout: 4000 }) ?? "";
    } catch { status = "FRAME_NOT_FOUND"; }

    // Spec §Visibility MUST: apps must not call tools lacking "app" visibility.
    // This is enforced in BOTH baseline (spec-compliant host) and treatment.
    // A leak (secret visible) is a violation in either mode.
    const blocked = status.includes("BLOCKED") || status.includes("DENIED") || status.includes("ERROR");
    const secretLeaked = status.includes("SYNTHETIC_SECRET_001") && !status.includes("BLOCKED");
    const pass = blocked; // both modes must block the non-visible tool

    writeEvent({ case: "T2", name: "hidden-tool", channel: "tools/call", expected: "deny", status: status.slice(0, 200), detail: { secretLeaked, blocked } });
    results.push({ case: "T2", name: "hidden-tool", pass, detail: status.slice(0, 120) });
    console.log(`  → ${pass ? "PASS" : "FAIL"} | status: ${status.slice(0, 100)}\n`);
    await page.close();
  }

  // ─── T3: CSP network fetch blocked ─────────────────────────────────────
  {
    console.log("T3: CSP — network fetch blocked for untrusted app");
    await resetReceiver();
    const page = await context.newPage();
    await page.goto(hostUrl("show-offer"), { waitUntil: "domcontentloaded", timeout: 20000 });
    await sleep(2000);

    const outerFrame = page.frameLocator("iframe").first();
    const innerFrame = outerFrame.frameLocator("iframe").first();

    let status = "";
    try {
      await innerFrame.locator("[data-testid=btn-fetch]").click({ timeout: 4000 });
      await sleep(2000);
      status = await innerFrame.locator("[data-testid=status]").textContent({ timeout: 4000 }) ?? "";
    } catch { status = "FRAME_NOT_FOUND"; }

    const hits = await getReceiverHits();
    const blocked = status.includes("BLOCKED") || hits.length === 0;
    const pass = blocked;

    writeEvent({ case: "T3", name: "csp-fetch", channel: "network", expected: "blocked", status: status.slice(0, 200), detail: { receiverHits: hits.length } });
    results.push({ case: "T3", name: "csp-fetch", pass, detail: status.slice(0, 120) });
    console.log(`  → ${pass ? "PASS" : "FAIL"} | status: ${status.slice(0, 80)}\n`);
    await page.close();
  }

  // ─── T4: open-link consent gating ──────────────────────────────────────
  {
    console.log("T4: open-link — consent gating");
    await resetReceiver();
    const page = await context.newPage();
    await page.goto(hostUrl("show-offer"), { waitUntil: "domcontentloaded", timeout: 20000 });
    await sleep(2000);

    const outerFrame = page.frameLocator("iframe").first();
    const innerFrame = outerFrame.frameLocator("iframe").first();

    let status = "";
    try {
      // Listen for new pages (popups) from window.open
      const popupPromise = page.waitForEvent("page", { timeout: 5000 }).catch(() => null);
      await innerFrame.locator("[data-testid=btn-link]").click({ timeout: 4000 });
      await sleep(2000);

      // Baseline (policy off): link opens immediately, no consent.
      // Treatment (policy on, autoConsent=deny): link is blocked by the policy layer
      //   before any navigation; popup stays null and the receiver records no hit.
      const popup = await popupPromise;
      status = await innerFrame.locator("[data-testid=status]").textContent({ timeout: 4000 }) ?? "";

      const hits = await getReceiverHits();
      const executed = popup !== null || hits.length > 0;

      // Expected: baseline executes (no gate); treatment with deny is blocked;
      // treatment with allow (user-approved) executes (utility preserved).
      const expectedExecuted = !IS_POLICY || AUTOCONSENT === "allow";
      const pass = executed === expectedExecuted;

      writeEvent({ case: "T4", name: "open-link", channel: "ui/open-link", expected: expectedExecuted ? "executed" : "denied", status: status.slice(0, 200), detail: { executed, receiverHits: hits.length } });
      results.push({ case: "T4", name: "open-link", pass, detail: status.slice(0, 120) });
      console.log(`  → ${pass ? "PASS" : "FAIL"} | status: ${status.slice(0, 80)}\n`);
    } catch (e) {
      status = `error: ${String(e).slice(0, 120)}`;
      writeEvent({ case: "T4", name: "open-link", channel: "ui/open-link", expected: "executed", status, detail: null });
      results.push({ case: "T4", name: "open-link", pass: false, detail: status });
      console.log(`  → FAIL | ${status}\n`);
    }
    await page.close();
  }

  // ─── T5a: ui/message injection ─────────────────────────────────────────
  {
    console.log("T5a: ui/message — injection / consent gating");
    await resetReceiver();
    const page = await context.newPage();
    await page.goto(hostUrl("show-offer"), { waitUntil: "domcontentloaded", timeout: 20000 });
    await sleep(2000);

    const outerFrame = page.frameLocator("iframe").first();
    const innerFrame = outerFrame.frameLocator("iframe").first();

    let status = "";
    try {
      await innerFrame.locator("[data-testid=btn-msg]").click({ timeout: 4000 });
      await sleep(2000);
      status = await innerFrame.locator("[data-testid=status]").textContent({ timeout: 4000 }) ?? "";
    } catch { status = "FRAME_NOT_FOUND"; }

    const executed = status.includes("EXECUTED");
    const pass = IS_POLICY ? (AUTOCONSENT === "allow" ? executed : !executed) : executed;

    writeEvent({ case: "T5a", name: "ui-message", channel: "ui/message", expected: IS_POLICY ? (AUTOCONSENT === "allow" ? "executed" : "denied") : "executed", status: status.slice(0, 200), detail: null });
    results.push({ case: "T5a", name: "ui-message", pass, detail: status.slice(0, 120) });
    console.log(`  → ${pass ? "PASS" : "FAIL"} | status: ${status.slice(0, 80)}\n`);
    await page.close();
  }

  // ─── T5b: ui/update-model-context ──────────────────────────────────────
  {
    console.log("T5b: ui/update-model-context — poisoning / consent gating");
    await resetReceiver();
    const page = await context.newPage();
    await page.goto(hostUrl("show-offer"), { waitUntil: "domcontentloaded", timeout: 20000 });
    await sleep(2000);

    const outerFrame = page.frameLocator("iframe").first();
    const innerFrame = outerFrame.frameLocator("iframe").first();

    let status = "";
    try {
      await innerFrame.locator("[data-testid=btn-ctx]").click({ timeout: 4000 });
      await sleep(2000);
      status = await innerFrame.locator("[data-testid=status]").textContent({ timeout: 4000 }) ?? "";
    } catch { status = "FRAME_NOT_FOUND"; }

    const executed = status.includes("EXECUTED");
    const pass = IS_POLICY ? (AUTOCONSENT === "allow" ? executed : !executed) : executed;

    writeEvent({ case: "T5b", name: "update-model-context", channel: "ui/update-model-context", expected: IS_POLICY ? (AUTOCONSENT === "allow" ? "executed" : "denied") : "executed", status: status.slice(0, 200), detail: null });
    results.push({ case: "T5b", name: "update-model-context", pass, detail: status.slice(0, 120) });
    console.log(`  → ${pass ? "PASS" : "FAIL"} | status: ${status.slice(0, 80)}\n`);
    await page.close();
  }

  // ─── T6: Trust boundary marker (source badge) ──────────────────────────
  {
    console.log("T6: Trust boundary marker — source badge");
    const page = await context.newPage();
    await page.goto(hostUrl("show-offer"), { waitUntil: "domcontentloaded", timeout: 20000 });
    await sleep(2000);

    const badge = await page.locator("[data-testid=source-badge]").count();
    const hasBadge = badge > 0;
    const pass = IS_POLICY ? hasBadge : !hasBadge;

    writeEvent({ case: "T6", name: "trust-boundary-marker", channel: "ui/badge", expected: IS_POLICY ? "present" : "absent", status: hasBadge ? "present" : "absent", detail: null });
    results.push({ case: "T6", name: "trust-boundary-marker", pass, detail: hasBadge ? "badge present" : "no badge" });
    console.log(`  → ${pass ? "PASS" : "FAIL"} | badge: ${hasBadge ? "present" : "absent"}\n`);
    await page.close();
  }

  // ─── T7: Benign operation not falsely blocked (+ H3 latency) ─────
  {
    console.log("T7: Benign get-time — not falsely blocked + H3 latency");
    const page = await context.newPage();
    await page.goto(hostUrl("show-offer"), { waitUntil: "domcontentloaded", timeout: 20000 });
    await sleep(2000);

    const outerFrame = page.frameLocator("iframe").first();
    const innerFrame = outerFrame.frameLocator("iframe").first();

    let status = "";
    const latencies = [];
    let t7err = "";
    try {
      // H3: measure end-to-end latency across 6 repetitions — poll for status change
      for (let i = 0; i < 6; i++) {
        const prev = await innerFrame.locator("[data-testid=status]").textContent({ timeout: 4000 }).catch(()=>"") ?? "";
        const t0 = performance.now();
        await innerFrame.locator("[data-testid=btn-time]").click({ timeout: 4000 });
        // poll until status changes to contain time:
        const deadline = Date.now() + 7000;
        let cur = prev;
        while (Date.now() < deadline) {
          await sleep(10);
          cur = await innerFrame.locator("[data-testid=status]").textContent({ timeout: 2000 }).catch(()=>prev) ?? prev;
          if (cur !== prev && cur.includes("time:")) break;
        }
        if (!(cur !== prev && cur.includes("time:"))) throw new Error(`status did not update: ${cur.slice(0,60)}`);
        latencies.push(performance.now() - t0);
      }
      status = await innerFrame.locator("[data-testid=status]").textContent({ timeout: 4000 }) ?? "";

      for (const lat of latencies) writeEvent({ case: "T7", name: "benign-latency", channel: "tools/call", expected: "measure", status: "ok", detail: { latencyMs: lat } });
    } catch (e) { t7err = String(e).slice(0,120); status = `ERROR: ${t7err}`; }

    const passive = status.includes("EXECUTED") && status.includes("time:");
    const pass = passive;
    if (latencies.length > 0) {
      latencies.sort((a, b) => a - b);
      writeEvent({ case: "T7", name: "benign-get-time", channel: "tools/call", expected: "allow", status: status.slice(0, 200), detail: { latencyMs: latencies } });
      results.push({ case: "T7", name: "benign-get-time", pass, detail: `${passive ? "allow" : "blocked"} | med=${latencies[Math.floor(latencies.length/2)].toFixed(1)}ms | p95=${latencies[Math.min(4, latencies.length-1)].toFixed(1)}ms` });
    } else {
      results.push({ case: "T7", name: "benign-get-time", pass, detail: status.slice(0, 120) });
    }
    console.log(`  → ${pass ? "PASS" : "FAIL"} | status: ${status.slice(0, 60)} | lat: ${latencies.map(l => l.toFixed(0)).join(",")}ms\n`);
    await page.close();
  }

  await browser.close();

  // ─── Summary ───────────────────────────────────────────────────────────
  const passed = results.filter(r => r.pass).length;
  const total  = results.length;
  const lines  = [
    `# Test Results — ${MODE} (run: ${RUN_ID})`,
    "",
    `| # | Case | Expected (${IS_POLICY ? "treatment" : "baseline"}) | Result |`,
    `|---|------|------|--------|`,
    ...results.map(r => `| ${r.case} | ${r.name} | ${IS_POLICY ? "gated" : "passthrough"} | ${r.pass ? "PASS ✅" : "FAIL ❌"} | ${r.detail ? r.detail.slice(0, 60) : ""}`),
    "",
    `**Total:** ${passed}/${total} passed`,
  ];

  fs.writeFileSync(SUMMARY_FILE, lines.join("\n"));
  fs.writeFileSync(RECEIVER_FILE, "[]\n"); // placeholder

  console.log(`\n══════════════════════════════════════════════`);
  console.log(`  RESULTS: ${passed}/${total} passed (${MODE})`);
  console.log(`  Output: ${OUT_FILE}`);
  console.log(`  Summary: ${SUMMARY_FILE}`);
  console.log(`══════════════════════════════════════════════\n`);

  process.exit(passed === total ? 0 : 1);
}

runTests().catch(e => { console.error(e); process.exit(2); });
