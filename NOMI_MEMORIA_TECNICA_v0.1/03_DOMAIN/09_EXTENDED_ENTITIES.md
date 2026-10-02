# Entidades extendidas del MVP y futuro

Este documento cubre entidades que forman parte del diseño maestro pero no son todas necesarias para la primera migración Core.

## Reminder — PLANIFICADA para MVP

```text
id
commitment_id
channel
scheduled_for
status
attempts
sent_at?
created_at
```

Responsabilidad: programar avisos para el propio usuario.

No puede bloquear la captura financiera.

Estados sugeridos: `scheduled`, `processing`, `sent`, `failed`, `cancelled`.

## NotificationPreference — PLANIFICADA

```text
id
user_id
channel
enabled
settings JSON
```

Responsabilidad: configuración del usuario para correo/push/in-app.

Evitar meter lógica arbitraria en `settings`; sólo usar JSON para parámetros realmente variables.

## Subscription — POST-CORE

```text
id
workspace_id
provider_customer_id
provider_subscription_id
plan_code
status
current_period_end
```

La suscripción pertenece a Workspace.

No almacenar tarjeta. El proveedor hospedado maneja checkout/portal.

## IdempotencyRecord — ACEPTADA Core

```text
id
workspace_id
operation
idempotency_key
request_hash
resource_type?
resource_id?
http_status?
created_at
expires_at?
```

UNIQUE:

```text
(workspace_id, operation, idempotency_key)
```

## Session — PROVISIONAL Core

Ver `02_IDENTITY.md`. Persistida en PostgreSQL inicialmente; Redis no se añade sólo por anticipación.

## Verification/Reset Tokens

Entidades auxiliares de seguridad con token hasheado, expiración y uso único.
