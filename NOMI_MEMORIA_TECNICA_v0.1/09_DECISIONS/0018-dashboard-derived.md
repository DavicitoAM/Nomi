# ADR-0018 — Dashboard derivado

**Estado:** ACEPTADA

## Decisión
No crear tabla de Dashboard como segunda fuente en Core.

## Fuente
Commitments activos y estados derivados.

## Motivo
Evitar sincronización manual y discrepancias.

## Revisión
Si rendimiento real lo exige, crear read model/materialized view preservando PostgreSQL financiero como verdad.
