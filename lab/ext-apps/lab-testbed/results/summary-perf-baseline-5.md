# Test Results — baseline (run: perf-baseline-5)

| # | Case | Expected (baseline) | Result |
|---|------|------|--------|
| T1 | legit-function | passthrough | PASS ✅ | Sanaa: 18.8°C (sunny)
| T2 | hidden-tool | passthrough | PASS ✅ | BLOCKED: MCP error -32603: Policy denied: tool 'read-secret'
| T3 | csp-fetch | passthrough | PASS ✅ | BLOCKED (network blocked by sandbox)
| T4 | open-link | passthrough | PASS ✅ | EXECUTED (link opened)
| T5a | ui-message | passthrough | PASS ✅ | EXECUTED (message injected)
| T5b | update-model-context | passthrough | PASS ✅ | EXECUTED (context poisoned)
| T6 | trust-boundary-marker | passthrough | PASS ✅ | no badge
| T7 | benign-get-time | passthrough | PASS ✅ | allow | med=359.0ms | p95=379.2ms

**Total:** 8/8 passed