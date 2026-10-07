import type { CapacitorConfig } from "@capacitor/cli";

const config: CapacitorConfig = {
  appId: "app.nomi.mobile", appName: "Nomi", webDir: "dist",
  server: { hostname: "localhost", androidScheme: "https" },
  android: { allowMixedContent: false, webContentsDebuggingEnabled: false },
  loggingBehavior: "none",
};
export default config;
