---
name: nomi-adr-c4-maintenance
description: Mantiene ADR, C4, ERD y memoria técnica sincronizados con cambios arquitectónicos.
---

# ADR/C4 Maintenance Skill

## Disparadores

- cambia stack;
- cambia frontera de módulo;
- nuevo proveedor;
- nueva tabla central;
- cambio de autenticación;
- cambio de consistencia;
- nueva estrategia offline.

## Proceso

1. Registrar contexto.
2. Enumerar alternativas reales.
3. Elegir decisión.
4. Documentar consecuencias negativas también.
5. Marcar estado.
6. Actualizar C4 si cambia contenedor/componente.
7. Actualizar ERD si cambia datos.
8. Actualizar casos de uso/API.
9. Añadir tests/migraciones relacionadas.

## Regla

ADR no es una retrospectiva para justificar código ya hecho; debe representar la decisión y sus tradeoffs.
