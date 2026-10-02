# Commitment

## Definición

Commitment representa una obligación económica pendiente entre un Workspace y un Contact.

No es una factura, una transferencia ni un movimiento bancario.

## Campos Core

```text
id
workspace_id
contact_id

direction
original_amount_minor
balance_minor
currency_code

concept?
notes?
due_date?

lifecycle_status
version

created_at
updated_at
deleted_at?
```

## Direction

- `receivable`: me deben.
- `payable`: yo debo.

La interfaz puede mostrar lenguaje humano; el dominio usa valores estables.

## Montos

```text
original_amount_minor > 0
0 <= balance_minor <= original_amount_minor
```

Dinero se almacena en unidad menor:

```text
$10,000.00 MXN → 1000000
```

## Ciclo de vida persistido

- `open`
- `paid`
- `cancelled`

### Open

Obligación activa. Debe tener balance > 0.

### Paid

Obligación liquidada. Debe tener balance = 0.

### Cancelled

La parte pendiente deja de ser exigible en Nomi. Puede conservar balance histórico > 0 y queda excluida de agregados activos.

## Payment state derivado

```text
PENDING:
balance == original

PARTIAL:
0 < balance < original

PAID:
balance == 0
```

## Timing state derivado

- `no_due_date`
- `upcoming`
- `due_soon`
- `overdue`

`due_soon` usa inicialmente la ventana de siete días del dashboard.

`overdue` requiere:

```text
lifecycle = open
balance > 0
due_date < today(workspace.timezone)
```

## Edición

Antes de movimientos puede permitirse editar monto/dirección/moneda bajo reglas.

Después de existir movimientos:

- concepto, notas y fecha pueden editarse;
- monto original, dirección y moneda quedan bloqueados en Core;
- correcciones financieras se hacen mediante movimientos/reversión, no reescribiendo historia.

## Cancelación

Cancelar no es pagar.

Ejemplo:

```text
Original: 10,000
Pagado:    3,000
Balance:   7,000
Status: cancelled
```

Los 3,000 pagados siguen existiendo; los 7,000 restantes dejan de participar como obligación activa.

## Version

`version` inicia en 1 y aumenta con cambios financieros para control optimista.
