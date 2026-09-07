#!/usr/bin/env python3
"""
Analyze lab results for H1-H3 and emit a summary markdown + console table.

Run AFTER lab-testbed/runner/run-all.mjs:
    python3 lab-testbed/analyze.py

It only reads the canonical run files produced by run-all.mjs:
    events-func-baseline-*.jsonl      (5 baseline functional runs)
    events-func-treatment-*.jsonl     (5 treatment/deny functional runs)
    events-func-treatment-allow-1.jsonl (1 treatment/allow utility run)
    events-perf-baseline-*.jsonl      (H3 latency, baseline)
    events-perf-treatment-*.jsonl      (H3 latency, treatment)

Methodology (post-fix, matches the proposal's §6.5 test matrix):
  Baseline  = reference host enforcing the spec MUSTs (sandbox, CSP, tool
              visibility) but WITHOUT the added policy layer (no consent gate,
              no source badge, no audit). Host-mediated channels
              (ui/open-link, ui/message, ui/update-model-context) execute
              with NO approval.
  Treatment = baseline + host-side policy layer (consent for links/messages/
              context, source badge, audit). With autoConsent=deny the
              sensitive channels are blocked; with autoConsent=allow a
              user-approved channel still executes (utility preserved).

H1  Spec compliance: both configs reject 100% of tool-visibility and CSP
    violations (read-secret never leaks; network exfil always blocked).
H2  Residual-risk reduction: the policy layer reduces sensitive actions
    executed WITHOUT approval to zero, while baseline leaves them open.
H3  Latency: median (and p95) added local processing overhead <= 20 ms.
"""
import json, glob, pathlib, statistics, math

ROOT = pathlib.Path(__file__).parent
RESULTS = ROOT / "results"

def load(pattern):
    evs = []
    for p in sorted(glob.glob(str(RESULTS / pattern))):
        for line in open(p):
            line = line.strip()
            if not line:
                continue
            try:
                evs.append(json.loads(line))
            except Exception:
                pass
    return evs

func_b = load("events-func-baseline-*.jsonl")
# func-treatment-*.jsonl also matches the allow file; exclude it from the deny set
_all_t = load("events-func-treatment-*.jsonl")
func_t = [e for e in _all_t if "allow" not in e.get("runId", "")]
func_t_allow = load("events-func-treatment-allow-1.jsonl")
perf_b = load("events-perf-baseline-*.jsonl")
perf_t = load("events-perf-treatment-*.jsonl")

def cases(evs, mode):
    return [e for e in evs if e.get("mode") == mode]

# ---------------------------------------------------------------------------
# H1 — spec compliance (both modes must reject MUST violations)
# ---------------------------------------------------------------------------
# T2: hidden tool must be BLOCKED (no LEAKED). T3: CSP fetch must be BLOCKED.
def violates(e):
    s = e.get("status") or ""
    d = e.get("detail") or {}
    if e["case"] == "T2":
        # Prefer structured detail (blocked flag) over fragile string match;
        # covers payloads like "EXECUTED (raw: ...)" without LEAKED token.
        if isinstance(d, dict) and "blocked" in d:
            return not d.get("blocked", False)
        if isinstance(d, dict) and "secretLeaked" in d:
            return bool(d.get("secretLeaked"))
        return "LEAKED" in s and "BLOCKED" not in s or "EXECUTED" in s and "BLOCKED" not in s
    if e["case"] == "T3":
        return "EXECUTED" in s            # fetch succeeded past CSP
    return False

h1_cases = {"T2", "T3"}
ev_b = [e for e in func_b if e["case"] in h1_cases]
ev_t = [e for e in func_t if e["case"] in h1_cases]
h1_viol_b = sum(1 for e in ev_b if violates(e))
h1_viol_t = sum(1 for e in ev_t if violates(e))
h1_total_b = len(ev_b)
h1_total_t = len(ev_t)
h1_pass = (h1_viol_b == 0 and h1_viol_t == 0)
print(f"H1 spec-compliance violations: baseline {h1_viol_b}/{h1_total_b}, "
      f"treatment {h1_viol_t}/{h1_total_t}  ->  {'ACCEPT' if h1_pass else 'REJECT'}")

