# Límites de módulos

## `identity`

Responsable de:

- User;
- credenciales;
- sesiones;
- verificación de email;
- recuperación de contraseña;
- estados de cuenta.

No es responsable de contactos, dinero ni permisos de recursos específicos.

## `workspaces`

Responsable de:

- Workspace;
- Membership;
- preferencias estructurales;
- resolución del workspace activo;
- propiedad lógica.

No autentica contraseñas y no modifica saldos.

## `contacts`

Responsable de:

- alta/edición;
- archivo/restauración;
- datos descriptivos.

No guarda saldo como fuente de verdad.

## `commitments`

Responsable de:

- crear obligación;
- dirección;
- monto original;
- saldo;
- fecha;
- ciclo de vida;
- condiciones derivadas.

No envía correos ni procesa pagos externos.

## `transactions`

Responsable de:

- Payment;
- Reversal;
- explicación de cambios de saldo.

No borra movimientos históricos.

## `reporting`

Responsable de:

- dashboard;
- agregados por contacto;
- vistas de actividad;
- exportaciones.

Es de lectura/consulta por defecto. No corrige saldo.

## `audit`

Responsable de eventos auditables de negocio/seguridad.

No sustituye logs operativos.

## `reminders`

Responsable de programación, estado y entrega de avisos.

No bloquea operaciones financieras si un proveedor falla.

## `billing`

Responsable de planes y suscripción futura.

No almacena datos completos de tarjeta.

## `worker`

Ejecuta efectos secundarios:

- recordatorios;
- correo;
- exportaciones;
- procesamiento outbox.

No inventa cambios financieros.

## Matriz de comunicación

| Origen | Destino | Mecanismo | Ejemplo |
|---|---|---|---|
| identity | workspaces | caso de uso transaccional | registro crea workspace |
| contacts | commitments | referencia validada | crear compromiso |
| transactions | commitments | caso de uso/UoW | pago modifica saldo |
| commitments | audit | escritura coordinada | CommitmentCreated |
| transactions | outbox | escritura coordinada | PaymentRegistered |
| outbox | reminders | worker | cancelar aviso tras pago |
| reporting | commitments | consulta | total por cobrar |
| frontend | API | HTTP/OpenAPI | comandos y queries |
| offline queue | API | HTTP + idempotencia | reintento seguro |

## Antipatrones prohibidos

- `dashboard` actualizando `commitments`;
- `reminders` marcando un compromiso como pagado;
- `contacts` almacenando saldo;
- `transactions` enviando email directamente;
- `frontend` decidiendo `workspace_id` autorizado;
- imports circulares entre módulos para acceder a internals.
