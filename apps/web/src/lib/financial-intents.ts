import { api, ApiError, type Profile } from "./api";

export type FinancialIntent = { scope: string; key: string; path: string; body: object; createdAt: string };
export const intentScope = (profile: Profile) => `${profile.user.id}:${profile.workspace.id}`;
export const intentEvent = "nomi-intent-changed";

async function database(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    let request: IDBOpenDBRequest;
    try { request = indexedDB.open("nomi-financial-intents", 1); }
    catch { reject(new Error("El navegador bloqueó el almacenamiento. No se envió ningún movimiento nuevo.")); return; }
    let settled = false;
    const fail = (message: string) => { if (!settled) { settled = true; clearTimeout(timer); reject(new Error(message)); } };
    const timer = setTimeout(() => fail("El almacenamiento no respondió. Cierra otras pestañas y vuelve a intentar."), 5000);
    request.onupgradeneeded = () => request.result.createObjectStore("pending", { keyPath: "scope" });
    request.onsuccess = () => { if (settled) { request.result.close(); return; } settled = true; clearTimeout(timer); request.result.onversionchange = () => request.result.close(); resolve(request.result); };
    request.onerror = () => fail("No se pudo abrir el almacenamiento de operaciones. No se envió un movimiento nuevo.");
    request.onblocked = () => fail("Cierra otras pestañas de Nomi y vuelve a intentar.");
  });
}

async function store<T>(mode: IDBTransactionMode, operation: (store: IDBObjectStore) => IDBRequest<T>): Promise<T> {
  const db = await database();
  try {
    return await new Promise<T>((resolve, reject) => {
      const transaction = db.transaction("pending", mode);
      const request = operation(transaction.objectStore("pending"));
      transaction.oncomplete = () => resolve(request.result);
      transaction.onabort = () => reject(new Error("No pudimos conservar el estado de la operación. Revisa las operaciones pendientes."));
      transaction.onerror = () => reject(new Error("No hay almacenamiento disponible para registrar el movimiento con seguridad."));
    });
  } finally { db.close(); }
}

export const pendingIntent = (scope: string): Promise<FinancialIntent | undefined> => store("readonly", value => value.get(scope));

async function remove(scope: string) {
  await store("readwrite", value => value.delete(scope));
  window.dispatchEvent(new Event(intentEvent));
}

async function locked<T>(scope: string, action: () => Promise<T>): Promise<T> {
  if (!navigator.locks) throw new Error("Este navegador no permite proteger las operaciones entre pestañas. Usa un navegador actualizado en HTTPS o localhost.");
  return navigator.locks.request(`nomi-financial:${scope}`, { ifAvailable: true }, lock => {
    if (!lock) throw new Error("Hay otra pestaña confirmando una operación. Espera su resultado antes de continuar.");
    return action();
  });
}

async function send<T>(intent: FinancialIntent): Promise<T> {
  // Never replay a previous account's intent with the current account's cookies.
  const profile = await api<Profile>("/me");
  if (intentScope(profile) !== intent.scope) throw new Error("Inicia sesión con la cuenta que creó esta operación.");
  try {
    const response = await api<T>(intent.path, intent.body, intent.key);
    await remove(intent.scope);
    return response;
  } catch (error) {
    // Connection, session and upstream failures do not tell us whether a commit happened.
    if (error instanceof ApiError && [400, 404, 409, 422].includes(error.status)
      && !["OPERATION_IN_PROGRESS", "IDEMPOTENCY_KEY_CONFLICT"].includes(error.code)) await remove(intent.scope);
    throw error;
  }
}

export async function financialMutation<T>(scope: string, path: string, body: object): Promise<T> {
  return locked(scope, async () => {
    if (await pendingIntent(scope)) throw new Error("Tienes una operación pendiente de confirmar. Cierra este formulario y revísala antes de registrar otra.");
    const intent: FinancialIntent = { scope, path, body, key: crypto.randomUUID(), createdAt: new Date().toISOString() };
    await store("readwrite", value => value.add(intent));
    window.dispatchEvent(new Event(intentEvent));
    return send<T>(intent);
  });
}

export async function recoverIntent(scope: string): Promise<void> {
  await locked(scope, async () => {
    const intent = await pendingIntent(scope);
    if (intent) await send(intent);
  });
}
