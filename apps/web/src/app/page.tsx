"use client";
import { useEffect, useState } from "react";
import { useInfiniteQuery, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowDownLeft, ArrowUpRight, ChevronRight, CircleCheck, Clock3, CalendarDays, LayoutGrid, LogOut, Plus, Search, Users, Wallet, X } from "lucide-react";
import { api, ApiError, dateLabel, money, type Commitment, type CommitmentListItem, type Contact, type Dashboard, type Page, type Profile, type Transaction } from "@/lib/api";
import { AuthScreen } from "@/features/auth/auth-screen";
import { AccountLinkScreen, VerificationNotice, VerificationRequired, type AccountLink } from "@/features/auth/account-flows";
import { CommitmentForm, ContactForm, PaymentForm, ReversalForm } from "@/features/commitments/forms";
import { intentScope } from "@/lib/financial-intents";
import { PendingOperation } from "@/features/commitments/pending-operation";
import { Dialog } from "@/components/dialog";
import { ContactDialog } from "@/features/contacts/contact-detail";
import { ContactsPanel } from "@/features/contacts/contacts-panel";
import { ManageCommitment } from "@/features/commitments/manage";
import { ConnectionNotice, ExportButton } from "@/features/account-tools";

function ErrorNotice({ error, retry }: { error: Error; retry: () => void }) {
  return <div role="alert" className="error-box">{error.message} <button className="text-button" onClick={retry}>Reintentar</button></div>;
}

export default function Home() {
  const client = useQueryClient();
  const [accountLink, setAccountLink] = useState<AccountLink | null>(null);
  useEffect(() => {
    const readLink = () => {
      const fragment = new URLSearchParams(window.location.hash.slice(1));
      const action = fragment.get("action"), token = fragment.get("token");
      if ((action === "verify" || action === "reset") && token) {
        setAccountLink({ action, token });
        window.history.replaceState(null, "", window.location.pathname);
      }
    };
    readLink(); window.addEventListener("hashchange", readLink);
    return () => window.removeEventListener("hashchange", readLink);
  }, []);
  const profile = useQuery({ queryKey: ["me"], queryFn: () => api<Profile>("/me"), staleTime: 60000 });
  useEffect(() => {
    const expire = () => { client.removeQueries({ predicate: query => query.queryKey[0] !== "me" }); client.setQueryData(["me"], null); };
    window.addEventListener("nomi-session-expired", expire);
    return () => window.removeEventListener("nomi-session-expired", expire);
  }, [client]);
  if (accountLink) return <AccountLinkScreen key={accountLink.token} link={accountLink} onDone={() => { setAccountLink(null); profile.refetch(); }} onReset={() => { client.removeQueries({ predicate: query => query.queryKey[0] !== "me" }); client.setQueryData(["me"], null); }} />;
  if (profile.isPending) return <main className="loading-screen"><span className="brand">nomi.</span><p role="status">Preparando tu espacio…</p></main>;
  if (profile.error && !(profile.error instanceof ApiError && profile.error.status === 401)) return <main className="loading-screen"><h1>Tu espacio estará aquí.</h1><ErrorNotice error={profile.error} retry={() => profile.refetch()} /></main>;
  if (!profile.data) return <AuthScreen onSuccess={value => { client.removeQueries({ predicate: query => query.queryKey[0] !== "me" }); client.setQueryData(["me"], value); }} />;
  if (!profile.data.can_operate) return <VerificationRequired profile={profile.data} onRefresh={() => profile.refetch()} onLogout={async () => { await api("/auth/logout", {}); client.setQueryData(["me"], null); }} />;
  return <Workspace key={profile.data.workspace.id} profile={profile.data} />;
}

