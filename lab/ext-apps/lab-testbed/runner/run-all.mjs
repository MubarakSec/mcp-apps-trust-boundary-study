#!/usr/bin/env node
// run-all.mjs — 5 functional baseline + 5 functional treatment (deny) + 30 perf
// runs for H3, plus a 1-run treatment-allow utility confirmation.
import { spawn } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.join(__dirname, "..", ".."); // ext-apps repo root

function run(mode, runId, extra = []) {
  return new Promise((resolve, reject) => {
    const child = spawn("npx", ["tsx", "lab-testbed/runner/run-tests.mjs", "--mode", mode, "--run", runId, ...extra], {
      cwd: ROOT, stdio: "inherit", shell: false
    });
    child.on("close", code => resolve(code));
    child.on("error", reject);
  });
}

async function main() {
  for (let i = 1; i <= 5; i++) {
    console.log(`\n========== Functional baseline ${i}/5 ==========`);
    await run("baseline", `func-baseline-${i}`);
  }
  for (let i = 1; i <= 5; i++) {
    console.log(`\n========== Functional treatment(deny) ${i}/5 ==========`);
    await run("treatment", `func-treatment-${i}`, ["--autoconsent", "deny"]);
  }
  // Utility confirmation: treatment with user consent (allow) must still execute
  // legitimate host-mediated channels (proves utility is preserved).
  console.log(`\n========== Functional treatment(allow) utility check ==========`);
  await run("treatment", `func-treatment-allow-1`, ["--autoconsent", "allow"]);
  // 30 perf (H3) — alternate baseline/treatment for overhead calc
  for (let i = 1; i <= 30; i++) {
    const mode = i % 2 === 1 ? "baseline" : "treatment";
    const extra = mode === "treatment" ? ["--autoconsent", "deny"] : [];
    console.log(`\n========== Perf ${i}/30 (${mode}) ==========`);
    await run(mode, `perf-${mode}-${Math.ceil(i / 2)}`, extra);
  }
  console.log("\nAll runs done. Aggregating...");
}
main().catch(e => { console.error(e); process.exit(1); });
