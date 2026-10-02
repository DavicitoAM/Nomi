# Estrategia de pruebas

## Prioridad

Probar reglas y riesgos, no perseguir cobertura porcentual vacía.

## Unitarias

Dominio puro:

- payment state;
- timing state;
- Payment;
- Reversal;
- cancelación;
- validación de montos;
- reglas de edición.

## Integración

Con PostgreSQL real/efímero:

- repositories;
- constraints;
- UoW;
- Alembic;
- idempotency;
- optimistic locking;
- outbox.

## Contrato

OpenAPI:

- schemas;
- códigos;
- Problem Details;
- cliente generado.

## E2E

Vertical slice:

```text
register
→ create contact
→ create commitment
→ payment
→ dashboard
→ reversal
```

## Seguridad

- IDOR/BOLA;
- CSRF;
- session revocation;
- password reset;
- rate limit;
- no secrets en responses/logs.

## Casos críticos obligatorios

- dos payments concurrentes;
- mismo request repetido;
- payment > balance;
- reversal duplicado;
- timezone;
- otro workspace;
- sync offline duplicado;
- rollback parcial.

## Accesibilidad

Automática + revisión manual.

## Rendimiento

Medir especialmente:

- dashboard;
- listados;
- history por Contact;
- escritura Payment.

## Test de invariantes

Además de ejemplos, usar property-based tests donde aporte valor:

```text
para cualquier saldo válido
payment <= balance
→ nuevo saldo >= 0
```