function Workspace({ profile }: { profile: Profile }) {
  const scope = intentScope(profile);
  const client = useQueryClient();
  const [section, setSection] = useState("Resumen");
  const [filter, setFilter] = useState("all");
  const [search, setSearch] = useState("");
  const [querySearch, setQuerySearch] = useState("");
  useEffect(() => { const timer = setTimeout(() => setQuerySearch(search), 200); return () => clearTimeout(timer); }, [search]);
  const [modal, setModal] = useState<"commitment" | "contact" | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [selectedContact, setSelectedContact] = useState<string | null>(null);
  useEffect(() => { document.title = `${section} · Nomi`; }, [section]);
  const [toast, setToast] = useState("");
  const [logoutError, setLogoutError] = useState("");
  const contactsQuery = useInfiniteQuery({ queryKey: ["contacts"], initialPageParam: "", queryFn: ({ pageParam }) => api<Page<Contact>>(`/contacts?limit=100${pageParam ? `&cursor=${pageParam}` : ""}`), getNextPageParam: page => page.next_cursor ?? undefined });
  const contacts = contactsQuery.data?.pages.flatMap(p => p.items) ?? [];
  const commitmentsQuery = useInfiniteQuery({ queryKey: ["commitments", filter, querySearch], initialPageParam: "", queryFn: ({ pageParam }) => api<Page<CommitmentListItem>>(`/commitments?limit=30&filter=${filter}&search=${encodeURIComponent(querySearch)}${pageParam ? `&cursor=${pageParam}` : ""}`), getNextPageParam: page => page.next_cursor ?? undefined });
  const summary = useQuery({ queryKey: ["dashboard"], queryFn: () => api<Dashboard>("/dashboard/summary") });
  const commitments = commitmentsQuery.data?.pages.flatMap(p => p.items) ?? [];
  const names = new Map([...contacts.map(c => [c.id, c.name] as const), ...commitments.map(c => [c.contact_id, c.contact_name] as const)]);
  const filtered = commitments;
  useEffect(() => { if (toast) { const timer = setTimeout(() => setToast(""), 5000); return () => clearTimeout(timer); } }, [toast]);
  const refresh = async () => { await Promise.all([client.invalidateQueries({ queryKey: ["commitments"] }), client.invalidateQueries({ queryKey: ["dashboard"] }), client.invalidateQueries({ queryKey: ["detail"] }), client.invalidateQueries({ queryKey: ["history"] })]); };
  async function contactCreated(contact: Contact) {
    await client.invalidateQueries({ queryKey: ["contact-directory"] });
    client.setQueryData(["contacts"], (old: { pages: Page<Contact>[]; pageParams: string[] } | undefined) => ({ pages: old ? [{ ...old.pages[0], items: [...old.pages[0].items, contact] }, ...old.pages.slice(1)] : [{ items: [contact], next_cursor: null }], pageParams: old?.pageParams ?? [""] }));
  }

  function showFilter(value: string) { setSection("Pendientes"); setFilter(value); setSearch(""); }
  const navigation = [{ label: "Resumen", icon: LayoutGrid }, { label: "Pendientes", icon: Wallet }, { label: "Contactos", icon: Users }];
  return <div className="workspace">
    <a className="skip-link" href="#main-content">Ir al contenido</a>
    <header className="app-header"><div className="header-inner">
      <a href="/" className="brand" aria-label="Nomi, inicio"><span className="brand-mark">n</span>nomi<span className="brand-dot">.</span></a>
      <nav className="main-nav" aria-label="Navegación principal">{navigation.map(({ label, icon: Icon }) =>
        <button key={label} className={`nav-item ${section === label ? "active" : ""}`} aria-current={section === label ? "page" : undefined} onClick={() => setSection(label)}>
          <Icon size={19} aria-hidden="true" /><span>{label}</span>
        </button>
      )}</nav>
      <div className="user-block"><span className="avatar" aria-hidden="true">{profile.user.display_name.slice(0, 1).toUpperCase()}</span><div><strong>{profile.user.display_name}</strong><small>Espacio personal</small></div>
        <button title="Cerrar sesión" aria-label="Cerrar sesión" className="icon-button" onClick={async () => { try { await api("/auth/logout", {}); client.removeQueries({ predicate: query => query.queryKey[0] !== "me" }); client.setQueryData(["me"], null); } catch (e) { setLogoutError((e as Error).message); } }}><LogOut size={18} /></button>
      </div>
    </div></header>
    <main className="page-content" id="main-content" tabIndex={-1}><ConnectionNotice />
      <div className="page-heading"><div><span className="eyebrow">TU ESPACIO, EN ORDEN</span>
        <h1>{section === "Resumen" ? `Hola, ${profile.user.display_name.split(" ")[0]}.` : section === "Pendientes" ? "Tus pendientes." : "Tus contactos."}</h1>
        <p className="muted">{section === "Resumen" ? "Ten claro lo que te deben, lo que debes y qué sigue." : section === "Pendientes" ? "Cada compromiso y cada abono, en un solo lugar." : "Las personas y negocios con quienes llevas tus cuentas."}</p>
      </div><div className="heading-actions"><span className="today"><CalendarDays size={15} aria-hidden="true" />{new Intl.DateTimeFormat("es-MX", { day: "numeric", month: "long", timeZone: profile.workspace.timezone }).format(new Date())}</span><button className="primary" onClick={() => setModal(section === "Contactos" ? "contact" : "commitment")}><Plus size={18} aria-hidden="true" />{section === "Contactos" ? "Nuevo contacto" : "Registrar pendiente"}</button></div></div>
      {!profile.user.email_verified && <VerificationNotice onRefresh={() => client.invalidateQueries({ queryKey: ["me"] })} />}
      <PendingOperation scope={scope} onResolved={refresh} />
      {logoutError && <p className="error-box" role="alert">{logoutError}</p>}
      {section === "Resumen" && <section className="overview" aria-label="Resumen de saldos">
        {summary.error ? <ErrorNotice error={summary.error} retry={() => summary.refetch()} /> : <>
          <article className="money-card hero-stat"><div className="stat-label"><span className="stat-icon"><ArrowDownLeft size={23} /></span><span>Me deben<small>Dinero por cobrar</small></span><span className="currency">MXN</span></div><strong className="big-amount">{summary.data ? money(summary.data.receivable_balance_minor) : "…"}</strong><button className="card-link" onClick={() => showFilter("receivable")}>Ver por cobrar <ArrowUpRight size={17} /></button></article>
          <article className="money-card payable-stat"><div className="stat-label"><span className="stat-icon"><ArrowUpRight size={23} /></span><span>Yo debo<small>Dinero por pagar</small></span><span className="currency">MXN</span></div><strong className="big-amount">{summary.data ? money(summary.data.payable_balance_minor) : "…"}</strong><button className="card-link" onClick={() => showFilter("payable")}>Ver por pagar <ArrowUpRight size={17} /></button></article>
          <article className="attention-card"><h2>Para dar seguimiento</h2><button className="attention-row" onClick={() => showFilter("overdue")}><span className="attention-icon warm"><Clock3 size={18} /></span><span>Vencidos<small>Fecha límite pasada</small></span><strong>{summary.data ? money(summary.data.overdue_balance_minor) : "…"}</strong><ChevronRight size={15} /></button><button className="attention-row" onClick={() => showFilter("due_soon")}><span className="attention-icon"><CalendarDays size={18} /></span><span>Por vencer<small>Hoy y próximos 7 días</small></span><strong>{summary.data ? money(summary.data.due_soon_balance_minor) : "…"}</strong><ChevronRight size={15} /></button><p><span className="status-dot" />{summary.data?.active_commitments ?? "—"} {summary.data?.active_commitments === 1 ? "compromiso activo" : "compromisos activos"}</p></article>
        </>}
      </section>}
      {section !== "Contactos" ? <section className="list-panel" aria-labelledby="pending-title">
        <div className="panel-title"><div><span className="eyebrow">CADA SALDO TIENE UNA HISTORIA</span><h2 id="pending-title">{section === "Resumen" ? "Tus pendientes" : "Todos tus pendientes"}<span className="count-chip">{summary.data?.active_commitments ?? "—"} {summary.data?.active_commitments === 1 ? "activo" : "activos"}</span></h2></div><label className="search-field"><Search size={18} aria-hidden="true" /><input aria-label="Buscar pendientes" value={search} onChange={e => setSearch(e.target.value)} maxLength={160} placeholder="Buscar contacto o concepto" /></label></div>
        <div className="list-toolbar"><div className="filter-tabs" role="group" aria-label="Filtrar pendientes">{[["all", "Todos"], ["receivable", "Me deben"], ["payable", "Yo debo"], ["overdue", "Vencidos"], ["due_soon", "Por vencer"]].map(([value, label]) => <button key={value} aria-pressed={filter === value} onClick={() => setFilter(value)} className={filter === value ? "selected" : ""}>{label}</button>)}</div><span className="loaded-count">{filtered.length} en esta lista</span></div>
        {contactsQuery.error && <ErrorNotice error={contactsQuery.error} retry={() => contactsQuery.refetch()} />}
        {commitmentsQuery.isPending ? <p className="panel-message" role="status">Cargando tus pendientes…</p> : commitmentsQuery.error ? <ErrorNotice error={commitmentsQuery.error} retry={() => commitmentsQuery.refetch()} /> : filtered.length ? <div className="commitment-list">
          <div className="list-columns" aria-hidden="true"><span>CONTACTO Y CONCEPTO</span><span>VENCIMIENTO</span><span>ESTADO</span><span>SALDO PENDIENTE</span><span /></div>
          {filtered.map(c => <button className="commitment-row" key={c.id} onClick={() => setSelected(c.id)}><span className="contact-cell"><span className={`contact-avatar ${c.direction === "payable" ? "sand" : ""}`} aria-hidden="true">{(names.get(c.contact_id) ?? "C").slice(0, 1)}</span><span><strong>{names.get(c.contact_id) ?? "Contacto"}</strong><small>{c.concept || (c.direction === "receivable" ? "Dinero por cobrar" : "Dinero por pagar")}</small></span></span><span className="due-cell">{dateLabel(c.due_date)}</span><span className={`badge ${c.lifecycle_status === "paid" ? "paid" : c.timing_state === "overdue" ? "overdue" : ""}`}><span />{c.lifecycle_status === "cancelled" ? "Cancelado" : c.lifecycle_status === "paid" ? "Pagado" : c.timing_state === "overdue" ? "Vencido" : c.payment_state === "partial" ? "Abonado" : "Pendiente"}</span><span className="amount-cell"><strong>{money(c.balance_minor)}</strong><small>{c.direction === "receivable" ? "Me deben" : "Yo debo"}</small></span><ChevronRight size={17} aria-hidden="true" /></button>)}
        </div> : <div className="empty-state"><span className="empty-icon"><Wallet size={30} strokeWidth={1.5} /></span><h3>{(filter !== "all" || querySearch || summary.data?.active_commitments) ? "No hay coincidencias." : "Todo empieza con un pendiente."}</h3><p>{(filter !== "all" || querySearch || summary.data?.active_commitments) ? "Prueba otro filtro o término de búsqueda." : "Registra algo que te deban o tengas por pagar. Nosotros te ayudamos a seguir el saldo."}</p><button className="secondary" onClick={() => setModal("commitment")}><Plus size={17} />Registrar pendiente</button></div>}
        {commitmentsQuery.hasNextPage && <><p className="pagination-note">Hay más resultados para estos filtros. Carga la siguiente página para consultarlos.</p><button className="load-more" disabled={commitmentsQuery.isFetchingNextPage} onClick={() => commitmentsQuery.fetchNextPage()}>Cargar más pendientes</button></>}
        {contactsQuery.hasNextPage && <button className="load-more" disabled={contactsQuery.isFetchingNextPage} onClick={() => contactsQuery.fetchNextPage()}>Cargar más nombres de contactos</button>}
        <div className="panel-footer"><span><CircleCheck size={14} /> Cada abono queda en tu historial</span><span>Importes en MXN</span></div>
      </section> : <ContactsPanel onSelect={setSelectedContact} onCreate={() => setModal("contact")} />}
      <ExportButton /><footer className="page-footer"><span>Menos pendientes en tu cabeza.</span><span>nomi · Tu espacio personal</span></footer>
    </main>
    {toast && <div className="toast" role="status"><CircleCheck size={19} />{toast}<button aria-label="Cerrar aviso" onClick={() => setToast("")}><X size={18} /></button></div>}
    {modal && <Dialog title={modal === "contact" ? "Un nuevo contacto" : "Registra un pendiente"} onClose={() => setModal(null)}>{modal === "contact" ? <ContactForm onSuccess={contact => { contactCreated(contact); setModal(null); setToast("Contacto guardado."); }} /> : <>{contactsQuery.error && <ErrorNotice error={contactsQuery.error} retry={() => contactsQuery.refetch()} />}<CommitmentForm scope={scope} contacts={contacts} onContact={contactCreated} onSuccess={() => { setModal(null); refresh(); setToast("Tu pendiente ya está en orden."); }} />{contactsQuery.hasNextPage && <button className="text-button" onClick={() => contactsQuery.fetchNextPage()}>Cargar más contactos existentes</button>}</>}</Dialog>}
    {selectedContact && <ContactDialog id={selectedContact} onClose={() => setSelectedContact(null)} onChange={async () => { await Promise.all([client.invalidateQueries({ queryKey: ["contacts"] }), client.invalidateQueries({ queryKey: ["contact-directory"] }), refresh()]); setToast("Contacto actualizado."); }} />}
    {selected && <Detail scope={scope} id={selected} name={names.get(commitments.find(c => c.id === selected)?.contact_id ?? "") ?? "Contacto"} timezone={profile.workspace.timezone} onClose={() => setSelected(null)} onChange={async () => { await refresh(); setToast("Pendiente actualizado."); }} />}
  </div>;
}

