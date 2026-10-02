---
name: nomi-api-contract
description: Diseña y revisa endpoints OpenAPI de Nomi con idempotencia, errores Problem Details y aislamiento por Workspace.
---

# API Contract Skill

## Proceso

1. Identificar use case, no sólo CRUD.
2. Elegir método y recurso.
3. Definir request schema.
4. No exponer campos de autoridad (`workspace_id`) si se derivan de sesión.
5. Definir success schema.
6. Definir Problem Details y error codes.
7. Marcar Idempotency-Key si cambia dinero.
8. Definir concurrency contract.
9. Añadir paginación por cursor en listas.
10. Generar/verificar OpenAPI.

## Convenciones

- `/api/v1`;
- UUID;
- ISO 8601;
- montos integer minor units;
- X-Request-ID;
- application/problem+json.

## Revisión

Una API correcta debe permitir al frontend manejar:
- loading;
- retry;
- conflict;
- empty;
- offline reconciliation.
