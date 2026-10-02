# Failure & Edge Case Pass

## Objetivo

Probar que el diseño no sólo funciona en happy path.

| Escenario | Resultado esperado |
|---|---|
| email duplicado | UNIQUE + error controlado |
| sesión ausente/expirada | 401, sin cambios |
| recurso de otro workspace | 404 |
| Contact archivado | no crear nuevo Commitment |
| doble CreateCommitment | idempotencia, uno |
| doble Payment | idempotencia, uno |
| misma key/payload distinto | conflicto |
| Payment > balance | 422, saldo intacto |
| Payment = balance | paid |
| Payment sobre paid | rechazo |
| dos Payments misma version | uno gana, otro VERSION_CONFLICT |
| Reverse dos veces | una reversión; UNIQUE impide segunda |
| Reverse Payment que dejó paid | Commitment vuelve a open |
| Cancel con Payments previos | conservar historia y balance histórico |
| Payment sobre cancelled | rechazo |
| due_date pasada | overdue derivado |
| paid con due_date pasada | no overdue actual |
| due_date null | no_due_date |
| cambio timezone | timestamps no se reescriben |
| fallo Audit dentro UoW | rollback completo |
| proveedor email caído | operación financiera permanece |
| Dashboard caído | verdad financiera no cambia |
| sesión expira al guardar | 401; no Transaction |

## Doble pago concurrente

Estado:

```text
balance = 1000
version = 4
```

A intenta 700; B intenta 500.

A actualiza con `WHERE version = 4` y deja version 5.

B actualiza con `WHERE version = 4`; affected rows = 0 → `VERSION_CONFLICT`.

Nunca llega a balance negativo.

## Misma idempotency key

```text
key ABC + hash H1 → ejecutar
key ABC + hash H1 → devolver resultado previo
key ABC + hash H2 → IDEMPOTENCY_KEY_CONFLICT
```

## Fallos secundarios

Correo, push, analítica y exportación no forman parte del commit de Payment. Fallan y reintentan por worker/outbox sin revertir el dinero registrado.
