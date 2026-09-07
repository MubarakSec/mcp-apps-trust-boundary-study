# Lab Results — Trust Boundary in MCP Apps

## Headline
- **H1** (spec compliance, both modes reject MUST violations): **ACCEPT**
  - T2 hidden-tool leaks: baseline 0/10, treatment 0/10
  - T3 CSP bypass: counted within the same totals
- **H2** (residual-risk reduction): **ACCEPT**
  - Sensitive actions without approval: baseline **15/15**, treatment **0/15**
  - SYNTHETIC_SECRET delivered via message/context: baseline **10**, treatment **0**
  - Utility (treatment + user consent): 3/3 legitimate channels still execute
- **H3** (latency overhead ≤ 20 ms): **ACCEPT**
  - baseline:  n=90  median=327.4 ms  p95=471.0 ms  mean=339.0 ms
  - treatment: n=90  median=318.3 ms  p95=474.3 ms  mean=334.6 ms
  - delta: median=-9.1 ms, p95=3.3 ms
  - pure policy decision time (tools/call) from audit: baseline=0.0 ms, treatment=0.0 ms

## Test matrix (functional runs)

| Case | Channel | Baseline | Treatment(deny) | Treatment(allow) |
| T1 | tools/call (legit weather) | allow | allow | allow |
| T2 | tools/call (hidden secret) | BLOCK | BLOCK | BLOCK |
| T3 | network (CSP) | BLOCK | BLOCK | BLOCK |
| T4 | ui/open-link | execute | BLOCK | execute |
| T5a | ui/message | execute | BLOCK | execute |
| T5b | ui/update-model-context | execute | BLOCK | execute |
| T6 | source badge | absent | present | present |
| T7 | benign get-time | allow | allow | allow |

## Interpretation
Baseline is a specification-compliant host: it enforces the sandbox, CSP and the
tool-visibility MUST, so a non-visible tool (`read-secret`) and the CSP-blocked
network fetch are both rejected. What the baseline does **not** govern is the set
of *host-mediated capabilities* the spec explicitly allows: `ui/open-link`,
`ui/message` and `ui/update-model-context` execute with no approval, which lets an
untrusted MCP App exfiltrate `SYNTHETIC_SECRET_001` into the host chat / model
context or open arbitrary links. The added policy layer closes exactly this gap:
with a default-deny consent posture it reduces sensitive actions executed without
approval to **0/15**, while a user-approved channel still
executes (utility preserved). The median added latency is **-9.1 ms**, well
under the 20 ms operational threshold.
