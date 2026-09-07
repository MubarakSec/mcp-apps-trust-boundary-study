// Exfiltration receiver (port 9999).
// Records every hit as evidence of a successful synthetic-value transfer.
import express from "express";
import fs from "node:fs";

const app = express();
const HITS_FILE = new URL("../results/receiver-hits.jsonl", import.meta.url);
let hits = [];

app.get("/exfil", (req, res) => {
  const hit = { ts: new Date().toISOString(), channel: req.query.channel ?? "unknown", value: req.query.value ?? "", url: req.originalUrl };
  hits.push(hit);
  fs.appendFileSync(HITS_FILE, JSON.stringify(hit) + "\n");
  console.log("[RECEIVER] HIT:", JSON.stringify(hit));
  res.set("Access-Control-Allow-Origin", "*");
  res.json({ ok: true });
});

app.get("/hits", (_req, res) => {
  res.set("Access-Control-Allow-Origin", "*");
  res.json(hits);
});

app.post("/reset", (_req, res) => {
  hits = [];
  fs.writeFileSync(HITS_FILE, "");
  res.set("Access-Control-Allow-Origin", "*");
  res.json({ ok: true });
});

app.listen(9999, () => console.log("[RECEIVER] listening on http://localhost:9999"));
