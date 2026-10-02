"use client";
import { useRef, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { api, ApiError, minorUnits, money, type Contact, type Commitment } from "@/lib/api";

const amount = z.string().refine(value => { try { minorUnits(value); return true; } catch { return false; } }, "Usa un monto positivo con hasta dos decimales.");
const commitmentSchema = z.object({ contact_id: z.string().min(1, "Elige un contacto."), direction: z.enum(["receivable", "payable"]), amount, concept: z.string().max(160), due_date: z.string() });
type CommitmentValues = z.infer<typeof commitmentSchema>;

export function ContactForm({ onSuccess }: { onSuccess: (contact: Contact) => void }) {
  const [error, setError] = useState("");
  const form = useForm<{ name: string; email: string; phone: string }>({ defaultValues: { name: "", email: "", phone: "" } });
  return <form onSubmit={form.handleSubmit(async values => {
    setError("");
    try { onSuccess(await api<Contact>("/contacts", { name: values.name, email: values.email || null, phone: values.phone || null })); }
    catch (e) { setError((e as Error).message); }
  })}>
    <p className="muted">Una persona o un negocio. Puedes tener pendientes por cobrar y por pagar con el mismo contacto.</p>
    <label>Nombre<input {...form.register("name")} required maxLength={160} autoFocus placeholder="Por ejemplo, Juan Pérez" /></label>
    <label>Correo <span className="optional">opcional</span><input {...form.register("email")} type="email" maxLength={254} placeholder="correo@ejemplo.com" /></label>
    <label>Teléfono <span className="optional">opcional</span><input {...form.register("phone")} type="tel" maxLength={40} placeholder="55 1234 5678" /></label>
    {error && <p role="alert" className="error-box">{error}</p>}
    <button className="primary full" disabled={form.formState.isSubmitting}>{form.formState.isSubmitting ? "Guardando…" : "Guardar contacto"}</button>
  </form>;
}

export function CommitmentForm({ contacts, onSuccess, onContact }: { contacts: Contact[]; onSuccess: () => void; onContact: (contact: Contact) => void }) {
  const [adding, setAdding] = useState(!contacts.length);
  const [error, setError] = useState("");
  const intent = useRef<{ signature: string; key: string } | null>(null);
  const form = useForm<CommitmentValues>({ resolver: zodResolver(commitmentSchema), defaultValues: { contact_id: contacts[0]?.id ?? "", direction: "receivable", amount: "", concept: "", due_date: "" } });
  if (adding) return <><button className="text-button" onClick={() => setAdding(false)}>← Volver al pendiente</button><ContactForm onSuccess={contact => { onContact(contact); form.setValue("contact_id", contact.id); setAdding(false); }} /></>;
  return <form onSubmit={form.handleSubmit(async values => {
    setError("");
    const payload = { contact_id: values.contact_id, direction: values.direction, original_amount_minor: minorUnits(values.amount), currency_code: "MXN", concept: values.concept || null, due_date: values.due_date || null };
    const signature = JSON.stringify(payload);
    if (intent.current?.signature !== signature) intent.current = { signature, key: crypto.randomUUID() };
    try { await api("/commitments", payload, intent.current.key); onSuccess(); }
    catch (e) { setError((e as Error).message); }
  })}>
    <div className="direction-choice"><label><input type="radio" value="receivable" {...form.register("direction")} /> Me deben</label><label><input type="radio" value="payable" {...form.register("direction")} /> Yo debo</label></div>
    <label>¿Con quién?<select {...form.register("contact_id")} required><option value="" disabled>Elige un contacto</option>{contacts.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}</select></label>
    <button className="text-button inline-add" type="button" onClick={() => setAdding(true)}>+ Crear un contacto</button>
    <label>Monto <span className="optional">MXN</span><input {...form.register("amount")} inputMode="decimal" placeholder="0.00" autoFocus required /></label>
    {form.formState.errors.amount && <small className="error">{form.formState.errors.amount.message}</small>}
    <label>Concepto <span className="optional">opcional</span><input {...form.register("concept")} maxLength={160} placeholder="Por ejemplo, diseño de página web" /></label>
    <label>Fecha de vencimiento <span className="optional">opcional</span><input {...form.register("due_date")} type="date" /></label>
    {error && <p role="alert" className="error-box">{error}</p>}
    <button className="primary full" disabled={form.formState.isSubmitting}>{form.formState.isSubmitting ? "Guardando…" : "Guardar pendiente"}</button>
  </form>;
}

export function PaymentForm({ commitment, onSuccess, onRefresh }: { commitment: Commitment; onSuccess: () => void; onRefresh: () => Promise<unknown> }) {
  const form = useForm<{ amount: string; note: string }>({ resolver: zodResolver(z.object({ amount, note: z.string().max(500) })), defaultValues: { amount: "", note: "" } });
  const [error, setError] = useState("");
  const [conflict, setConflict] = useState(false);
  const intent = useRef<{ signature: string; key: string; payload: object } | null>(null);
  return <form onSubmit={form.handleSubmit(async values => {
    setError("");
    const amountMinor = minorUnits(values.amount);
    if (amountMinor > commitment.balance_minor) { setError("El abono no puede superar el saldo pendiente."); return; }
    const signature = JSON.stringify([values, commitment.version]);
    if (intent.current?.signature !== signature) intent.current = { signature, key: crypto.randomUUID(), payload: { type: "payment", amount_minor: amountMinor, expected_version: commitment.version, occurred_at: new Date().toISOString(), note: values.note || null } };
    try { await api(`/commitments/${commitment.id}/transactions`, intent.current.payload, intent.current.key); onSuccess(); }
    catch (e) { setError((e as Error).message); if (e instanceof ApiError && e.code === "VERSION_CONFLICT") setConflict(true); }
  })}>
    <div className="balance-callout"><span>Saldo pendiente</span><strong>{money(commitment.balance_minor)} <small>MXN</small></strong></div>
    <label>Monto del abono<input {...form.register("amount")} inputMode="decimal" placeholder="0.00" required autoFocus /></label>
    {form.formState.errors.amount && <small className="error">{form.formState.errors.amount.message}</small>}
    <label>Nota <span className="optional">opcional</span><input {...form.register("note")} maxLength={500} placeholder="Por ejemplo, transferencia" /></label>
    <p className="fine-print">Registra un pago que ya ocurrió. Este abono quedará guardado en el historial.</p>
    {error && <p role="alert" className="error-box">{error}</p>}
    {conflict ? <button type="button" className="primary full" onClick={async () => { await onRefresh(); intent.current = null; setConflict(false); setError("Saldo actualizado. Revisa el monto y confirma nuevamente."); }}>Actualizar saldo para revisar</button> : <button className="primary full" disabled={form.formState.isSubmitting || commitment.lifecycle_status !== "open"}>{form.formState.isSubmitting ? "Registrando…" : "Confirmar abono"}</button>}
  </form>;
}
