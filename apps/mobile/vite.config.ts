import { defineConfig } from "vite";
import { fileURLToPath, URL } from "node:url";
import tailwindcss from "@tailwindcss/postcss";

export default defineConfig({
  resolve: { alias: { "@": fileURLToPath(new URL("../web/src", import.meta.url)) }, dedupe: ["react", "react-dom"] },
  css: { postcss: { plugins: [tailwindcss()] } },
  server: { proxy: { "/api": { target: "http://127.0.0.1:8000", changeOrigin: true, headers: { Origin: "http://localhost:3000" } } } },
  build: { sourcemap: false, target: "es2022" },
});
