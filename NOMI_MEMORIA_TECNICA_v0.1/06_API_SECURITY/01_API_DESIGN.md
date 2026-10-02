# Diseño de API

## Convenciones

- Base: `/api/v1`.
- JSON UTF-8.
- UUID para identificadores.
- `TIMESTAMPTZ` serializado ISO 8601 UTC.
- `due_date` como `YYYY-MM-DD`.
- montos como enteros en unidad menor.
- paginación por cursor.
- errores `application/problem+json`.
- `X-Request-ID` para correlación.
- `Idempotency-Key` en escrituras financieras.
- OpenAPI 3.1 como contrato.

## Recursos Core

```text
POST   /api/v1/auth/register
POST   /api/v1/auth/login
POST   /api/v1/auth/logout
POST   /api/v1/auth/password/forgot
POST   /api/v1/auth/password/reset

GET    /api/v1/me
PATCH  /api/v1/me
DELETE /api/v1/me

GET    /api/v1/contacts
POST   /api/v1/contacts
GET    /api/v1/contacts/{contact_id}
PATCH  /api/v1/contacts/{contact_id}
POST   /api/v1/contacts/{contact_id}/archive
POST   /api/v1/contacts/{contact_id}/restore
GET    /api/v1/contacts/{contact_id}/summary

GET    /api/v1/commitments
POST   /api/v1/commitments
GET    /api/v1/commitments/{commitment_id}
PATCH  /api/v1/commitments/{commitment_id}
POST   /api/v1/commitments/{commitment_id}/cancel

POST   /api/v1/commitments/{commitment_id}/transactions
GET    /api/v1/commitments/{commitment_id}/transactions
POST   /api/v1/transactions/{transaction_id}/reverse

GET    /api/v1/dashboard/summary
```

Los endpoints `/archive`, `/restore` y `/cancel` hacen explícita la intención. Si se prefiere PATCH, el ADR/API contract debe cambiarlo de forma consciente.

## Commands vs Queries

Commands cambian estado:

- register;
- create contact;
- create commitment;
- payment;
- reversal;
- cancel.

Queries no cambian estado:

- me;
- list contacts;
- summary;
- dashboard.

## Respuestas

El API devuelve DTOs, no modelos ORM.

## Crear Payment

Respuesta recomendada incluye Transaction + Commitment actualizado para evitar round-trip adicional.

## Versionado

`/api/v1` protege cambios incompatibles mayores. No crear `/v2` por cambios aditivos normales.

## Cliente frontend

Generar tipos/cliente a partir de OpenAPI cuando el contrato se estabilice. No mantener manualmente dos copias divergentes de schemas.
