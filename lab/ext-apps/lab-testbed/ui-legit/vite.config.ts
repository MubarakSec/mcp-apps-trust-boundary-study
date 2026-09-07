import { defineConfig } from "vite";
import { viteSingleFile } from "vite-plugin-singlefile";

export default defineConfig({
  plugins: [viteSingleFile()],
  build: {
    outDir: "../server/ui/legit",
    emptyDirOnBuild: false,
    rollupOptions: { input: "mcp-app.html" },
  },
});
