# Reminders y Notification Preferences

**Estado:** PLANIFICADO para MVP, posterior a Core v0.1.

## Objetivo

Recordar al usuario de Nomi sobre compromisos que requieren atención. El MVP no envía cobranza automática a terceros.

## Reminder

```text
id
commitment_id
channel
scheduled_for
status
attempts
sent_at?
created_at
```

## NotificationPreference

```text
id
user_id
channel
enabled
settings
```

## Regla de diseño

Un Reminder es un efecto secundario del estado financiero, no parte de la transacción crítica que registra el dinero.

Si el proveedor de correo falla:

```text
RegisterPayment = success
Email = retry/failure independiente
```

## Programación

Inputs:

- due_date del Commitment;
- timezone del Workspace;
- preferencias del User;
- lifecycle/balance.

Un compromiso `paid` o `cancelled` no debe seguir generando avisos pendientes normales.

## Worker

```text
Outbox/clock
  ↓
seleccionar reminder debido
  ↓
marcar processing
  ↓
adapter proveedor
  ↓
sent o retry
```

## Idempotencia

Cada intento de entrega necesita una clave lógica para evitar correo duplicado al reintentar worker.

## Estados sugeridos

- `scheduled`
- `processing`
- `sent`
- `failed`
- `cancelled`

## No garantía

Nomi puede garantizar que procesó la intención dentro de una ventana operativa, no que el proveedor o dispositivo entregó físicamente el mensaje.
