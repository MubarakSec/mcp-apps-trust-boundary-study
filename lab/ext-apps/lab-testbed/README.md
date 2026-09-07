# Lab Testbed — Trust Boundaries in MCP Apps

> Reproducible harness for the proposal in `/home/mobta/university/malik/` — baseline vs. treatment host, 8 test cases, 41 runs.

## Quick start (copy-paste)

```bash
cd lab/ext-apps

# 0. install (once)
npm install
npx playwright install chromium

# 1. build host policy (must after any src/ edit)
npm --workspace lab-testbed/host-policy run build

# 2. full experiment — reliable wrapper (~22 min)
rm -rf lab-testbed/results/* && rm -f lab-testbed/rt.log
( node lab-testbed/server/receiver.mjs > lab-testbed/rec.log 2>&1 & \
  node lab-testbed/server/server.mjs > lab-testbed/srv.log 2>&1 & \
  HOST_PORT=8090 SANDBOX_PORT=8091 SERVERS='["http://localhost:3001/mcp"]' \
    npx tsx lab-testbed/host-policy/serve.ts > lab-testbed/host.log 2>&1 & \
  sleep 7; \
  npx tsx lab-testbed/runner/run-all.mjs 2>&1 | tee -a lab-testbed/rt.log ) &
wait; echo done

# 3. analyze
python3 lab-testbed/analyze.py
cat lab-testbed/results/FINAL_REPORT.md
```

You should see:

```
H1 spec-compliance violations: baseline 0/10, treatment 0/10  ->  ACCEPT
H2 sensitive actions without approval: baseline 15/15, treatment 0/15  ->  ACCEPT
H3 latency (ms): ... delta med -9.1 p95 3.3 -> ACCEPT
```

---

## Why the wrapper?

Plain `bash lab-testbed/start.sh` backgrounds services with `&` inside the same shell that later runs `run-tests.mjs`. On zsh with Playwright, the orphan `headless_shell` (child of `npx tsx`) survives `timeout SIGKILL` to `npx` and holds the tool's stdout pipe, so the command appears to hang at 120–200 s even though the log file already contains `8/8 PASS`.

Wrapping in `( services & + run-all ) & wait` makes the outer shell reap the inner subshell cleanly; when the inner subshell exits after `run-all`, its background services are reparented and die with the outer shell. `run-tests.mjs` always `await browser.close()` so no orphan remains.

If you run a single case, the same pattern works:

```bash
( node lab-testbed/server/receiver.mjs > /dev/null 2>&1 & \
  node lab-testbed/server/server.mjs > /dev/null 2>&1 & \
  HOST_PORT=8090 SANDBOX_PORT=8091 SERVERS='["http://localhost:3001/mcp"]' \
    npx tsx lab-testbed/host-policy/serve.ts > /dev/null 2>&1 & \
  sleep 7; \
  npx tsx lab-testbed/runner/run-tests.mjs --mode baseline --run smoke-1 ) &
wait
```

---

## Architecture

```
lab-testbed/
  server/server.mjs        — MCP server: get-weather (app-visible), read-secret (visibility ["model"]), get-time, show-offer; CSP via headers
  server/receiver.mjs      — :9999 /hits + /reset, captures T3 network exfil attempt
  host-policy/             — Vite host (8090) + sandbox (8091) built from src/
    src/policy-layer.ts    — 4 rules: link allow-list + consent, message/context consent + badge + size/rate, audit
    src/implementation.ts  — AppBridge wiring, fire-and-forget audit
    src/index.tsx          — SourceBadge + ConsentModal (treatment only)
    serve.ts               — serves dist/index.html + dist/sandbox.html
  ui-legit/                — legitimate weather app (rendered inside host iframe)
  ui-untrusted/            — attacker app (buttons for read-secret, fetch, link, message, context, time)
  runner/run-tests.mjs     — Playwright driver for T1–T7 (see below)
  runner/run-all.mjs       — 5 baseline + 5 treatment(deny) + 1 allow + 30 perf
  analyze.py               — loads events-*.jsonl → H1/H2/H3 → FINAL_REPORT.md
```

Ports: `3001` MCP, `9999` receiver, `8090` host, `8091` sandbox.