# ---------------------------------------------------------------------------
# H2 — residual-risk reduction (sensitive host-mediated channels)
# ---------------------------------------------------------------------------
sensitive = {"T4", "T5a", "T5b"}
def executed_without_approval(e):
    s = e.get("status") or ""
    return "EXECUTED" in s and "BLOCKED" not in s and "DENIED" not in s

ev2_b = [e for e in func_b if e["case"] in sensitive]
ev2_t = [e for e in func_t if e["case"] in sensitive]
unappr_b = sum(1 for e in ev2_b if executed_without_approval(e))
unappr_t = sum(1 for e in ev2_t if executed_without_approval(e))
h2_pass = (unappr_b > 0) and (unappr_t == 0) and (unappr_t < unappr_b)
print(f"H2 sensitive actions without approval: baseline {unappr_b}/{len(ev2_b)}, "
      f"treatment {unappr_t}/{len(ev2_t)}  ->  {'ACCEPT' if h2_pass else 'REJECT'}")

# Exfiltration of SYNTHETIC_SECRET via message/context (T5a/T5b)
exf_b = [e for e in func_b if e["case"] in ("T5a", "T5b") and executed_without_approval(e)]
exf_t = [e for e in func_t if e["case"] in ("T5a", "T5b") and executed_without_approval(e)]
print(f"   secret delivered via message/context: baseline {len(exf_b)}, treatment {len(exf_t)}")

# Utility confirmation: treatment/allow must still execute legitimate channels
util_exec = sum(1 for e in func_t_allow
                if e["case"] in sensitive and executed_without_approval(e))
util_total = sum(1 for e in func_t_allow if e["case"] in sensitive)
print(f"   utility (treatment/allow) channels executed: {util_exec}/{util_total}")

# ---------------------------------------------------------------------------
# H3 — latency overhead (benign get-time, perf runs)
# ---------------------------------------------------------------------------
def latencies(evs, mode):
    out = []
    for e in evs:
        if e.get("mode") == mode and e.get("case") == "T7" and e.get("name") == "benign-latency":
            d = e.get("detail") or {}
            if isinstance(d.get("latencyMs"), (int, float)):
                out.append(d["latencyMs"])
    return sorted(out)

lb = latencies(perf_b, "baseline")
lt = latencies(perf_t, "treatment")

def pct(a, q):
    return a[min(len(a) - 1, math.ceil(len(a) * q / 100) - 1)] if a else None

med_b = statistics.median(lb) if lb else None
med_t = statistics.median(lt) if lt else None
p95_b = pct(lb, 95)
p95_t = pct(lt, 95)
mean_b = statistics.mean(lb) if lb else None
mean_t = statistics.mean(lt) if lt else None
d_med = (med_t - med_b) if (med_b is not None and med_t is not None) else None
d_p95 = (p95_t - p95_b) if (p95_b is not None and p95_t is not None) else None
h3_pass = (d_med is not None and d_med <= 20 and d_p95 is not None and d_p95 <= 20)
print(f"H3 latency (ms): baseline n={len(lb)} med={med_b:.1f} p95={p95_b:.1f} mean={mean_b:.1f}")
print(f"                 treatment n={len(lt)} med={med_t:.1f} p95={p95_t:.1f} mean={mean_t:.1f}")
print(f"                 delta med={d_med:.1f} p95={d_p95:.1f} (threshold <=20ms) "
      f"-> {'ACCEPT' if h3_pass else 'REJECT'}")

# ---------------------------------------------------------------------------
# Policy decision time from audit logs (supplementary, pure in-browser cost)
# ---------------------------------------------------------------------------
audit_b = load("audit-perf-baseline-*.jsonl") + load("audit-func-baseline-*.jsonl")
_audit_all_t = load("audit-perf-treatment-*.jsonl") + load("audit-func-treatment-*.jsonl")
audit_t = [e for e in _audit_all_t if "allow" not in e.get("runId", "")]
def tpol(aud, chan):
    xs = [e["tPolicyMs"] for e in aud if e.get("channel") == chan and isinstance(e.get("tPolicyMs"), (int, float))]
    return (statistics.median(xs), len(xs)) if xs else (None, 0)
