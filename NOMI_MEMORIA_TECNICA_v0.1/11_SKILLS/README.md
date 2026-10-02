# Skills de desarrollo de Nomi

Estas skills son guías operativas reutilizables para personas o asistentes de desarrollo. No son librerías de runtime. Su propósito es mantener consistencia con esta memoria técnica.

Cada `SKILL.md` define:

- cuándo usarla;
- qué información necesita;
- proceso;
- criterios de salida;
- guardrails específicos de Nomi.

## Skills

1. `architecture-review` — revisar cambios contra límites de módulos y ADR.
2. `fastapi-use-case` — implementar un caso de uso backend.
3. `postgresql-migration` — diseñar/revisar migraciones e integridad.
4. `api-contract` — diseñar OpenAPI/Problem Details.
5. `security-review` — revisión de auth, workspace, secretos, CSRF/IDOR.
6. `testing-financial-core` — tests críticos e invariantes.
7. `pwa-offline-sync` — diseñar colas y conflictos offline.
8. `adr-c4-maintenance` — actualizar decisiones/diagramas/documentación.
9. `domain-change` — introducir un cambio al dominio sin romper trazabilidad.

Estas skills deben leerse junto con los documentos de arquitectura, no sustituirlos.
