import type { Metadata } from "next";
import { headers } from "next/headers";
import { Providers } from "./providers";
import "./globals.css";

export const metadata: Metadata = {
  title: "Nomi · Tus pendientes, en orden",
  description: "Un lugar simple para saber cuánto te deben, cuánto debes y qué sigue.",
};

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  await headers(); // Per-request rendering is required for nonce-based CSP.
  return <html lang="es-MX"><body><Providers>{children}</Providers></body></html>;
}
