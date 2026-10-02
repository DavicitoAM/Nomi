# ADR-0012 — Una moneda por Workspace en Core

**Estado:** ACEPTADA

## Contexto
Sumar MXN y USD exigiría tipos de cambio, fecha de conversión y reglas adicionales.

## Decisión
Core v0.1 limita cada Workspace a una moneda.

## Reglas
Commitment.currency = Workspace.currency.
Transaction.currency = Commitment.currency.

## Consecuencia
Cambio de moneda se bloquea tras existir actividad financiera.

## Revisión
Sólo cuando investigación valide necesidad multimoneda.
