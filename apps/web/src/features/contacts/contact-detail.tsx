"use client";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Dialog } from "@/components/dialog";
import { api, money, type Contact, type ContactDetail } from "@/lib/api";
import { ContactForm } from "@/features/commitments/forms";

export function ContactDialog({ id, onClose, onChange }: { id: string; onClose: () => void; onChange: () => Promise<void> }) {
  const detail = useQuery({ queryKey: ["contact-detail", id], queryFn: () => api<ContactDetail>(`/contacts/${id}`) });
  const [editing, setEditing] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const c = detail.data;
  async function done() { setEditing(false); setConfirming(false); setError(""); await detail.refetch(); await onChange(); }
  return <Dialog title={editing ? "Editar contacto" : c?.name ?? "Contacto"} onClose={onClose}>
    {detail.isPending ? <p role="status">Cargando contacto…</p> : detail.error ? <p role="alert">{detail.error.message}<button className="text-button" onClick={() => detail.refetch()}>Reintentar</button></p> : c && (editing
      ? <><button className="text-button" onClick={() => setEditing(false)}>← Volver al contacto</button><ContactForm key={c.updated_at} initial={c} onSuccess={done} onRefresh={() => detail.refetch()} /></>
      : <>
        <p className="muted">{c.archived_at ? "Contacto archivado" : "Contacto activo"}</p>
        <p>{c.email || "Sin correo registrado"}<br />{c.phone || "Sin teléfono registrado"}</p>
        {c.notes && <p className="preserve-lines">{c.notes}</p>}
        <div className="detail-facts"><span>Me debe<strong>{money(c.summary.receivable_balance_minor)}</strong></span><span>Le debo<strong>{money(c.summary.payable_balance_minor)}</strong></span><span>Pendientes activos<strong>{c.summary.active_commitments}</strong></span></div>
        <button className="secondary full" onClick={() => setEditing(true)}>Editar contacto</button>
        {!confirming ? <button className="text-button" onClick={() => setConfirming(true)}>{c.archived_at ? "Restaurar contacto" : "Archivar contacto"}</button>
          : <form onSubmit={async event => { event.preventDefault(); setBusy(true); setError(""); try { await api<Contact>(`/contacts/${id}/${c.archived_at ? "restore" : "archive"}`, { expected_updated_at: c.updated_at }); await done(); } catch (e) { setError((e as Error).message); } finally { setBusy(false); } }}>
            <p>{c.archived_at ? "Volverá a estar disponible para nuevos pendientes." : `Este contacto tiene ${c.summary.active_commitments} pendientes activos. Archivar conserva sus saldos e historial; impide crear nuevos pendientes hasta restaurarlo.`}</p>
            <button className="primary full" disabled={busy}>{busy ? "Guardando…" : c.archived_at ? "Confirmar restauración" : "Confirmar archivo"}</button>
            <button type="button" className="text-button" disabled={busy} onClick={() => setConfirming(false)}>Volver</button>
          </form>}
      </>)}
    {error && <div role="alert" className="error-box">{error}<button className="text-button" onClick={async () => { await detail.refetch(); setError(""); }}>Actualizar contacto</button></div>}
  </Dialog>;
}
