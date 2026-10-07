"use client";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { api, ApiError, minorUnits, money, type Contact, type Commitment } from "@/lib/api";
import { financialMutation } from "@/lib/financial-intents";

const amount = z.string().refine(value => { try { minorUnits(value); return true; } catch { return false; } }, "Usa un monto positivo con hasta dos decimales.");
const commitmentSchema = z.object({ contact_id: z.string().min(1, "Elige un contacto."), direction: z.enum(["receivable", "payable"]), amount, concept: z.string().max(160), due_date: z.string() });
type CommitmentValues = z.infer<typeof commitmentSchema>;

export function ContactForm({ onSuccess, initial, onRefresh }: { onSuccess: (contact: Contact) => void; initial?: Contact; onRefresh?: () => Promise<unknown> }) {
  const [error, setError] = useState("");
  const [conflict, setConflict] = useState(false);
  const form = useForm<{ name: string; email: string; phone: string; notes: string }>({ defaultValues: { name: initial?.name ?? "", email: initial?.email ?? "", phone: initial?.phone ?? "", notes: initial?.notes ?? "" } });
  return <form onSubmit={form.handleSubmit(async values => {
    setError("");
    try { onSuccess(await api<Contact>(initial ? `/contacts/${initial.id}` : "/contacts", { name: values.name, email: values.email || null, phone: values.phone || null, notes: values.notes || null, ...(initial ? { expected_updated_at: initial.updated_at } : {}) }, undefined, initial ? "PATCH" : undefined)); }
    catch (e) { setError((e as Error).message); if (e instanceof ApiError && e.code === "VERSION_CONFLICT") setConflict(true); }
  })}>
    <p className="muted">Una persona o un negocio. Puedes tener pendientes por cobrar y por pagar con el mismo contacto.</p>
    <label>Nombre<input {...form.register("name")} required maxLength={160} autoFocus placeholder="Por ejemplo, Juan Pérez" /></label>
    <label>Correo <span className="optional">opcional</span><input {...form.register("email")} type="email" maxLength={254} placeholder="correo@ejemplo.com" /></label>
    <label>Teléfono <span className="optional">opcional</span><input {...form.register("phone")} type="tel" maxLength={40} placeholder="55 1234 5678" /></label>
    <label>Notas <span className="optional">opcional</span><textarea {...form.register("notes")} maxLength={2000} rows={3} /></label>
    {error && <p role="alert" className="error-box">{error}</p>}
    {conflict && onRefresh ? <button type="button" className="secondary full" onClick={onRefresh}>Actualizar contacto para revisar</button> : <button className="primary full" disabled={form.formState.isSubmitting}>{form.formState.isSubmitting ? "Guardando…" : "Guardar contacto"}</button>}
  </form>;
}

export function CommitmentForm({ scope, contacts, onSuccess, onContact }: { scope: string; contacts: Contact[]; onSuccess: () => void; onContact: (contact: Contact) => void }) {
  const [adding, setAdding] = useState(!contacts.length);
  const [error, setError] = useState("");
  const form = useForm<CommitmentValues>({ resolver: zodResolver(commitmentSchema), defaultValues: { contact_id: contacts[0]?.id ?? "", direction: "receivable", amount: "", concept: "", due_date: "" } });
  if (adding) return <><button className="text-button" onClick={() => setAdding(false)}>← Volver al pendiente</button><ContactForm onSuccess={contact => { onContact(contact); form.setValue("contact_id", contact.id); setAdding(false); }} /></>;
  return <form onSubmit={form.handleSubmit(async values => {
    setError("");
    const payload = { contact_id: values.contact_id, direction: values.direction, original_amount_minor: minorUnits(values.amount), currency_code: "MXN", concept: values.concept || null, due_date: values.due_date || null };
    try { await financialMutation(scope, "/commitments", payload); onSuccess(); }
    catch (e) { setError((e as Error).message); }
  })}>
    <div className="direction-choice"><label><input type="radio" value="receivable" {...form.register("direction")} /> Me deben</label><label><input type="radio" value="payable" {...form.register("direction")} /> Yo debo</label></div>
    <label>¿Con quién?<select {...form.register("contact_id")} required><option value="" disabled>Elige un contacto</option>{contacts.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}</select></label>
    <button className="text-button inline-add" type="button" onClick={() => setAdding(true)}>+ Crear un contacto</button>
    <label>Monto <span className="optional">MXN</span><input {...form.register("amount")} inputMode="decimal" placeholder="0.00" autoFocus required aria-invalid={!!form.formState.errors.amount} aria-describedby={form.formState.errors.amount ? "commitment-amount-error" : undefined} /></label>
    {form.formState.errors.amount && <small className="error" id="commitment-amount-error" role="alert">{form.formState.errors.amount.message}</small>}
    <label>Concepto <span className="optional">opcional</span><input {...form.register("concept")} maxLength={160} placeholder="Por ejemplo, diseño de página web" /></label>
    <label>Fecha de vencimiento <span className="optional">opcional</span><input {...form.register("due_date")} type="date" /></label>
    {error && <p role="alert" className="error-box">{error}</p>}
    <button className="primary full" disabled={form.formState.isSubmitting}>{form.formState.isSubmitting ? "Guardando…" : "Guardar pendiente"}</button>
  </form>;
}

