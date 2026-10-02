# Plan de implementación

## Milestone 0 — Documentación congelable

Entregables:

- dominio Core;
- casos de uso;
- ERD;
- constraints;
- ADR;
- API preliminar;
- pruebas críticas.

## Milestone 1 — Foundation

- monorepo;
- tooling;
- Docker local;
- PostgreSQL;
- Alembic;
- FastAPI skeleton;
- Next.js skeleton;
- config por ambiente;
- CI básico;
- logging/request id.

## Milestone 2 — Identity + Workspace

- User;
- Session;
- RegisterUser;
- login/logout;
- `/me`;
- Workspace/Membership;
- password reset/verificación.

## Milestone 3 — Contacts

- CRUD controlado;
- archive/restore;
- list/search;
- tests de aislamiento.

## Milestone 4 — Commitments

- Create;
- Get/List;
- Edit reglas no financieras;
- cancel;
- estados derivados;
- Dashboard query inicial.

## Milestone 5 — Transactions

- RegisterPayment;
- ReverseTransaction;
- optimistic lock;
- idempotency;
- audit/outbox;
- tests concurrentes.

## Milestone 6 — Vertical slice web

```text
registro
→ dashboard vacío
→ contacto
→ compromiso
→ payment
→ historial
→ dashboard actualizado
```

## Milestone 7 — Hardening Core

- autorización negativa;
- CSRF;
- rate limiting;
- CSP;
- observabilidad;
- backup restore;
- rendimiento;
- accesibilidad.

## Milestone 8 — PWA/offline lectura

- install;
- shell;
- cache;
- IndexedDB read.

## Milestone 9 — Offline writes

Gradual:

1. Contact;
2. Commitment;
3. Payment.

## Milestone 10 — Reminders/export

Worker, outbox processing, email, CSV.

## Milestone 11 — Beta

20–40 usuarios, soporte, métricas, entrevistas y corrección de fricción.

## Milestone 12 — Monetización

Sólo después de validar valor.
