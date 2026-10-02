# Modelo de errores

## Formato

Usar `application/problem+json`.

Ejemplo:

```json
{
  "type": "https://docs.nomi.app/problems/payment-exceeds-balance",
  "title": "El movimiento excede el saldo",
  "status": 422,
  "detail": "El abono no puede superar el saldo pendiente.",
  "instance": "/api/v1/commitments/...",
  "request_id": "req_..."
}
```

## Categorías

### 400

Forma/semántica general inválida.

### 401

No autenticado o sesión inválida/expirada.

### 403

Autenticado pero acción global explícitamente prohibida, cuando revelar recurso sea seguro.

### 404

Recurso inexistente o fuera del Workspace para evitar enumeración.

### 409

Conflictos de estado/concurrencia/idempotencia:

- `VERSION_CONFLICT`
- `IDEMPOTENCY_KEY_CONFLICT`
- `TRANSACTION_ALREADY_REVERSED`

### 422

Regla de negocio con payload válido:

- `PAYMENT_EXCEEDS_BALANCE`
- `INVALID_AMOUNT`
- `CONTACT_ARCHIVED`
- `COMMITMENT_NOT_OPEN`

## Códigos de dominio

Mantener un `code` estable en el detalle/extensión del Problem Details para que frontend no dependa del texto traducido.

## Mensajes

El usuario ve texto comprensible. Logs internos usan request_id y error code, no stack trace público.
