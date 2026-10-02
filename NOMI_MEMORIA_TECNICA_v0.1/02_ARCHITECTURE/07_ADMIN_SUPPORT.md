# Panel administrativo y soporte

**Estado:** MVP mínimo / diseño a concretar.

## Objetivo

Operación de la plataforma:

- ver salud;
- gestionar incidencias;
- localizar cuenta por identificadores mínimos;
- revisar estado de suscripción;
- ejecutar soporte controlado;
- observar auditoría de seguridad.

## Principio de mínimo privilegio

`support_admin` es rol de plataforma, no Membership automática.

El panel no debe convertir a personal de soporte en lector por defecto de datos financieros.

## Acceso excepcional

Si una incidencia requiere ver información financiera:

1. motivo/ticket;
2. autorización;
3. acceso temporal;
4. mínimo alcance;
5. AuditEvent;
6. expiración.

## Prohibido

- búsqueda abierta de contactos de usuarios;
- exportar datos financieros sin motivo;
- modificar balances manualmente;
- usar el panel como “SQL con botones”.

## Operaciones de reparación

Cualquier corrección financiera debe pasar por un caso de uso auditado o runbook específico; nunca por UPDATE libre.
