"use client";
import { useEffect, useRef } from "react";
import { X } from "lucide-react";

export function Dialog({ title, onClose, children }: { title: string; onClose: () => void; children: React.ReactNode }) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => { const dialog = ref.current; dialog?.showModal(); return () => dialog?.close(); }, []);
  return <dialog ref={ref} onCancel={e => { e.preventDefault(); onClose(); }} aria-labelledby="dialog-title">
    <div className="dialog-head"><h2 id="dialog-title">{title}</h2><button className="icon-button" aria-label="Cerrar" onClick={onClose}><X size={20} /></button></div>
    {children}
  </dialog>;
}
