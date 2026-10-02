import type { components } from "./schema";

export type Profile = components["schemas"]["ProfileOut"];
export type Contact = components["schemas"]["ContactOut"];
export type Commitment = components["schemas"]["CommitmentOut"];
export type Transaction = components["schemas"]["TransactionOut"];
export type Dashboard = components["schemas"]["DashboardOut"];
export type Page<T> = { items: T[]; next_cursor: string | null };

export class ApiError extends Error {
  constructor(public code: string, message: string, public status: number) { super(message); }
}

export async function api<T>(path: string, body?: unknown, key?: string): Promise<T> {
  const csrf = document.cookie.split("; ").find(x => x.startsWith("nomi_csrf="))?.split("=")[1];
  let response: Response;
  try {
    response = await fetch(`/api/v1${path}`, {
      method: body === undefined ? "GET" : "POST", credentials: "same-origin", cache: "no-store",
      headers: { "Content-Type": "application/json", ...(csrf ? { "X-CSRF-Token": csrf } : {}),
        ...(key ? { "Idempotency-Key": key } : {}) },
      body: body === undefined ? undefined : JSON.stringify(body), signal: AbortSignal.timeout(15000),
    });
  } catch {
    throw new ApiError("NETWORK_ERROR", "No pudimos confirmar la operación. Reintenta con los mismos datos; no duplicaremos el abono.", 0);
  }
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    if (response.status === 401 && path !== "/me" && !path.startsWith("/auth/")) window.dispatchEvent(new Event("nomi-session-expired"));
    throw new ApiError(error.code ?? "UNKNOWN", error.detail ?? "No pudimos completar la operación.", response.status);
  }
  return response.status === 204 ? undefined as T : response.json();
}

export function money(minor: number) {
  return new Intl.NumberFormat("es-MX", { style: "currency", currency: "MXN", minimumFractionDigits: 2 }).format(minor / 100);
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
