"use client";
import { useEffect, useId, useRef, type KeyboardEvent } from "react";
import { X } from "lucide-react";

export function Dialog({ title, onClose, children }: { title: string; onClose: () => void; children: React.ReactNode }) {
  const ref = useRef<HTMLDialogElement>(null);
  const titleId = useId();
  useEffect(() => { const previous = document.activeElement as HTMLElement | null; const dialog = ref.current; dialog?.showModal(); return () => { dialog?.close(); if (previous?.isConnected) previous.focus(); }; }, []);
  const keepFocusInside = (event: KeyboardEvent<HTMLDialogElement>) => {
    if (event.key !== "Tab") return;
    const controls = [...event.currentTarget.querySelectorAll<HTMLElement>("a[href], button, input, select, textarea, [tabindex], [contenteditable=true]")]
      .filter(element => element.tabIndex >= 0 && !element.matches(":disabled") && !element.closest("[inert]") && element.getClientRects().length > 0);
    const first = controls[0], last = controls.at(-1);
    if (event.shiftKey && document.activeElement === first && last) { event.preventDefault(); last.focus(); }
    else if (!event.shiftKey && document.activeElement === last && first) { event.preventDefault(); first.focus(); }
  };
  return <dialog ref={ref} onKeyDown={keepFocusInside} onCancel={e => { e.preventDefault(); onClose(); }} aria-labelledby={titleId}>
    <div className="dialog-head"><h2 id={titleId}>{title}</h2><button type="button" className="icon-button" aria-label="Cerrar" onClick={onClose}><X size={20} /></button></div>
    {children}
  </dialog>;
}
