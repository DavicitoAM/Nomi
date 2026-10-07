# ADR-0021 — Verificación, recuperación y entrega de correo durable

Estado: **ACEPTADA**, 2026-10-06. Alcance autorizado: cuentas, correo en segundo plano y pruebas de consistencia/persistencia.

## Contexto y decisiones

Completa Identity y ADR-0006/0020. Se conserva el registro atómico con sesión. La sesión opaca
continúa provisional hasta validar TLS/staging. No modificar dinero ni añadir otros módulos de producto.

- Tokens aleatorios de 32 bytes, tablas separadas EmailVerificationToken y PasswordResetToken,
  hash SHA-256, expiración UTC y used_at. Verificación: 24 h; reset: 30 min. Reenvío máximo una vez
  por minuto por usuario/propósito, con respuesta genérica. Reenviar invalida el enlace anterior.
- Para entrega asíncrona, la copia necesaria del secreto se cifra con Fernet en el registro auxiliar;
  la validación usa exclusivamente su hash. Outbox sólo guarda IDs. Tras entrega, uso, sustitución o
  descarte se borra la copia cifrada. No guardar tokens en logs, URL query, auditoría ni localStorage.
- Clave de entrega fuera de PostgreSQL: ACCOUNT_MAIL_KEY en entornos compartidos; archivo persistente
  .local/account-mail.key, generado una sola vez, sólo en desarrollo. API y worker comparten la clave.
  No rotarla hasta drenar envíos pendientes; si se pierde, solicitar enlaces nuevos. No inventar criptografía.
- URLs construidas desde APP_ORIGIN configurado, con token en fragmento. La UI retira el fragmento
  del historial al cargar y sólo consume el enlace al confirmar un POST; los scanners GET no lo gastan.
- Forgot devuelve el mismo 202 para cuenta ausente, deshabilitada, pendiente o activa; piso de latencia
  y límite por IP, sin enviar síncronamente. Reenvío de verificación requiere sesión + CSRF.
- Consumo, estado/cambio de contraseña, invalidación de tokens, revocación de todas las sesiones y
  auditoría se confirman juntos. Login/reset/emisión serializan por usuario para impedir sesiones
  creadas con una contraseña vieja después del reset. Reset no inicia sesión ni verifica email implícitamente.
- Worker PostgreSQL con SKIP LOCKED, reserva de 60 s, reintentos con espera creciente y máximo 8.
  Caída tras reservar recupera el evento al vencer la reserva. Fallo SMTP no revierte el negocio.
  Entrega al menos una vez; Message-ID estable. SMTP puede duplicar un correo tras caída entre envío
  y confirmación DB, pero contiene el mismo enlace de un uso; no prometer exactly-once de SMTP.
- Buzón local: archivos HTML/JSON en .local/mailbox, sin tráfico externo, deduplicados por evento.
  SMTP opcional exige TLS/configuración explícita. El backend de archivos se rechaza fuera de desarrollo.
  El buzón contiene enlaces sensibles de prueba; se excluye de Git y no se expone por la API pública.
- Se conservan eventos financieros sin consumidor. El worker procesa sólo eventos de correo conocidos.
  Eventos antiguos de registro se adaptan al preparar su entrega, con token persistido antes de enviar.

## Migración y seguridad

Nueva migración aditiva: dos tablas de tokens, email_verified_at/updated_at en User y datos de
reintento en Outbox. No reescribir migración inicial ni borrar datos. Usuarios active conservan acceso;
los timestamps históricos de verificación desconocidos quedan null. Downgrade elimina los nuevos
datos auxiliares y debe reservarse para pruebas; en entornos compartidos preferir forward-fix.

Referencias: [recuperación OWASP](https://cheatsheetseries.owasp.org/cheatsheets/Forgot_Password_Cheat_Sheet.html)
y [Fernet](https://cryptography.io/en/latest/fernet/). Se adoptan respuesta genérica, tokens seguros,
un solo uso y revocación de sesiones. La operación local no demuestra entregabilidad de un proveedor real.

## Evidencia requerida

Verificación/reenvío; caducidad/reutilización/propósito equivocado; reset y login con contraseña nueva;
sesiones revocadas incluso concurrentes; rollback de token/usuario/audit/outbox; worker concurrente,
fallo y reinicio; nueva conexión/proceso observa lo persistido. Migración hacia adelante con datos,
invariantes financieras intactas y E2E escritorio/móvil mediante buzón local.
