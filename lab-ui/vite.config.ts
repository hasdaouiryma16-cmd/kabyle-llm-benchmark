import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

// L'interface appelle /api sur sa propre origine ; Vite relaie vers l'API du labo.
// En local : API sur 127.0.0.1:8800 ; dans Docker Compose : http://api:8000.
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    host: "127.0.0.1",
    port: 5173,
    proxy: {
      "/api": {
        target: process.env.API_PROXY_TARGET ?? "http://127.0.0.1:8800",
        changeOrigin: true,
      },
    },
    // Les volumes Windows ne propagent pas les notifications de fichiers dans Docker
    watch: { usePolling: Boolean(process.env.VITE_POLLING) },
  },
  test: { environment: "jsdom" },
});
