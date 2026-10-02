# ADR-0015 — Reversal mediante self-FK UNIQUE

**Estado:** ACEPTADA

## Problema
`reversed_at` no indica qué fila representa la reversión y duplica verdad.

## Decisión
Transaction.reversal_of_transaction_id → Transaction.id.

La columna:
- nullable;
- FK RESTRICT;
- UNIQUE.

## Efectos
- Payment: reversal_of NULL.
- Reversal: reversal_of obligatorio.
- sólo una reversión por Payment.

`reversed_at` se elimina como fuente persistida; la fecha de la fila reversal explica cuándo ocurrió.
