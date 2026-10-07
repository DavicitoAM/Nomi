"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { platform } from "@/lib/platform";

export function ConnectionNotice() {
  const [offline, setOffline] = useState(false);
  useEffect(() => { const update = () => setOffline(!navigator.onLine); update(); window.addEventListener("online", update); window.addEventListener("offline", update); return () => { window.removeEventListener("online", update); window.removeEventListener("offline", update); }; }, []);
  return offline ? <p className="error-box" role="status">Sin conexión. Los datos visibles pueden estar desactualizados. Cuando vuelva la conexión, revisa cualquier operación pendiente antes de registrar otra.</p> : null;
}

export function ExportButton() {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  return <div className="export-tools"><button type="button" className="text-button" disabled={busy} onClick={async () => {
    setBusy(true); setError("");
    try {
      const result = await api<object>("/exports/workspace", {});
      if (platform.saveExport) { await platform.saveExport(result); return; }
      const url = URL.createObjectURL(new Blob([JSON.stringify(result, null, 2)], { type: "application/json" }));
      const link = document.createElement("a"); link.href = url; link.download = "nomi-workspace.json"; document.body.appendChild(link); link.click(); link.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (e) { setError((e as Error).message); }
    finally { setBusy(false); }
  }}>{busy ? "Preparando archivo…" : "Exportar mis datos"}</button><small className="muted">Archivo JSON con contactos, pendientes y movimientos. Contiene datos privados. Hasta 10,000 registros / 10 MB.</small>{error && <p role="alert" className="error-box">{error}</p>}</div>;
}
