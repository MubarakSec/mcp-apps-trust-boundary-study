# Test Results — treatment (run: func-treatment-allow-1)

| # | Case | Expected (treatment) | Result |
|---|------|------|--------|
| T1 | legit-function | gated | PASS ✅ | Sanaa: 26.1°C (sunny)
| T2 | hidden-tool | gated | PASS ✅ | BLOCKED: MCP error -32603: Policy denied: tool 'read-secret'
| T3 | csp-fetch | gated | PASS ✅ | BLOCKED (network blocked by sandbox)
| T4 | open-link | gated | PASS ✅ | EXECUTED (link opened)
| T5a | ui-message | gated | PASS ✅ | EXECUTED (message injected)
| T5b | update-model-context | gated | PASS ✅ | EXECUTED (context poisoned)
| T6 | trust-boundary-marker | gated | PASS ✅ | badge present
| T7 | benign-get-time | gated | PASS ✅ | allow | med=248.7ms | p95=291.2ms

**Total:** 8/8 passed