Secret constant: `SYNTHETIC_SECRET_001` (never leaves the lab).

---

## Test matrix (what each run does)

Every `run-tests.mjs` run opens a fresh Chromium `newContext` and 8 pages:

| # | Name | Channel | What it clicks | Baseline expected | Treatment(deny) expected |
|---|------|---------|----------------|-------------------|---------------------------|
| T1 | legit weather | `tools/call` | auto (host `?tool=get-weather&call=true`) | `allow` °C | `allow` °C |
| T2 | hidden tool | `tools/call` | `btn-read` → `read-secret` | **BLOCKED** `visibility` | **BLOCKED** |
| T3 | CSP fetch | `network` | `btn-fetch` → fetch to `receiver:9999` | **BLOCKED** + `hits==0` | **BLOCKED** |
| T4 | open-link | `ui/open-link` | `btn-link` + `waitForEvent("page")` | **EXECUTED** popup/hit | **DENIED** |
| T5a | message | `ui/message` | `btn-msg` | **EXECUTED** | **DENIED** (`user denied`) |
| T5b | context | `ui/update-model-context` | `btn-ctx` | **EXECUTED** | **DENIED** |
| T6 | badge | `ui/badge` | `source-badge` count | absent | present |
| T7 | benign latency | `tools/call` | 6× `btn-time` poll until `time:` | allow, record 6 latencies | allow, record 6 |

Each case `writeEvent({case, status, detail})` to `results/events-<runId>.jsonl`. T7 latencies are `benign-latency` events used by `analyze.py` for H3 (90 points per mode).

Run IDs and modes:

- `func-baseline-1..5` — `mode=baseline`
- `func-treatment-1..5` — `mode=treatment` + `policy=on&autoconsent=deny`
- `func-treatment-allow-1` — `mode=treatment` + `autoconsent=allow` (utility, excluded from H2 deny)
- `perf-baseline-1..15`, `perf-treatment-1..15` — alternating, same T1–T7 but only T7 latencies matter

---

## Files you will actually cite

```
results/FINAL_REPORT.md          — headline (copy into thesis §6.6)
results/events-func-*.jsonl      — H1/H2 evidence
results/events-perf-*.jsonl      — H3 latency points
results/audit-*.jsonl            — tPolicyMs supplementary (median 0.0 ms)
results/summary-*.md             — per-run 8/8
rt.log                           — full stdout of last run-all (8/8 per run)
```

Example T2 leak check:

```bash
grep SYNTHETIC_SECRET_001 results/events-*.jsonl || echo "no leak"
# should print nothing — leaks are BLOCKED
```

---

## Troubleshooting

- **No output / hangs at 130 s** — you used plain `start.sh & npx tsx run-tests` without `( ) & wait`. Use the wrapped form above.
- **`Cannot find module .../lab-testbed/runner/run-tests.mjs`** — `run-all.mjs:8` ROOT must be `join(__dirname,"..","..")` (fixed). Re-pull if you see `lab-testbed/lab-testbed`.
- **`port 8090 DOWN`** — `dist/` stale. Run `npm --workspace lab-testbed/host-policy run build` again.
- **`chromium-1228 not found`** — `npx playwright install chromium`.
- **H2 shows `3/18`** — old `analyze.py` counted `allow` in deny. Now filtered (`"allow" not in runId`). Re-run `python3 analyze.py`.

---

## For developers

Edit policy: `host-policy/src/policy-layer.ts` → `npm --workspace lab-testbed/host-policy run build`.

Edit attacker UI: `ui-untrusted/src/main.ts` → `npm --workspace lab-testbed/ui-untrusted run build` (output copied to `server/ui/untrusted/mcp-app.html`).

Edit legit UI: `ui-legit/src/main.ts` similarly.

All builds are `vite build` with `vite-plugin-singlefile` → one `mcp-app.html`.

---

## Honest scope

Single host (`basic-host` + `AppBridge`), single Linux box, 3 channel families, synthetic data. No browser escape, no real users. The 20 ms H3 threshold is an in-lab operational threshold, not an MCP Apps spec norm. See `proposal.txt:6.7` and `results/FINAL_REPORT.md:Interpretation`.
