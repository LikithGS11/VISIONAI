import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// In development, Vite serves the UI on :5173 and forwards API + WebSocket
// calls to FastAPI on :8000, so the browser only ever talks to one origin.
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    proxy: {
      "/api": "http://127.0.0.1:8000",
      "/ws": { target: "ws://127.0.0.1:8000", ws: true },
    },
  },
});
