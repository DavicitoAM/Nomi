# ADR-0006 — Outbox transaccional

**Estado:** ACEPTADA

## Decisión
Persistir evento de integración en la misma transacción que el cambio de negocio.

## Motivo
Evitar el fallo: DB commit exitoso + mensaje/evento perdido.

## Consecuencias
- worker;
- reintentos;
- idempotencia de consumidores;
- limpieza/retención.

## Límite
Outbox no se usa para diferir la actualización de saldo: Payment y balance siguen siendo síncronos.
