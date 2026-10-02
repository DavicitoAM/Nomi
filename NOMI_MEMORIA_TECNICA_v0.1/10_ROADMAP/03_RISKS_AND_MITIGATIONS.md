# Riesgos y mitigaciones

| Riesgo | Impacto | Mitigación |
|---|---|---|
| producto demasiado genérico | baja adopción | usuario ancla y validación |
| sobreingeniería | retraso | Core estricto y ADR |
| offline prematuro | errores financieros | online primero, etapas |
| fuga entre workspaces | crítico | query scoped + tests BOLA |
| saldo inconsistente | crítico | UoW + constraints + reconciliation tests |
| doble Payment | alto | idempotencia |
| carrera de pagos | alto | optimistic locking |
| reversión ambigua | alto | self-FK UNIQUE |
| multimoneda temprana | complejidad | una moneda por Workspace |
| emails bloquean captura | mala UX | outbox/worker |
| telemetría filtra PII | privacidad | sanitización |
| proveedor de pago | lock-in | adapter + hosted billing |
| cambios DB peligrosos | pérdida | Alembic + backup + expand/contract |
| Contact duplicado | confusión | sugerencia, no UNIQUE incorrecto |
| cancelación confundida con pago | datos falsos | lifecycle separado; balance histórico |
| precio prematuro | mala conversión | investigación antes de fijar |
