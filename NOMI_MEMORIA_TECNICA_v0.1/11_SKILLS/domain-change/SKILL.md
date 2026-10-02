---
name: nomi-domain-change
description: Introduce una capacidad nueva al dominio Nomi sin romper invariantes, historial ni límites del MVP.
---

# Domain Change Skill

## Ejemplos

- ajustes financieros;
- multimoneda;
- recurrencias;
- equipos;
- reapertura de cancelados.

## Proceso

1. Describir problema real validado.
2. Identificar entidad responsable.
3. Evaluar si cabe en modelo actual.
4. Escribir invariantes nuevas.
5. Ejecutar escenarios happy + failure.
6. Revisar historial y auditoría.
7. Revisar efecto en balance/dashboard.
8. Revisar offline/concurrencia.
9. Diseñar migración.
10. Crear ADR.
11. Actualizar OpenAPI.
12. Añadir tests.

## Pregunta obligatoria

> ¿El nuevo comportamiento puede cambiar un saldo histórico sin dejar una operación que explique el cambio?

Si sí, el diseño debe revisarse.