export function PaymentForm({ scope, commitment, onSuccess, onRefresh }: { scope: string; commitment: Commitment; onSuccess: () => void; onRefresh: () => Promise<unknown> }) {
  const form = useForm<{ amount: string; note: string }>({ resolver: zodResolver(z.object({ amount, note: z.string().max(500) })), defaultValues: { amount: "", note: "" } });
  const [error, setError] = useState("");
  const [conflict, setConflict] = useState(false);
  return <form onSubmit={form.handleSubmit(async values => {
    setError("");
    const amountMinor = minorUnits(values.amount);
    if (amountMinor > commitment.balance_minor) { setError("El abono no puede superar el saldo pendiente."); return; }
    try { await financialMutation(scope, `/commitments/${commitment.id}/transactions`, { type: "payment", amount_minor: amountMinor, expected_version: commitment.version, occurred_at: new Date().toISOString(), note: values.note || null }); onSuccess(); }
    catch (e) { setError((e as Error).message); if (e instanceof ApiError && e.code === "VERSION_CONFLICT") setConflict(true); }
  })}>
    <div className="balance-callout"><span>Saldo pendiente</span><strong>{money(commitment.balance_minor)} <small>MXN</small></strong></div>
    <label>Monto del abono<input {...form.register("amount")} inputMode="decimal" placeholder="0.00" required autoFocus aria-invalid={!!form.formState.errors.amount} aria-describedby={form.formState.errors.amount ? "payment-amount-error" : undefined} /></label>
    {form.formState.errors.amount && <small className="error" id="payment-amount-error" role="alert">{form.formState.errors.amount.message}</small>}
    <label>Nota <span className="optional">opcional</span><input {...form.register("note")} maxLength={500} placeholder="Por ejemplo, transferencia" /></label>
    <p className="fine-print">Registra un pago que ya ocurrió. Este abono quedará guardado en el historial.</p>
    {error && <p role="alert" className="error-box">{error}</p>}
    {conflict ? <button type="button" className="primary full" onClick={async () => { await onRefresh(); setConflict(false); setError("Saldo actualizado. Revisa el monto y confirma nuevamente."); }}>Actualizar saldo para revisar</button> : <button className="primary full" disabled={form.formState.isSubmitting || commitment.lifecycle_status !== "open"}>{form.formState.isSubmitting ? "Registrando…" : "Confirmar abono"}</button>}
  </form>;
}

export function ReversalForm({ scope, commitment, payment, onSuccess, onRefresh, onBack }: { scope: string; commitment: Commitment; payment: { id: string; amount_minor: number }; onSuccess: () => Promise<void>; onRefresh: () => Promise<unknown>; onBack: () => void }) {
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [conflict, setConflict] = useState(false);
  return <form onSubmit={async event => {
    event.preventDefault(); setBusy(true); setError("");
    try { await financialMutation(scope, `/transactions/${payment.id}/reverse`, { expected_version: commitment.version, note: note || null }); await onSuccess(); }
    catch (e) { setError((e as Error).message); if (e instanceof ApiError && e.code === "VERSION_CONFLICT") setConflict(true); }
    finally { setBusy(false); }
  }}>
    <button className="text-button" type="button" disabled={busy} onClick={onBack}>← Volver al historial</button>
    <div className="balance-callout"><span>Importe a restaurar</span><strong>{money(payment.amount_minor)}</strong></div>
    <p>El saldo aumentará a {money(commitment.balance_minor + payment.amount_minor)}. El abono original se conservará y quedará vinculado a la reversión.</p>
    <label>Motivo <span className="optional">opcional</span><input value={note} onChange={event => setNote(event.target.value)} maxLength={500} autoFocus /></label>
    {error && <p role="alert" className="error-box">{error}</p>}
    {conflict ? <button type="button" className="secondary full" onClick={async () => { await onRefresh(); setConflict(false); setError("Revisa el saldo actualizado antes de confirmar."); }}>Actualizar saldo para revisar</button>
      : <button className="primary full" disabled={busy}>{busy ? "Revirtiendo…" : "Confirmar reversión"}</button>}
  </form>;
}
