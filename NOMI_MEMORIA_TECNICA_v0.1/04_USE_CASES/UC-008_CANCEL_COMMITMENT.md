# UC-008 — CancelCommitment

## Objetivo

Indicar que la obligación restante deja de considerarse exigible dentro de Nomi sin fingir un pago.

## Precondiciones

- Commitment pertenece al Workspace;
- status = `open`;
- no soft-deleted;
- confirmación de usuario.

## Flujo

1. Cargar Commitment.
2. Confirmar abierto.
3. `lifecycle_status = cancelled`.
4. Incrementar version.
5. Audit `commitment.cancelled`.
6. Outbox `CommitmentCancelled`.
7. Commit.

## Saldo

No se fuerza a cero.

Ejemplo:

```text
Original 10,000
Payments  3,000
Balance   7,000
Status    cancelled
```

Reporting excluye el balance de totales activos.

## Pagos posteriores

No se permiten sobre `cancelled`.

Core v0.1 no implementa ReopenCancelledCommitment. Si se necesita, será un caso de uso explícito y auditado.

## Errores

- `COMMITMENT_NOT_FOUND`
- `COMMITMENT_NOT_OPEN`
- `VERSION_CONFLICT`
