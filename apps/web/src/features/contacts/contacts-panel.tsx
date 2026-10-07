"use client";
import { useEffect, useState } from "react";
import { useInfiniteQuery } from "@tanstack/react-query";
import { api, type Contact, type Page } from "@/lib/api";

export function ContactsPanel({ onSelect, onCreate }: { onSelect: (id: string) => void; onCreate: () => void }) {
  const [status, setStatus] = useState("active");
  const [search, setSearch] = useState("");
  const [query, setQuery] = useState("");
  useEffect(() => { const timer = setTimeout(() => setQuery(search), 200); return () => clearTimeout(timer); }, [search]);
  const contacts = useInfiniteQuery({ queryKey: ["contact-directory", status, query], initialPageParam: "", queryFn: ({ pageParam }) => api<Page<Contact>>(`/contacts?status=${status}&search=${encodeURIComponent(query)}&limit=30${pageParam ? `&cursor=${pageParam}` : ""}`), getNextPageParam: page => page.next_cursor ?? undefined });
  const rows = contacts.data?.pages.flatMap(p => p.items) ?? [];
  return <section aria-label="Tus contactos">
    <div className="list-toolbar"><div className="filter-tabs" role="group" aria-label="Estado de contactos">{[["active", "Activos"], ["archived", "Archivados"], ["all", "Todos"]].map(([value, label]) => <button key={value} aria-pressed={status === value} className={status === value ? "selected" : ""} onClick={() => setStatus(value)}>{label}</button>)}</div><label className="search-field"><input aria-label="Buscar contactos" value={search} onChange={e => setSearch(e.target.value)} maxLength={160} placeholder="Buscar por nombre" /></label></div>
    {contacts.isPending ? <p role="status">Cargando contactos…</p> : contacts.error ? <div role="alert" className="error-box">{contacts.error.message}<button className="text-button" onClick={() => contacts.refetch()}>Reintentar</button></div> : <div className="contacts-grid">
      {rows.map(c => <button type="button" className="person-card contact-button" key={c.id} onClick={() => onSelect(c.id)}><span className="contact-avatar" aria-hidden="true">{c.name.slice(0, 1)}</span><span className="eyebrow">{c.archived_at ? "ARCHIVADO" : "CONTACTO"}</span><h2>{c.name}</h2><p>{c.email || "Sin correo registrado"}</p><small>{c.phone || "Sin teléfono registrado"}</small><span className="text-button">Ver contacto</span></button>)}
      {!rows.length && <div className="empty-state"><h2>No hay contactos en esta lista.</h2><p>Cambia el filtro o agrega un contacto.</p><button className="secondary" onClick={onCreate}>Crear contacto</button></div>}
    </div>}
    {contacts.hasNextPage && <button className="load-more" disabled={contacts.isFetchingNextPage} onClick={() => contacts.fetchNextPage()}>Cargar más contactos</button>}
  </section>;
}
