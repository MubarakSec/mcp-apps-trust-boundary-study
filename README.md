# Evaluating Trust Boundaries in MCP Apps — Research Package

> **Emirates International University — 2026/8**  
> Prof. Dr. Malik Nasir Ali Al-Jabri (Supervisor) — Mubarak Walid Al-Hamadi — Yasin Abd Al-Aziz Al-Khalqi — Muhammad Saif Ali Al-Heimi

**One-line:** We measure what the MCP Apps sandbox *technically* blocks vs. what the **host must govern by policy**, then prove a tiny host-side policy layer closes the gap with ~0 ms overhead.

---

## What is this repo?

| Path | What is inside |
|------|----------------|
| `proposal.txt` | Source of truth (Arabic). Fixed: 6 weeks, correct baseline definition |
| `build_proposals.py` | Generates the Word proposals (EN / AR / Concise) |
| `MCP_Apps_Trust_Boundaries_Proposal_EN.docx` | Full English proposal — **read this first** |
| `MCP_Apps_Trust_Boundaries_Proposal_AR.docx` | Full Arabic proposal |
| `lab/ext-apps/lab-testbed/` | **Reproducible lab** — host, server, two UIs, runner, analyzer |
| `lab/ext-apps/lab-testbed/results/FINAL_REPORT.md` | **Actual measured results** (41 runs) — H1/H2/H3 ACCEPT |

No hidden steps. Everything you submit is built from these files.

---

## The core idea (60 seconds)

```
MCP Server (untrusted) --UI--> Host sandbox (iframe) --policy--> Chat / Model Context / Browser
```

- The sandbox stops the UI from touching the host page directly.
- But the UI can still ask the **host to do things**: `ui/open-link`, `ui/message`, `ui/update-model-context`.
- The MCP Apps spec **allows** those channels — the host decides whether to prompt/allow/block.
- **Baseline** = spec-compliant host (enforces `sandbox + CSP + tool.visibility MUST`, no extra prompts) → `read-secret` and CSP fetch are blocked, but links/messages/context **execute with no approval** (we exfiltrate `SYNTHETIC_SECRET_001`).
- **Treatment** = same host + 4-rule policy layer (https link allow-list + explicit consent + persistent source badge + size/rate + audit) with `default-deny` → same 3 channels are **blocked** until user approves; with `allow` they still execute (utility preserved).

Three hypotheses, tested honestly (we accept *or* reject per data):

- **H1** — both modes reject 100% of MUST violations (CSP + visibility).
- **H2** — treatment reduces sensitive actions *without approval* to 0 and blocks `SYNTHETIC_SECRET_001` exfiltration.
- **H3** — treatment keeps all legitimate controls passing and median local overhead ≤ 20 ms.

**Result (real run, 2026-09-07): H1 ACCEPT, H2 ACCEPT, H3 ACCEPT** — see table below.

---

## Results you can cite

> Full machine-readable log: `lab/ext-apps/lab-testbed/results/` (165 files, `events-*.jsonl` + `audit-*.jsonl`)

**Headline** (`results/FINAL_REPORT.md`):

- H1: baseline `0/10`, treatment `0/10` violations → ACCEPT
- H2: sensitive without approval `15/15` → `0/15`, secret via message/context `10` → `0`, utility with consent `3/3` → ACCEPT
- H3: `n=90` each, `baseline med 327.4 p95 471.0`, `treatment med 318.3 p95 474.3`, **delta med -9.1 ms p95 +3.3 ms** → ACCEPT

**Test matrix (5 reps per functional case):**

| Case | Channel | Baseline | Treatment (deny) | Treatment (allow) |
|------|---------|----------|------------------|-------------------|
| T1 | `tools/call` legit weather | allow | allow | allow |
| T2 | `tools/call` hidden `read-secret` | **BLOCK** | **BLOCK** | **BLOCK** |
| T3 | `network` CSP fetch | **BLOCK** | **BLOCK** | **BLOCK** |
| T4 | `ui/open-link` | execute | **BLOCK** | execute |
| T5a | `ui/message` | execute | **BLOCK** | execute |
| T5b | `ui/update-model-context` | execute | **BLOCK** | execute |
| T6 | source badge | absent | **present** | present |
| T7 | benign `get-time` | allow | allow | allow |

Interpretation: baseline is *compliant* — it does what the spec says. The residual risk lives in the **allowed** channels, which is exactly what the policy closes.

---

## How to reproduce (5 minutes)

### 0. Prerequisites

```bash
node --version  # 24.x used, 20+ works
npm --version   # 11.x
npx playwright --version  # chromium 1228+ (auto-installed via runner)
python3 --version  # 3.10+ for analyze.py (no pip deps)
```

Install once:

```bash
cd lab/ext-apps
npm install
npx playwright install chromium  # first time only
```

Build once (after any `host-policy/src/*.ts` change):

```bash
npm --workspace lab-testbed/host-policy run build
# dist/index.html  +  dist/sandbox.html  (539 kB, sandbox 102 kB)
```

### 1. Regenerate proposals (optional)

```bash
cd /home/mobta/university/malik
python3 build_proposals.py
# → MCP_Apps_Trust_Boundaries_Proposal_EN.docx  (43 kB)
# → MCP_Apps_Trust_Boundaries_Proposal_AR.docx  (44 kB)
```

Source is `proposal.txt` (Arabic, 6 weeks). Docx is the submission artifact.

### 2. Run the lab — the reliable way

> `lab-testbed/start.sh` uses `fuser` + `&` which leaves orphans holding the shell pipe on some zsh setups and hangs mid-run. The wrapped form below is what actually finishes 41 runs reliably.

