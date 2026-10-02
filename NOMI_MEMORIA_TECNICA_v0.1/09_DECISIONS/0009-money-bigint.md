# ADR-0009 — Dinero como BIGINT en unidad menor

**Estado:** ACEPTADA

## Decisión
Montos en enteros de unidad menor + currency_code.

## Ejemplo
`$1,250.50 MXN` → `125050`.

## Motivo
Evitar errores binarios de FLOAT y establecer redondeo explícito en límites.

## Consecuencia
Toda UI/API debe formatear/desformatear correctamente.
