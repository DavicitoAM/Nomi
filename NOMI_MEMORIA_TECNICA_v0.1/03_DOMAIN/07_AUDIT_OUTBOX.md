# Audit y Outbox

## AuditEvent

Objetivo: trazabilidad de acciones relevantes.

Campos base:

```text
id
workspace_id
actor_user_id?
action
entity_type
entity_id
metadata
created_at
```

Ejemplos de `action`:

- `user.registered`
- `contact.created`
- `contact.archived`
- `commitment.created`
- `commitment.cancelled`
- `transaction.payment_registered`
- `transaction.reversed`

## Qué NO es Audit

No es un log de depuración. Debe ser estable, consultable y semántico.

No guardar innecesariamente:

- contraseñas;
- tokens;
- cookies;
- cuerpo financiero completo;
- PII que no haga falta.

## OutboxEvent

Objetivo: garantizar que un efecto secundario no se pierda entre el commit de negocio y el worker.

Campos base:

```text
id
workspace_id
event_type
payload
occurred_at
processed_at?
attempts
```

## Patrón

```text
BEGIN
  cambio de negocio
  audit event
  outbox event
COMMIT

después:
worker → procesa outbox
```

Si el worker cae, el evento sigue persistido.

## Eventos iniciales

- `CommitmentCreated`
- `PaymentRegistered`
- `TransactionReversed`
- `CommitmentFullyPaid`
- `CommitmentCancelled`

## Regla

Un evento no sustituye una operación que necesita consistencia inmediata. Payment y actualización de saldo deben estar en la misma transacción; no se “eventualiza” el saldo.