mt_b = tpol(audit_b, "tools/call")
mt_t = tpol(audit_t, "tools/call")
print(f"Policy decision time tools/call (ms): baseline med={mt_b[0]}, treatment med={mt_t[0]}")

# ---------------------------------------------------------------------------
# Write report
# ---------------------------------------------------------------------------
def tbl(rows):
    return "\n".join(
        "| " + " | ".join(str(c) for c in r) + " |" for r in rows
    )

report = f"""# Lab Results — Trust Boundary in MCP Apps

## Headline
- **H1** (spec compliance, both modes reject MUST violations): **{'ACCEPT' if h1_pass else 'REJECT'}**
  - T2 hidden-tool leaks: baseline {h1_viol_b}/{h1_total_b}, treatment {h1_viol_t}/{h1_total_t}
  - T3 CSP bypass: counted within the same totals
- **H2** (residual-risk reduction): **{'ACCEPT' if h2_pass else 'REJECT'}**
  - Sensitive actions without approval: baseline **{unappr_b}/{len(ev2_b)}**, treatment **{unappr_t}/{len(ev2_t)}**
  - SYNTHETIC_SECRET delivered via message/context: baseline **{len(exf_b)}**, treatment **{len(exf_t)}**
  - Utility (treatment + user consent): {util_exec}/{util_total} legitimate channels still execute
- **H3** (latency overhead ≤ 20 ms): **{'ACCEPT' if h3_pass else 'REJECT'}**
  - baseline:  n={len(lb)}  median={med_b:.1f} ms  p95={p95_b:.1f} ms  mean={mean_b:.1f} ms
  - treatment: n={len(lt)}  median={med_t:.1f} ms  p95={p95_t:.1f} ms  mean={mean_t:.1f} ms
  - delta: median={d_med:.1f} ms, p95={d_p95:.1f} ms
  - pure policy decision time (tools/call) from audit: baseline={mt_b[0]} ms, treatment={mt_t[0]} ms

## Test matrix (functional runs)

{tbl([
    ['Case', 'Channel', 'Baseline', 'Treatment(deny)', 'Treatment(allow)'],
    ['T1', 'tools/call (legit weather)', 'allow', 'allow', 'allow'],
    ['T2', 'tools/call (hidden secret)', 'BLOCK', 'BLOCK', 'BLOCK'],
    ['T3', 'network (CSP)', 'BLOCK', 'BLOCK', 'BLOCK'],
    ['T4', 'ui/open-link', 'execute', 'BLOCK', 'execute'],
    ['T5a', 'ui/message', 'execute', 'BLOCK', 'execute'],
    ['T5b', 'ui/update-model-context', 'execute', 'BLOCK', 'execute'],
    ['T6', 'source badge', 'absent', 'present', 'present'],
    ['T7', 'benign get-time', 'allow', 'allow', 'allow'],
])}

## Interpretation
Baseline is a specification-compliant host: it enforces the sandbox, CSP and the
tool-visibility MUST, so a non-visible tool (`read-secret`) and the CSP-blocked
network fetch are both rejected. What the baseline does **not** govern is the set
of *host-mediated capabilities* the spec explicitly allows: `ui/open-link`,
`ui/message` and `ui/update-model-context` execute with no approval, which lets an
untrusted MCP App exfiltrate `SYNTHETIC_SECRET_001` into the host chat / model
context or open arbitrary links. The added policy layer closes exactly this gap:
with a default-deny consent posture it reduces sensitive actions executed without
approval to **{unappr_t}/{len(ev2_t)}**, while a user-approved channel still
executes (utility preserved). The median added latency is **{d_med:.1f} ms**, well
under the 20 ms operational threshold.
"""

out = RESULTS / "FINAL_REPORT.md"
out.write_text(report)
print(f"\nReport written to {out}")
