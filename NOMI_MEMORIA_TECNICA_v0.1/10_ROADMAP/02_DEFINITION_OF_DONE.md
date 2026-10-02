# Definition of Done

Una funcionalidad no está terminada sólo porque “funciona en mi máquina”.

## Checklist

- [ ] criterios de aceptación cumplidos;
- [ ] reglas de dominio cubiertas;
- [ ] pruebas unitarias/integración adecuadas;
- [ ] autorización por Workspace;
- [ ] no filtra secretos/PII en logs;
- [ ] OpenAPI actualizado;
- [ ] errores Problem Details;
- [ ] loading/error/empty states;
- [ ] funciona en viewport móvil;
- [ ] accesibilidad básica;
- [ ] idempotencia si es escritura financiera;
- [ ] concurrencia considerada si modifica saldo;
- [ ] audit/outbox si aplica;
- [ ] migración versionada;
- [ ] plan forward-fix para datos;
- [ ] telemetría útil;
- [ ] revisión de código;
- [ ] staging;
- [ ] smoke tests.

## Definition of Done financiera adicional

- [ ] saldo explicable por historial;
- [ ] no saldo negativo;
- [ ] no bypass de workspace;
- [ ] rollback probado;
- [ ] reintento seguro;
- [ ] operación concurrente probada.
