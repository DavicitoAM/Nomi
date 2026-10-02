# ADR-0013 — Ciclo persistido y estados derivados

**Estado:** ACEPTADA

## Problema
“Partial” y “Overdue” pueden coexistir. Una sola columna status mezcla dimensiones.

## Decisión
Persistir:
- open
- paid
- cancelled

Derivar:
- payment_state: pending/partial/paid
- timing_state: no_due_date/upcoming/due_soon/overdue

## Beneficio
Evita estados mutuamente excluyentes artificiales y datos temporales desincronizados.
