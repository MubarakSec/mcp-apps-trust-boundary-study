# Test Results — treatment (run: perf-treatment-15)

| # | Case | Expected (treatment) | Result |
|---|------|------|--------|
| T1 | legit-function | gated | PASS ✅ | Sanaa: 24.6°C (sunny)
| T2 | hidden-tool | gated | PASS ✅ | BLOCKED: MCP error -32603: Policy denied: tool 'read-secret'
| T3 | csp-fetch | gated | PASS ✅ | BLOCKED (network blocked by sandbox)
| T4 | open-link | gated | PASS ✅ | DENIED
| T5a | ui-message | gated | PASS ✅ | ERROR: McpError: MCP error -32603: Policy denied: user denie
| T5b | update-model-context | gated | PASS ✅ | ERROR: McpError: MCP error -32603: Policy denied: user denie
| T6 | trust-boundary-marker | gated | PASS ✅ | badge present
| T7 | benign-get-time | gated | PASS ✅ | allow | med=270.5ms | p95=270.7ms

**Total:** 8/8 passed