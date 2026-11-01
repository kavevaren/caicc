import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// P0: relative base so the built SPA works at the Studio domain root or under
// a path (SPEC §13). Dev server proxies /api to the FastAPI server on :7860.
export default defineConfig({
  base: "./",
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": "http://localhost:7860",
    },
  },
});
