# UC-006 — ReverseTransaction

## Objetivo

Corregir un Payment erróneo sin editar ni borrar la historia.

## Endpoint

```http
POST /api/v1/transactions/{transaction_id}/reverse
Idempotency-Key: <uuid>
```

## Entrada

El cliente identifica el Payment original y, opcionalmente, una nota/motivo.

No envía libremente amount ni currency; el servidor los deriva.

## Precondiciones

- original existe en Workspace actual;
- original.type = `payment`;
- no existe una reversión previa;
- Commitment no está eliminado;
- idempotencia válida;
- version esperada si se expone al cliente.

## Flujo

1. Cargar Payment original mediante Commitment aislado por Workspace.
2. Confirmar que no está revertido.
3. Tomar `amount`, `currency`, `commitment_id`.
4. Crear Transaction `reversal` con `reversal_of_transaction_id = original.id`.
5. Sumar el amount al balance.
6. Si Commitment estaba `paid`, cambiarlo a `open`.
7. Incrementar version.
8. Audit.
9. Outbox `TransactionReversed`.
10. Commit.

## Restricción de DB

`reversal_of_transaction_id` es UNIQUE. Una carrera de dos reversiónes termina con una sola válida.

## Errores

- `TRANSACTION_NOT_FOUND`
- `TRANSACTION_NOT_REVERSIBLE`
- `TRANSACTION_ALREADY_REVERSED`
- `VERSION_CONFLICT`

## Ejemplo

```text
Original 10,000
T1 payment 2,500 → balance 7,500
T2 reversal(T1) 2,500 → balance 10,000
```

## Reapertura

Si:

```text
balance = 0
status = paid
```

y se revierte un Payment de 4,000:

```text
balance = 4,000
status = open
```
