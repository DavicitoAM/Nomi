# ADR-0007 — OpenTelemetry

**Estado:** ACEPTADA

## Decisión
Instrumentación vendor-neutral mediante OpenTelemetry/OTLP.

## Motivos
Correlación y libertad de proveedor.

## Riesgos
Costo y fuga de datos.

## Mitigación
Sampling, control de cardinalidad y sanitización estricta.
