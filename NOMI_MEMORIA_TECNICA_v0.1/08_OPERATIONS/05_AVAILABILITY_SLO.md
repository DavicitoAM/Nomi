# Disponibilidad, SLI y SLO

## SLO inicial

Hipótesis:

- API 99.5% mensual;
- 95% de lecturas bajo 500 ms sin red de usuario;
- escrituras p95 bajo 800 ms;
- 99% de recordatorios procesados dentro de ventana de 15 min respecto de programación, sin garantizar entrega del proveedor.

## SLI

- disponibilidad API;
- latencia;
- 5xx;
- outbox/worker lag;
- recordatorio lag;
- sync success/conflict.

## Degradación

Servicios no críticos pueden fallar sin bloquear:

- email;
- push;
- analítica.

Una dependencia crítica como PostgreSQL sí vuelve `ready=false`.

## Error budget

Las alertas deben observar consumo sostenido del presupuesto y no sólo picos instantáneos.

## Rendimiento

Evitar optimizar prematuramente. Medir:

- dashboard;
- listados;
- history;
- Payment writes.

Los índices definidos son hipótesis que se validan con EXPLAIN y datos reales.
