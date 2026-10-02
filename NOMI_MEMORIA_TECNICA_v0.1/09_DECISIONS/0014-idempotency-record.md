# ADR-0014 — Registro genérico de idempotencia

**Estado:** ACEPTADA

## Decisión
Tabla IdempotencyRecord en lugar de columna exclusiva en Transaction.

## Clave
(workspace_id, operation, idempotency_key)

## request_hash
Permite distinguir reintento real de reutilización accidental de key con otro payload.

## Aplicación
CreateCommitment, RegisterPayment, ReverseTransaction y futuras escrituras financieras.
