# UC-004 — RegisterPayment

## Objetivo

Registrar un abono/pago y reducir el saldo exactamente una vez.

## Endpoint conceptual

```http
POST /api/v1/commitments/{commitment_id}/transactions
Idempotency-Key: <uuid>
```

## Entrada

```json
{
  "type": "payment",
  "amount_minor": 250000,
  "occurred_at": "2026-10-02T17:00:00Z",
  "note": "Transferencia",
  "expected_version": 1
}
```

`expected_version` puede viajar en body/If-Match/otro contrato; la decisión HTTP exacta se cerrará con OpenAPI.

## Precondiciones

- sesión válida;
- Commitment pertenece al Workspace;
- lifecycle = `open`;
- amount > 0;
- amount <= balance;
- currency se deriva/valida;
- version coincide;
- idempotency key no conflictiva.

## Transacción

```text
BEGIN
  INSERT Transaction(payment)
  UPDATE Commitment
      balance = balance - amount
      lifecycle = paid si nuevo balance = 0; open en otro caso
      version = version + 1
  INSERT AuditEvent
  INSERT OutboxEvent(PaymentRegistered)
  si balance = 0:
      INSERT OutboxEvent(CommitmentFullyPaid)
  completar IdempotencyRecord
COMMIT
```

## Respuesta recomendada

```json
{
  "transaction": {
    "id": "...",
    "type": "payment",
    "amount_minor": 250000,
    "occurred_at": "..."
  },
  "commitment": {
    "id": "...",
    "balance_minor": 750000,
    "lifecycle_status": "open",
    "payment_state": "partial",
    "version": 2
  }
}
```

## Errores

- `COMMITMENT_NOT_FOUND`
- `COMMITMENT_NOT_OPEN`
- `INVALID_AMOUNT`
- `PAYMENT_EXCEEDS_BALANCE`
- `VERSION_CONFLICT`
- `IDEMPOTENCY_KEY_CONFLICT`

## Regla de atomicidad

Si falla Audit/Outbox dentro de la unidad transaccional, no debe quedar Payment sin balance ni balance sin Payment.

## Pruebas críticas

1. payment parcial;
2. payment exacto → paid;
3. payment mayor → rechazo;
4. doble request misma key → un movimiento;
5. dos dispositivos misma version → uno obtiene conflicto;
6. recurso de otro Workspace → 404;
7. fallo en insert de audit → rollback.
