---
name: nomi-architecture-review
description: Revisa un cambio de Nomi para detectar acoplamiento, violaciones de dominio, inconsistencias de datos y ADR faltantes.
---

# Nomi Architecture Review

## Usar cuando

- se agrega un módulo;
- un módulo necesita acceder a datos de otro;
- se introduce un proveedor externo;
- cambia el modelo de datos;
- una feature toca más de un dominio.

## Entradas

- descripción del cambio;
- módulos afectados;
- entidades/tablas;
- endpoints;
- eventos;
- migraciones.

## Proceso

1. Identificar dueño de cada dato.
2. Dibujar flujo: API → Application → Domain → Repository.
3. Verificar que un módulo no modifique tablas internas de otro sin caso de uso.
4. Confirmar Workspace scoping.
5. Identificar transacción ACID necesaria.
6. Separar efecto síncrono de secundario/outbox.
7. Verificar idempotencia/concurrencia si toca dinero.
8. Revisar si cambia un ADR.
9. Revisar impacto offline/API/frontend.
10. Proponer tests negativos.

## Guardrails Nomi

- Dashboard no es fuente de verdad.
- Saldo no cambia sin Transaction.
- No microservicios por anticipación.
- Redis sólo por necesidad demostrada.
- No multimoneda incidental.
- No secretos/PII en telemetría.

## Salida

Checklist con:
- decisión;
- riesgos;
- cambios de docs;
- ADR requerido;
- tests obligatorios.
