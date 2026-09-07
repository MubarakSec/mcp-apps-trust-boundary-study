import { App } from "@modelcontextprotocol/ext-apps";
import type { CallToolResult } from "@modelcontextprotocol/sdk/types.js";

const app = new App({ name: "Weather App", version: "1.0.0" });

function extract(result: CallToolResult): string {
  const sc = result.structuredContent as { city?: string; tempC?: number; conditions?: string } | undefined;
  if (!sc) return "[no data]";
  return `${sc.city}: ${sc.tempC}°C (${sc.conditions})`;
}

const root = document.getElementById("root")!;
root.innerHTML = `
<div style="padding:16px;font-family:system-ui">
  <h3 style="margin:0 0 8px">Weather Station</h3>
  <div id="status" data-testid="weather-status"
       style="padding:8px;background:#e8f5e9;border:1px solid #4caf50;border-radius:4px;margin-bottom:12px">
    Loading…</div>
  <button id="refresh" data-testid="refresh-btn"
          style="padding:8px 16px;border-radius:4px;border:1px solid #4caf50;background:#4caf50;color:#fff;cursor:pointer">
    Refresh</button>
</div>`;

const status = document.getElementById("status")!;

app.ontoolinput = () => { status.textContent = "Waiting…"; };
app.ontoolresult = (r: CallToolResult) => { status.textContent = extract(r); };
app.ontoolcancelled = () => { status.textContent = "Cancelled"; };
app.onerror = (e: unknown) => { status.textContent = "Error: " + String(e); };

document.getElementById("refresh")!.onclick = async () => {
  status.textContent = "Refreshing…";
  try {
    const r = await app.callServerTool({ name: "get-weather", arguments: { city: "Sanaa" } });
    status.textContent = extract(r);
  } catch (e: unknown) {
    status.textContent = "Error: " + String(e);
  }
};

app.connect().then(() => {});
