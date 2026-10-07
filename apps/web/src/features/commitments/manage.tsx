"use client";
import { useState } from "react";
import { api, ApiError, money, type Commitment } from "@/lib/api";
import { financialMutation } from "@/lib/financial-intents";

export function ManageCommitment({ scope, commitment: c, cancel, onBack, onRefresh, onSuccess }: { scope: string; commitment: Commitment; cancel: boolean; onBack: () => void; onRefresh: () => Promise<unknown>; onSuccess: () => Promise<void> }) {
  const [concept, setConcept] = useState(c.concept ?? "");
  const [notes, setNotes] = useState(c.notes ?? "");
  const [dueDate, setDueDate] = useState(c.due_date ?? "");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [conflict, setConflict] = useState(false);
  return <form onSubmit={async event => {
    event.preventDefault(); setBusy(true); setError("");
    try {
      if (cancel) await financialMutation(scope, `/commitments/${c.id}/cancel`, { expected_version: c.version });
      else await api(`/commitments/${c.id}`, { expected_version: c.version, concept: concept || null, notes: notes || null, due_date: dueDate || null }, undefined, "PATCH");
      await onSuccess();
    } catch (e) { setError((e as Error).message); if (e instanceof ApiError && e.code === "VERSION_CONFLICT") setConflict(true); }
    finally { setBusy(false); }
  }}>
    <button type="button" className="text-button" disabled={busy} onClick={onBack}>← Volver al historial</button>
    {cancel ? <><p>El saldo de <strong>{money(c.balance_minor)}</strong> dejará de aparecer en los totales activos.</p><p>Se conservarán el saldo y todos los movimientos. Cancelar no registra un pago. Esta versión no permite reabrir un pendiente cancelado.</p></> : <>
      <label>Concepto<input value={concept} onChange={e => setConcept(e.target.value)} maxLength={160} autoFocus /></label>
      <label>Notas<textarea value={notes} onChange={e => setNotes(e.target.value)} maxLength={2000} rows={3} /></label>
      <label>Fecha de vencimiento<input type="date" value={dueDate} onChange={e => setDueDate(e.target.value)} /></label>
      <p className="fine-print">El monto, la moneda y la dirección permanecen iguales. Para corregir abonos utiliza una reversión.</p>
    </>}
    {error && <p role="alert" className="error-box">{error}</p>}
    {conflict ? <button className="secondary full" type="button" onClick={async () => { await onRefresh(); onBack(); }}>Actualizar y revisar el pendiente</button>
      : <button className="primary full" disabled={busy}>{busy ? "Guardando…" : cancel ? "Confirmar cancelación" : "Guardar cambios"}</button>}
  </form>;
}
