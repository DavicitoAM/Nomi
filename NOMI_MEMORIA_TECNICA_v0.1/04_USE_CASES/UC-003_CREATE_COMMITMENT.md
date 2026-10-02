# UC-003 — CreateCommitment

## Actor

Usuario autenticado.

## Objetivo

Crear una obligación por cobrar o por pagar.

## Endpoint conceptual

```http
POST /api/v1/commitments
Idempotency-Key: <uuid>
```

## Entrada

```json
{
  "contact_id": "...",
  "direction": "receivable",
  "original_amount_minor": 1000000,
  "currency_code": "MXN",
  "concept": "Diseño de página web",
  "due_date": "2026-10-20",
  "notes": null
}
```

## Precondiciones

- Contact existe en Workspace actual;
- Contact no archivado;
- amount > 0;
- direction válida;
- currency = Workspace.currency;
- idempotency key válida.

## Flujo

1. Auth context.
2. Reservar/consultar idempotency record.
3. Cargar Contact por `(id, workspace_id)`.
4. Validar reglas.
5. Iniciar transacción.
6. Crear Commitment:
   - original = amount;
   - balance = amount;
   - status = open;
   - version = 1.
7. AuditEvent `commitment.created`.
8. OutboxEvent `CommitmentCreated`.
9. Completar IdempotencyRecord.
10. Commit.
11. Responder Commitment.

## Resultado

```json
{
  "id": "...",
  "direction": "receivable",
  "original_amount_minor": 1000000,
  "balance_minor": 1000000,
  "currency_code": "MXN",
  "lifecycle_status": "open",
  "payment_state": "pending",
  "version": 1
}
```

`payment_state` es calculado.

## Errores

- `CONTACT_NOT_FOUND`
- `CONTACT_ARCHIVED`
- `INVALID_AMOUNT`
- `INVALID_DIRECTION`
- `CURRENCY_MISMATCH`
- `IDEMPOTENCY_KEY_CONFLICT`

## Idempotencia

Misma key + mismo request → mismo resultado.

Misma key + request distinto → conflicto.

## Pruebas

- balance inicial = original;
- no crea con Contact de otro Workspace;
- no crea con 0/negativo;
- reintento no duplica;
- Audit + Outbox existen sólo si Commitment existe.