function Detail({ scope, id, name, timezone, onClose, onChange }: { scope: string; id: string; name: string; timezone: string; onClose: () => void; onChange: () => Promise<void> }) {
  const [paying, setPaying] = useState(false);
  const [reversing, setReversing] = useState<Transaction | null>(null);
  const [managing, setManaging] = useState<"edit" | "cancel" | null>(null);
  const detail = useQuery({ queryKey: ["detail", id], queryFn: () => api<Commitment>(`/commitments/${id}`) });
  const history = useInfiniteQuery({ queryKey: ["history", id], initialPageParam: "", queryFn: ({ pageParam }) => api<Page<Transaction>>(`/commitments/${id}/transactions?limit=50${pageParam ? `&cursor=${pageParam}` : ""}`), getNextPageParam: page => page.next_cursor ?? undefined });
  const c = detail.data;
  const movements = history.data?.pages.flatMap(page => page.items) ?? [];
  const done = async () => { setPaying(false); setReversing(null); setManaging(null); await onChange(); };
  return <Dialog title={managing === "edit" ? "Editar pendiente" : managing === "cancel" ? "Cancelar pendiente" : reversing ? "Revertir abono" : paying ? "Registrar abono" : name} onClose={onClose}>
    {detail.isPending ? <p role="status">Cargando pendiente…</p> : detail.error ? <ErrorNotice error={detail.error} retry={() => detail.refetch()} /> : c && (
      managing ? <ManageCommitment scope={scope} commitment={c} cancel={managing === "cancel"} onBack={() => setManaging(null)} onRefresh={() => detail.refetch()} onSuccess={done} />
      : reversing ? <ReversalForm scope={scope} commitment={c} payment={reversing} onBack={() => setReversing(null)} onRefresh={() => detail.refetch()} onSuccess={done} />
      : paying ? <><button className="text-button" onClick={() => setPaying(false)}>← Volver al historial</button><PaymentForm scope={scope} commitment={c} onRefresh={() => detail.refetch()} onSuccess={done} /></>
      : <>
        <p className="muted">{c.concept || "Tu pendiente"} · {c.direction === "receivable" ? "Me deben" : "Yo debo"}</p>
        <div className="balance-callout"><span>Saldo pendiente</span><strong>{money(c.balance_minor)}</strong></div>
        <div className="detail-facts"><span>Original<strong>{money(c.original_amount_minor)}</strong></span><span>Abonado<strong>{money(c.original_amount_minor - c.balance_minor)}</strong></span><span>Vencimiento<strong>{dateLabel(c.due_date)}</strong></span></div>
        {c.lifecycle_status === "open" && <button className="primary full" onClick={() => setPaying(true)}><Plus size={17} />Registrar abono</button>}
        {c.notes && <p className="preserve-lines">{c.notes}</p>}
        {c.lifecycle_status === "cancelled" && <p className="error-box">Cancelado. El saldo se conserva como historial y no participa en los totales activos.</p>}
        <div className="detail-actions"><button className="text-button" onClick={() => setManaging("edit")}>Editar pendiente</button>{c.lifecycle_status === "open" && <button className="text-button" onClick={() => setManaging("cancel")}>Cancelar pendiente</button>}</div>
        <h3 className="history-title">Así va tu pendiente</h3>
        {history.isPending && <p role="status" className="muted">Cargando movimientos…</p>}
        <ol className="timeline"><li><span className="timeline-dot" /><div><strong>Pendiente creado</strong><small>Monto original</small></div><strong>{money(c.original_amount_minor)}</strong></li>
          {movements.map(t => <li key={t.id} id={`movement-${t.id}`}><span className="timeline-dot green" /><div>
            <strong>{t.type === "payment" ? (t.reversed_by_transaction_id ? "Abono revertido" : "Abono registrado") : "Reversión registrada"}</strong>
            <small>{new Intl.DateTimeFormat("es-MX", { dateStyle: "medium", timeStyle: "short", timeZone: timezone }).format(new Date(t.occurred_at))}</small>
            {t.note && <small>{t.note}</small>}
            {t.reversal_of_transaction_id && <small>Corrige el abono {t.reversal_of_transaction_id.slice(0, 8)}</small>}
            {t.type === "payment" && !t.reversed_by_transaction_id && c.lifecycle_status !== "cancelled" && <button className="text-button" onClick={() => setReversing(t)}>Revertir abono</button>}
          </div><strong>{t.type === "payment" ? "−" : "+"}{money(t.amount_minor)}</strong></li>)}
        </ol>
        {history.error && <ErrorNotice error={history.error} retry={() => history.refetch()} />}
        {history.hasNextPage && <button className="load-more" onClick={() => history.fetchNextPage()}>Ver más movimientos</button>}
      </>
    )}
  </Dialog>;
}
