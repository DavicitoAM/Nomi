# Glosario de dominio

## User

Identidad autenticable de Nomi. Responde “quién eres”.

## Workspace

Frontera lógica de propiedad de datos. Responde “a qué conjunto de datos estás accediendo”.

## Membership

Relación entre un User y un Workspace. En Core, el usuario creador tiene rol `owner`.

## Contact

Persona u organización con la que existe una relación económica. No tiene un rol financiero permanente.

## Commitment

Obligación económica declarada. Puede ser `receivable` (me deben) o `payable` (yo debo).

## Transaction

Movimiento que modifica el saldo de un Commitment. En Core: `payment` o `reversal`.

## Payment

Movimiento que reduce saldo.

## Reversal

Movimiento nuevo que deshace exactamente un Payment anterior sin borrar historial.

## Original amount

Monto base con el que nació el compromiso.

## Balance

Saldo pendiente actual. En Core cumple `0 <= balance <= original_amount`.

## Lifecycle status

Estado persistente del compromiso:

- `open`;
- `paid`;
- `cancelled`.

## Payment state

Estado derivado del saldo:

- `pending`;
- `partial`;
- `paid`.

## Timing state

Condición temporal derivada:

- `no_due_date`;
- `upcoming`;
- `due_soon`;
- `overdue`.

## Idempotency key

Identificador de una intención de escritura. Permite reintentar sin duplicar efecto.

## Version

Contador usado para bloqueo optimista en Commitment.

## Audit event

Registro de quién realizó una acción relevante y sobre qué entidad.

## Outbox event

Evento persistido en la misma transacción de negocio para trabajo asíncrono posterior.

## Soft delete

Marcado lógico de eliminación sin destruir inmediatamente la fila.

## Archive

Ocultar un Contact del uso normal sin destruir su historial.

## Cancel

Terminar una obligación restante sin fingir que fue pagada.

## Due date

Fecha de negocio sin hora. Su interpretación depende de `Workspace.timezone`.
