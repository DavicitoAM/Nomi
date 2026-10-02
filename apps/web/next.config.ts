import type { NextConfig } from "next";

const config: NextConfig = {
  async rewrites() {
    return [{ source: "/api/v1/:path*", destination: `${process.env.API_INTERNAL_URL ?? "http://127.0.0.1:8000"}/api/v1/:path*` }];
  },
  async headers() {
    return [{ source: "/:path*", headers: [
      { key: "X-Content-Type-Options", value: "nosniff" },
      { key: "Referrer-Policy", value: "same-origin" },
      { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
      { key: "X-Frame-Options", value: "DENY" }
    ] }];
  }
};
export default config;
