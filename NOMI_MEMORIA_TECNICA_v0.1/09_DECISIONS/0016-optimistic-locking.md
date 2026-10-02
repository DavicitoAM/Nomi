# ADR-0016 — Optimistic locking

**Estado:** ACEPTADA

## Decisión
Commitment incluye integer `version`.

Las escrituras usan expected version.

## Razón
Evitar que dos dispositivos calculen sobre el mismo saldo viejo.

## Resultado
0 filas actualizadas → VERSION_CONFLICT.

## UX
Recargar estado y pedir reconfirmación; no fusionar Payment financiero silenciosamente.
