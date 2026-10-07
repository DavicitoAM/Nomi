"use client";
import { useEffect, useState } from "react";
import {
  intentEvent,
  pendingIntent,
  recoverIntent,
} from "@/lib/financial-intents";

export function PendingOperation({
  scope,
  onResolved,
}: {
  scope: string;
  onResolved: () => Promise<void>;
}) {
  const [pending, setPending] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => {
    let active = true;
    const check = () => {
      pendingIntent(scope)
        .then((value) => {
          if (active) { setPending(Boolean(value)); setError(""); }
        })
        .catch((e) => {
          if (active) setError((e as Error).message);
        });
    };
    check();
    window.addEventListener(intentEvent, check);
    window.addEventListener("focus", check);
    window.addEventListener("online", check);
    return () => {
      active = false;
      window.removeEventListener(intentEvent, check);
      window.removeEventListener("focus", check);
      window.removeEventListener("online", check);
    };
  }, [scope]);
  if (!pending && !error) return null;
  return (
    <aside className="error-box" aria-label="Operación pendiente">
      <strong>Revisa el estado de tu operación</strong>
      {pending && (
        <>
          <p>
            Hay un movimiento pendiente de confirmar. Recuperaremos su resultado
            con la misma clave; no registres otro para sustituirlo.
          </p>
          <button
            className="secondary"
            disabled={busy}
            onClick={async () => {
              setBusy(true);
              setError("");
              try {
                await recoverIntent(scope);
                await onResolved();
              } catch (e) {
                setError((e as Error).message);
                await onResolved();
              } finally {
                setBusy(false);
                try {
                  setPending(Boolean(await pendingIntent(scope)));
                } catch (e) {
                  setError((e as Error).message);
                }
              }
            }}
          >
            {busy ? "Consultando…" : "Revisar operación pendiente"}
          </button>
        </>
      )}
      {error && <p role="alert">{error}</p>}
    </aside>
  );
}
