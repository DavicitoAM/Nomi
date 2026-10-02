# Monetización

## Principio

Cobrar por valor sostenido y reducción de fricción, no por secuestrar datos.

Exportación y eliminación deben permanecer disponibles.

## Hipótesis de planes

### Gratis

- un usuario;
- límite de compromisos activos;
- dashboard;
- pagos/abonos;
- recordatorios in-app;
- CSV básico.

### Nomi Plus

- límites ampliados;
- email/push;
- recurrencias;
- PDF/personalización;
- filtros/historial avanzados.

### Nomi Negocio — futuro

- miembros;
- roles;
- auditoría visible;
- espacios/sucursales;
- soporte prioritario.

## Precio

No fijar definitivamente antes de:

- entrevistas de disposición a pagar;
- experimentos de página de precios;
- cohortes/rangos;
- medir conversión/cancelación;
- revisar margen real.

## Billing

Cuando se implemente:

- checkout alojado;
- portal alojado;
- webhooks firmados;
- no almacenar tarjeta;
- Subscription pertenece al Workspace;
- pago fallido no borra datos;
- periodo de gracia;
- degradación reversible de funciones premium.

## Aislamiento arquitectónico

Billing no debe contaminar el dominio financiero de Commitments. Una suscripción de Nomi es distinta del dinero pendiente que el usuario registra.
