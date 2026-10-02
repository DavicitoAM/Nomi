---
name: nomi-pwa-offline-sync
description: Diseña operaciones offline de Nomi sin crear duplicados ni sobrescribir cambios financieros concurrentes.
---

# PWA Offline Sync Skill

## Usar cuando

Una feature debe funcionar sin conexión o sincronizar después.

## Proceso

1. Determinar si realmente necesita write offline.
2. Definir representación local.
3. Generar UUID/idempotency key.
4. Guardar operación durable.
5. Registrar expected version.
6. Sincronizar secuencialmente por dependencia.
7. Manejar success/idempotent replay/conflict.
8. Nunca hacer last-write-wins para movimientos financieros.
9. Mostrar estado al usuario.
10. Añadir telemetría sin PII.

## Orden recomendado

- read cache;
- Contact writes;
- Commitment writes;
- Payment writes al final.

## Conflict UI

Debe mostrar:
- estado local;
- estado servidor;
- motivo;
- acción de reintento/reconfirmación.
