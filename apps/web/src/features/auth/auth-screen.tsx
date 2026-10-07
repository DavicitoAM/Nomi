"use client";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { ArrowUpRight, Check, MoveUpRight } from "lucide-react";
import { api, type Profile } from "@/lib/api";
import { ForgotPassword } from "./account-flows";

const schema = z.object({ display_name: z.string(), email: z.email("Revisa tu correo electrónico."), password: z.string().min(1, "Escribe tu contraseña.") });
type Values = z.infer<typeof schema>;

export function AuthScreen({ onSuccess }: { onSuccess: (profile: Profile) => void }) {
  const [login, setLogin] = useState(false);
  const [forgot, setForgot] = useState(false);
  const [error, setError] = useState("");
  const form = useForm<Values>({ resolver: zodResolver(schema), defaultValues: { display_name: "", email: "", password: "" } });
  async function submit(values: Values) {
    setError("");
    if (!login && (!values.display_name.trim() || values.password.length < 12)) { setError("Escribe tu nombre y una contraseña de al menos 12 caracteres."); return; }
    try {
      const body = login ? { email: values.email, password: values.password } : values;
      onSuccess(await api<Profile>(`/auth/${login ? "login" : "register"}`, body));
    } catch (e) { setError((e as Error).message); }
  }
  if (forgot) return <ForgotPassword onBack={() => { setForgot(false); setLogin(true); }} />;
  return <main className="auth-shell">
    <section className="auth-story">
      <a href="/" className="brand"><span className="brand-mark">n</span>nomi<span className="brand-dot">.</span></a>
      <div><span className="eyebrow light">MENOS PENDIENTES EN TU CABEZA</span><h1>Tu dinero pendiente.<br /><em>Todo en su lugar.</em></h1><p>Lo que te deben, lo que debes y cada abono.<br />La tranquilidad de tener las cuentas claras.</p>
        <div className="story-note"><span className="mini-icon"><MoveUpRight size={24} /></span><div><strong>La claridad empieza con un pendiente.</strong><small>Regístralo. Dale seguimiento. Sigue con tu día.</small></div></div>
      </div>
      <div className="auth-foot"><Check size={16} /> Simple desde el primer día <span>Hecho para tu ritmo</span></div>
    </section>
    <section className="auth-form-side">
      <span className="pill">UN POCO MÁS DE TRANQUILIDAD</span><h2>{login ? "Qué bueno verte." : "Empieza con claridad."}</h2><p className="muted">{login ? "Entra a tu espacio y retoma tus pendientes." : "Crea tu espacio personal. Nosotros ponemos el orden."}</p>
      <form onSubmit={form.handleSubmit(submit)}>
        {!login && <label>Tu nombre<input autoComplete="name" maxLength={120} {...form.register("display_name")} placeholder="¿Cómo te llamas?" required /></label>}
        <label>Correo electrónico<input type="email" autoComplete="email" {...form.register("email")} placeholder="tu@correo.com" required /></label>
        {form.formState.errors.email && <small className="error">{form.formState.errors.email.message}</small>}
        <label>Contraseña<input type="password" autoComplete={login ? "current-password" : "new-password"} minLength={login ? 1 : 12} maxLength={128} {...form.register("password")} placeholder={login ? "Tu contraseña" : "Al menos 12 caracteres"} required /></label>
        {error && <p role="alert" className="error-box">{error}</p>}
        <button className="primary full" disabled={form.formState.isSubmitting}>{form.formState.isSubmitting ? "Un momento…" : login ? "Entrar a mi espacio" : "Crear mi espacio"}<ArrowUpRight size={18} /></button>
      </form>
      {login && <button className="text-button" onClick={() => setForgot(true)}>Olvidé mi contraseña</button>}
      <p className="auth-switch">{login ? "¿Primera vez por aquí?" : "¿Ya tienes cuenta?"} <button className="text-button" onClick={() => { setLogin(!login); setError(""); }}>{login ? "Crea tu espacio" : "Inicia sesión"}</button></p>
      <p className="fine-print">Una moneda, un espacio personal.<br />Confirma tu correo para proteger el acceso a tu cuenta.</p>
    </section>
  </main>;
}
