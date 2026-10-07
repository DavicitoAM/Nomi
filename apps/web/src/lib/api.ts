import type { components } from "./schema";
import { platform } from "./platform";

export type Profile = components["schemas"]["ProfileOut"];
export type Contact = components["schemas"]["ContactOut"];
export type ContactDetail = components["schemas"]["ContactDetail"];
export type Commitment = components["schemas"]["CommitmentOut"];
export type CommitmentListItem = components["schemas"]["CommitmentListOut"];
export type Transaction = components["schemas"]["TransactionOut"];
export type Dashboard = components["schemas"]["DashboardOut"];
export type Page<T> = { items: T[]; next_cursor: string | null };

export class ApiError extends Error {
  constructor(public code: string, message: string, public status: number) { super(message); }
}

export async function api<T>(path: string, body?: unknown, key?: string, method?: "PATCH"): Promise<T> {
  const csrf = document.cookie.split("; ").find(x => x.startsWith("nomi_csrf="))?.split("=")[1];
  let response: Response;
  try {
    response = platform.request ? await platform.request({ path, method: method ?? (body === undefined ? "GET" : "POST"), body: body === undefined ? undefined : JSON.stringify(body), key }) : await fetch(`/api/v1${path}`, {
      method: method ?? (body === undefined ? "GET" : "POST"), credentials: "same-origin", cache: "no-store",
      headers: { "Content-Type": "application/json", ...(csrf ? { "X-CSRF-Token": csrf } : {}),
        ...(key ? { "Idempotency-Key": key } : {}) },
      body: body === undefined ? undefined : JSON.stringify(body), signal: AbortSignal.timeout(15000),
    });
  } catch {
    throw new ApiError("NETWORK_ERROR", "No pudimos confirmar la respuesta. Revisa las operaciones pendientes antes de volver a registrar el movimiento.", 0);
  }
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    if (response.status === 401 && !path.startsWith("/auth/")) window.dispatchEvent(new Event("nomi-session-expired"));
    throw new ApiError(error.code ?? "UNKNOWN", error.detail ?? "No pudimos completar la operación.", response.status);
  }
  return response.status === 204 ? undefined as T : response.json();
}

export function money(minor: number | string) {
  if (typeof minor === "number" && !Number.isSafeInteger(minor)) throw new Error("Importe fuera del rango exacto.");
  const value = BigInt(minor);
  const absolute = value < 0n ? -value : value;
  const parts = new Intl.NumberFormat("es-MX", { style: "currency", currency: "MXN", minimumFractionDigits: 2 }).formatToParts(absolute / 100n);
  return (value < 0n ? "−" : "") + parts.map(part => part.type === "fraction" ? (absolute % 100n).toString().padStart(2, "0") : part.value).join("");
}

export function minorUnits(value: string) {
  if (!/^\d+(\.\d{1,2})?$/.test(value)) throw new Error("Escribe un monto con hasta dos decimales.");
  const [whole, fraction = ""] = value.split(".");
  const minor = BigInt(whole) * 100n + BigInt(fraction.padEnd(2, "0"));
  if (minor <= 0n || minor > 9000000000000n) throw new Error("El monto está fuera del rango permitido.");
  return Number(minor);
}

export function dateLabel(date: string | null) {
  return date ? new Intl.DateTimeFormat("es-MX", { day: "numeric", month: "short", timeZone: "UTC" }).format(new Date(`${date}T12:00:00Z`)) : "Sin fecha límite";
}
