---
name: nomi-fastapi-use-case
description: Implementa casos de uso FastAPI manteniendo dominio, aplicación, infraestructura y API separados.
---

# FastAPI Use Case Skill

## Usar cuando

Se implementa un command/query nuevo.

## Flujo

1. Definir DTO/command de aplicación.
2. Definir errores de dominio.
3. Implementar regla pura en domain cuando aplique.
4. Definir puertos Repository/UoW necesarios.
5. Implementar use case sin dependencias HTTP.
6. Implementar adapters SQLAlchemy.
7. Añadir route FastAPI.
8. Mapear errores a Problem Details.
9. Actualizar OpenAPI.
10. Tests unitarios + integración + autorización.

## Para escrituras financieras

Obligatorio revisar:

- current Workspace;
- Idempotency-Key;
- expected version;
- UoW;
- AuditEvent;
- OutboxEvent;
- rollback.

## Anti-patrones

No:
- lógica de saldo en route;
- ORM model como response público;
- `workspace_id` confiado desde body;
- envío de email en la transacción de request;
- `except Exception: return 400`.

## Done

La feature cumple Definition of Done y tiene test de otro Workspace.
