import fs from "node:fs";
import path from "node:path";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// Instancias: piloto (API 8000, front 5173) y demo (API 8001, front 5174).
// El front del demo se levanta con: POLPILOT_API_PORT=8001 npm run dev -- --port 5174
const apiPort = process.env.POLPILOT_API_PORT || "8000";

function stampServiceWorker() {
  // Cada build pisa __BUILD_ID__ en dist/sw.js para que el SW viejo se
  // reemplace y tire el cache del index.html (si no, el hash del bundle
  // queda pegado y el módulo llega como text/html).
  let swPath = "";
  return {
    name: "stamp-sw-version",
    apply: "build",
    configResolved(config) {
      swPath = path.resolve(config.root, config.build.outDir, "sw.js");
    },
    closeBundle() {
      if (!swPath || !fs.existsSync(swPath)) return;
      const src = fs.readFileSync(swPath, "utf8");
      if (!src.includes("__BUILD_ID__")) return;
      fs.writeFileSync(swPath, src.replaceAll("__BUILD_ID__", Date.now().toString(36)));
    },
  };
}

export default defineConfig({
  plugins: [react(), tailwindcss(), stampServiceWorker()],
  resolve: {
    dedupe: ["zustand"],
  },
  server: {
    port: 5173,
    // Proxy a la API de FastAPI durante desarrollo.
    // 127.0.0.1 y NO "localhost": en Windows, "localhost" resuelve primero a
    // ::1 y —con uvicorn escuchando en IPv4— cada request se come ~2 s de
    // timeout antes de reintentar. Medido acá: 2.04 s contra 0.007 s. Es sólo
    // el proxy de desarrollo (en producción el backend sirve el front: no hay
    // proxy ni segundo origen), pero hacía que el demo local pareciera lento.
    proxy: {
      "/api": `http://127.0.0.1:${apiPort}`,
    },
  },
});
