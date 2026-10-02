# Billing y Subscription

**Estado:** PLANIFICADO después de validar Core.

## Separación conceptual

El dinero que el usuario controla en Nomi y el dinero que paga por usar Nomi son dominios distintos.

`Commitment` nunca debe mezclarse con `Subscription`.

## Subscription

```text
id
workspace_id
provider_customer_id
provider_subscription_id
plan_code
status
current_period_end
```

## Fuente

El proveedor procesa pago; Nomi mantiene una proyección local del estado de la suscripción mediante webhooks verificados.

## Webhooks

- verificar firma;
- event_id único;
- responder rápido;
- procesar idempotentemente;
- tolerar duplicados/fuera de orden;
- no confiar en frontend para habilitar plan.

## Pago fallido

No borrar datos.

Aplicar:

```text
active
→ grace period
→ restricted premium features
```

de forma reversible.

## Plan ownership

Subscription pertenece al Workspace para permitir futura membresía multiusuario.

## Seguridad

Nomi no guarda números completos de tarjeta.
