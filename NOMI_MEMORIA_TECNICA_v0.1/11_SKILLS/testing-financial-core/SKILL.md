---
name: nomi-testing-financial-core
description: Diseña pruebas de dominio, integración y concurrencia para saldos, pagos, reversiones e idempotencia.
---

# Testing Financial Core Skill

## Suite mínima

### Domain
- pending/partial/paid;
- due states;
- cancel;
- reversal.

### DB
- constraints de amount;
- balance;
- lifecycle;
- reversal unique;
- FKs.

### Use case
- payment parcial;
- payment total;
- overpayment;
- paid commitment;
- cancelled commitment.

### Idempotency
- retry mismo hash;
- key reutilizada con hash distinto.

### Concurrencia
- dos payments misma version;
- doble reversal.

### Security
- otro Workspace.

### Atomicidad
Inyectar fallo entre pasos y demostrar rollback.

## Propiedad fundamental

Para cualquier secuencia válida de Payment/Reversal:

```text
0 <= balance <= original_amount
```

y el saldo debe ser explicable por el historial efectivo.
