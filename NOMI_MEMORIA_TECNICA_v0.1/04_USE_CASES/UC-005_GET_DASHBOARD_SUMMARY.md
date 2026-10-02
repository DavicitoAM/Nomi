# UC-005 — GetDashboardSummary

## Tipo

Query de lectura.

## Objetivo

Mostrar rápidamente la posición pendiente del Workspace.

## Endpoint

```http
GET /api/v1/dashboard/summary
```

## Precondición

Sesión y Membership válidas.

## Cálculos

Sólo compromisos:

```text
workspace_id = current
deleted_at IS NULL
lifecycle_status = open
```

### Receivable

SUM(balance) donde direction = `receivable`.

### Payable

SUM(balance) donde direction = `payable`.

### Overdue

SUM(balance) donde due_date < today(workspace.timezone).

### Due soon

SUM(balance) donde:

```text
today <= due_date <= today + 7 days
```

y sigue abierto.

## Respuesta conceptual

```json
{
  "currency_code": "MXN",
  "receivable_balance_minor": 750000,
  "payable_balance_minor": 0,
  "overdue_balance_minor": 0,
  "due_soon_balance_minor": 750000,
  "active_commitments": 1
}
```

## Regla

No existe una tabla `dashboard` que se actualice manualmente en Core.

## Estado vacío

Debe responder ceros correctamente, no error:

```json
{
  "receivable_balance_minor": 0,
  "payable_balance_minor": 0,
  "overdue_balance_minor": 0,
  "due_soon_balance_minor": 0,
  "active_commitments": 0
}
```

La UI convierte eso en un empty state orientado a “Registrar pendiente”.

## Pruebas

- paid excluido;
- cancelled excluido;
- otro Workspace excluido;
- sin due_date no overdue;
- fecha límite hoy no es overdue;
- timezone define today.
