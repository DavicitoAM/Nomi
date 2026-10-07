# Cuentas, correo y validación de persistencia

Fecha: 2026-10-06. Implementación local de ADR-0021; no despliegue de producción.

## Funciones

- Registro conserva usuario/Workspace/OWNER/sesión/audit/outbox en un commit e incorpora token de verificación.
- Verificar correo con enlace de un uso y 24 horas; reenviar desde el aviso de cuenta, con intervalo de un minuto.
- Olvidé mi contraseña responde siempre con mensaje genérico; enlace de 30 minutos.
- Restablecer cambia el hash Argon2id, invalida enlaces previos y revoca todas las sesiones en una transacción.
- Notificación de cambio de contraseña sin secretos. El correo no verifica automáticamente una cuenta pendiente.
- Perfil incluye `can_operate` para presentar el bloqueo de verificación fuera de desarrollo; backend siempre autoriza.

Endpoints nuevos: POST `/api/v1/auth/email/verify`, `/auth/email/resend`,
`/auth/password/forgot` y `/auth/password/reset` (todos bajo `/api/v1`).
Enlaces usan fragmento y confirmación explícita; abrir un enlace no consume el token.

## Entrega durable

Worker `python -m app.worker`: PostgreSQL, reserva de 60 segundos, SKIP LOCKED, máximo 8 intentos,
espera creciente entre fallos. Los correos pendientes sobreviven al reinicio. El worker procesa solamente
verificación, reset y aviso de contraseña cambiada; los eventos financieros se conservan para consumidores futuros.

El token se valida por hash. La copia para entrega usa Fernet y clave separada de la DB; se elimina al
confirmar envío, invalidar/consumir el token o detectar caducidad, incluso si se agotaron reintentos.
Los errores persistidos son códigos genéricos, sin datos de proveedor, email ni token.

SMTP puede repetir un correo si cae el proceso después de enviarlo y antes del commit de confirmación.
Se repite el mismo enlace y Message-ID; no produce dos cambios de contraseña ni dos verificaciones.
El buzón de archivos se deduplica por ID de evento. No se promete exactly-once de un proveedor externo.

## Probar manualmente

1. Iniciar `scripts/dev.ps1`: API, web, worker y buzón local.
2. Crear cuenta en http://localhost:3000.
3. Abrir http://localhost:8025, seleccionar el correo y «Continuar en Nomi».
4. Confirmar correo; el aviso desaparece al actualizar el perfil.
5. Crear contacto/compromiso/abono y anotar el saldo.
6. Cerrar sesión → Inicia sesión → Olvidé mi contraseña; solicitar el enlace.
7. Abrir el correo de recuperación, guardar una contraseña nueva y entrar de nuevo.
8. Comprobar saldo/historial iguales; contraseña anterior, enlaces reutilizados y sesiones previas se rechazan.

El buzón escucha exclusivamente en loopback, comprueba Host y no se inicia fuera de development/file.
Sus HTML/JSON están en `.local/mailbox`, ignorado por Git. Contienen enlaces de prueba sensibles.
No usar el buzón local ni compartir esos archivos como un servicio público.

## Configuración y operación

Desarrollo usa MAIL_BACKEND=file y clave persistente `.local/account-mail.key`, generada una vez.
No eliminar la clave mientras existan envíos cifrados pendientes. API y worker deben compartirla.
En entornos compartidos: ACCOUNT_MAIL_KEY desde gestor de secretos, APP_ORIGIN HTTPS,
COOKIE_SECURE=true y MAIL_BACKEND=smtp; configurar SMTP_HOST/PORT/FROM/USERNAME/PASSWORD.
El adaptador exige STARTTLS con validación de certificado y timeout de 10 segundos.
No se configuró ni se envió a un proveedor externo durante esta entrega.

Procesamiento acotado: `python -m app.worker --once --limit 100`.
Tras resolver una avería: `python -m app.worker --once --retry-failed` reabre intentos agotados.
No extiende la vigencia del token: ante caducidad, el usuario solicita un enlace nuevo.

Consulta operativa sin PII:

```sql
SELECT event_type, count(*) AS pending, max(attempts) AS max_attempts
FROM outbox_events
WHERE processed_at IS NULL
  AND event_type IN ('EmailVerificationRequested','PasswordResetRequested','PasswordChanged')
GROUP BY event_type;
```

## Evidencia automatizada

Resultado local: **88 pruebas de backend y 8 E2E aprobadas**. Build de producción,
TypeScript y Ruff aprobados; Alembic sin diferencias pendientes entre modelos y esquema.
Tras el ajuste final del puerto de entrega, se repitieron las 25 pruebas de cuentas y correo: aprobadas.
Permanece un aviso de deprecación del adaptador HTTPX de Starlette; no hay fallos de pruebas.

Suite: `apps/api/tests/test_account_lifecycle.py`, más regresiones financieras anteriores.
E2E: `tests/e2e/account.spec.ts` y `tests/e2e/core.spec.ts`.

| Dimensión | Evidencia |
| --- | --- |
| Funcionamiento | Verificación/reenvío, recuperación, contraseña nueva y expiración; UI escritorio/móvil. |
| Seguridad | Propósito equivocado, reutilización, cuenta deshabilitada, respuesta genérica, CSRF/origen, límites por IP y sesión revocada. |
| Concurrencia | Dos consumos del mismo enlace: uno confirma; carrera login/reset: ninguna sesión con contraseña vieja queda válida; dos workers no reclaman el mismo evento simultáneamente. |
| Atomicidad | Fallos inyectados de audit/outbox revierten consumo, cambio de contraseña y revocación. Fallar al emitir no deja token huérfano. |
| Persistencia | Nuevo proceso de API consume un token persistido; conexión nueva ve contraseña, sesión y saldo coherentes. Nuevo proceso worker retoma reserva vencida tras caída posterior al envío y conserva el mismo correo/enlace. |
| Migraciones | Base desechable nomi_test recorre esquema anterior → nuevo con usuarios y pagos existentes; conserva credenciales y saldos. |
| Base local existente | Antes/después de la migración se compararon counts y SHA-256 de los registros anteriores de diez tablas; sin diferencias inesperadas. Evidencia privada: `.local/account-migration-evidence.json`. |
| Entrega | Fallo/reintento, máximo de intentos, reproceso manual, descarte de enlaces vencidos/usados y limpieza de secretos; SMTP simulado comprueba TLS y Message-ID estable. |

Estas pruebas demuestran persistencia entre conexiones y procesos y conservación al migrar.
El ensayo posterior de [operación y recuperación](OPERATIONS_VALIDATION.md) ya valida restauración
de backup cifrado, caída del proceso PostgreSQL y TLS local. No simula pérdida eléctrica, corrupción
de disco ni failover. Staging, TLS público, respaldos del proveedor y entregabilidad real siguen pendientes.