**Single-command full experiment (~22 min, ~1.2 GB RAM peak):**

```bash
cd lab/ext-apps
rm -rf lab-testbed/results/*   # fresh
rm -f lab-testbed/rt.log

( node lab-testbed/server/receiver.mjs > lab-testbed/rec.log 2>&1 & \
  node lab-testbed/server/server.mjs > lab-testbed/srv.log 2>&1 & \
  HOST_PORT=8090 SANDBOX_PORT=8091 SERVERS='["http://localhost:3001/mcp"]' \
    npx tsx lab-testbed/host-policy/serve.ts > lab-testbed/host.log 2>&1 & \
  sleep 7; \
  echo "services up at $(date)" | tee -a lab-testbed/rt.log; \
  npx tsx lab-testbed/runner/run-all.mjs 2>&1 | tee -a lab-testbed/rt.log; \
  echo "run-all done rc=$?" | tee -a lab-testbed/rt.log ) &
wait; echo "outer done"
```

What `run-all.mjs` does internally:

- 5× `func-baseline` + 5× `func-treatment` (deny) + 1× `func-treatment-allow` + 15× `perf-baseline` + 15× `perf-treatment` (alternating)
- Each run launches Chromium `headless, channel: chromium`, drives the 8 cases via Playwright, writes `results/events-<runId>.jsonl`

**Quick smoke test (one baseline, ~35 s):**

```bash
( node lab-testbed/server/receiver.mjs > /dev/null 2>&1 & \
  node lab-testbed/server/server.mjs > /dev/null 2>&1 & \
  HOST_PORT=8090 SANDBOX_PORT=8091 SERVERS='["http://localhost:3001/mcp"]' \
    npx tsx lab-testbed/host-policy/serve.ts > /dev/null 2>&1 & \
  sleep 7; \
  npx tsx lab-testbed/runner/run-tests.mjs --mode baseline --run smoke-baseline-1 ) &
wait
cat lab-testbed/results/events-smoke-baseline-1.jsonl
```

### 3. Analyze (10 ms)

```bash
cd lab/ext-apps
python3 lab-testbed/analyze.py
cat lab-testbed/results/FINAL_REPORT.md
```

Output matches the table above. The analyzer deliberately excludes `treatment-allow` from the H2 deny count (`"allow" not in runId`).

### 4. Where logs live

```
lab-testbed/results/
  events-func-baseline-*.jsonl          5 files  → H1/H2
  events-func-treatment-*.jsonl         5 files  → H1/H2 (deny)
  events-func-treatment-allow-1.jsonl   1 file   → utility
  events-perf-baseline-*.jsonl         15 files  → H3 latency (6× T7 per file = 90 points)
  events-perf-treatment-*.jsonl        15 files  → H3
  audit-*.jsonl                         → tPolicyMs (supplementary)
  FINAL_REPORT.md                       → headline + matrix
  summary-*.md                          → per-run 8/8
lab-testbed/rt.log                      → full stdout of last run-all
lab-testbed/host.log | srv.log | rec.log → service logs
```

---

## Why previous runs hung (and why it is fixed now)

1. **Orphan Chromium** — `npx tsx run-tests.mjs` spawns `headless_shell`; `timeout -k` SIGKILL to `npx` does NOT kill the browser child, so the tool waits for the pipe forever. Fix: wrap `services + run-all` in `( … ) & wait` so the outer shell reaps cleanly; `run-tests.mjs` now always `await browser.close()`.
2. **Stale `dist/`** — `host-policy/serve.ts` serves `dist/index.html`. After editing `src/policy-layer.ts`/`implementation.ts`, you **must** `npm --workspace lab-testbed/host-policy run build`.
3. **`ROOT` bug** — `run-all.mjs:8` was `join(__dirname,"..")` → `lab-testbed/lab-testbed/run-tests.mjs` not found. Now `join(__dirname,"..","..")`.
4. **`analyze.py` double-count** — `func-treatment-*.jsonl` also matched `allow` → H2 counted 3 utility EXECUTED as leaks. Now filtered.

---

## Limitations (honest)

- One host (`basic-host` + `AppBridge`), one Linux box, 3 capability families, synthetic tools/resources + `SYNTHETIC_SECRET_001`.
- No real browser escape, no real phishing, no multi-host variance — proof-of-concept, not a product.
- Latency is local processing (Playwright + policy). Real-world LLM + network adds noise; use our 20 ms as in-lab operational threshold, not a spec norm.

---

## References (as cited in proposal)

- Model Context Protocol. (2026b). MCP Apps spec 2026-01-26.
- Salomon et al. (2026). SEP-1865: MCP Apps — Interactive UIs for MCP.
- Hou et al. (2025). MCP: Landscape, Security Threats, and Future Research.
- Maloyan & Namiot (2026). Breaking the Protocol.
- Bühler et al. (2026). AgentBound.  Debenedetti et al. (2024). AgentDojo.  Greshake et al. (2023). Not What You've Signed Up For.  Radosevich & Halloran (2025). MCP Safety Audit.

---

## For examiners: what to open first

1. `MCP_Apps_Trust_Boundaries_Proposal_EN.docx` — Sections 6.5 (matrix) + 7 (6 weeks).
2. `lab/ext-apps/lab-testbed/results/FINAL_REPORT.md` — measured H1–H3.
3. `lab/ext-apps/lab-testbed/runner/run-tests.mjs:68-350` — the 8 cases T1–T7.
4. `lab/ext-apps/lab-testbed/host-policy/src/policy-layer.ts` — the 4-rule policy.

Questions? Re-run the smoke test above — it reproduces the exact `8/8 PASS` line in under a minute.
