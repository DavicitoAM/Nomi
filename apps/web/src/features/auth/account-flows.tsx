"use client";
import { useState, type ReactNode } from "react";
import { api, type Profile } from "@/lib/api";

export type AccountLink = { action: "verify" | "reset"; token: string };
function AccountPanel({ title, children }: { title: string; children: ReactNode }) {
  return <main className="account-screen"><section className="account-panel"><a href="/" className="brand">nomi.</a><h1>{title}</h1>{children}</section></main>;
}

export function ForgotPassword({ onBack }: { onBack: () => void }) {
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  return <AccountPanel title="Recupera tu acceso"><p className="muted">Te enviaremos un enlace para elegir una contraseña nueva.</p>
    <form onSubmit={async event => {
      event.preventDefault(); setBusy(true); setError("");
      try { const result = await api<{ message: string }>("/auth/password/forgot", { email }); setMessage(result.message); }
      catch (e) { setError((e as Error).message); }
      finally { setBusy(false); }
    }}><label>Correo electrónico<input type="email" value={email} onChange={event => setEmail(event.target.value)} autoComplete="email" maxLength={254} required autoFocus /></label>
      {error && <p className="error-box" role="alert">{error}</p>}{message && <p role="status">{message}</p>}
      <button className="primary full" disabled={busy}>{busy ? "Solicitando…" : "Enviar enlace de recuperación"}</button>
    </form><button className="text-button" onClick={onBack}>Volver al inicio de sesión</button></AccountPanel>;
}

export function AccountLinkScreen({ link, onDone, onReset }: { link: AccountLink; onDone: () => void; onReset: () => void }) {
  const [password, setPassword] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [busy, setBusy] = useState(false);
  const reset = link.action === "reset";
  return <AccountPanel title={reset ? "Elige una contraseña nueva" : "Confirma tu correo"}>
    {success ? <><p role="status">{success}</p><button className="primary full" onClick={onDone}>{reset ? "Ir al inicio de sesión" : "Continuar a Nomi"}</button></>
      : <form onSubmit={async event => {
        event.preventDefault(); setError("");
        if (reset && password !== confirmation) { setError("Las contraseñas no coinciden."); return; }
        setBusy(true);
        try {
          const result = await api<{ message: string }>(reset ? "/auth/password/reset" : "/auth/email/verify", reset ? { token: link.token, password } : { token: link.token });
          setSuccess(result.message); setPassword(""); setConfirmation(""); if (reset) onReset();
        } catch (e) { setError((e as Error).message); }
        finally { setBusy(false); }
      }}><p className="muted">{reset ? "Usa al menos 12 caracteres. Al guardar se cerrarán tus sesiones anteriores." : "Confirma para activar el acceso a tu espacio. Este enlace sólo puede utilizarse una vez."}</p>
        {reset && <><label>Nueva contraseña<input type="password" value={password} onChange={event => setPassword(event.target.value)} minLength={12} maxLength={128} autoComplete="new-password" required autoFocus /></label>
          <label>Repite la contraseña<input type="password" value={confirmation} onChange={event => setConfirmation(event.target.value)} minLength={12} maxLength={128} autoComplete="new-password" required /></label></>}
        {error && <p className="error-box" role="alert">{error}</p>}
        <button className="primary full" disabled={busy}>{busy ? "Confirmando…" : reset ? "Guardar nueva contraseña" : "Confirmar correo"}</button>
        <button className="text-button" type="button" onClick={onDone}>Volver al inicio</button>
      </form>}</AccountPanel>;
}

export function VerificationNotice({ onRefresh }: { onRefresh: () => Promise<unknown> }) {
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  return <aside className="verification-notice" aria-label="Verificación de correo"><div><strong>Verifica tu correo</strong><p>Revisa el enlace que enviamos para confirmar tu cuenta.</p></div>
    <div><button className="secondary" disabled={busy} onClick={async () => {
      setBusy(true); setError("");
      try { const result = await api<{ message: string }>("/auth/email/resend", {}); setMessage(result.message); }
      catch (e) { setError((e as Error).message); }
      finally { setBusy(false); }
    }}>{busy ? "Solicitando…" : "Reenviar verificación"}</button>
    <button className="text-button" onClick={async () => { try { await onRefresh(); } catch (e) { setError((e as Error).message); } }}>Ya verifiqué mi correo</button></div>
    {message && <p role="status">{message}</p>}{error && <p role="alert" className="error">{error}</p>}</aside>;
}

export function VerificationRequired({ profile, onRefresh, onLogout }: { profile: Profile; onRefresh: () => Promise<unknown>; onLogout: () => Promise<void> }) {
  const [error, setError] = useState("");
  return <AccountPanel title="Confirma tu cuenta para continuar"><p>Tu espacio está listo, {profile.user.display_name}. Confirma tu correo para comenzar.</p>
    <VerificationNotice onRefresh={onRefresh} />{error && <p role="alert">{error}</p>}
    <button className="text-button" onClick={async () => { try { await onLogout(); } catch (e) { setError((e as Error).message); } }}>Cerrar sesión</button></AccountPanel>;
}
