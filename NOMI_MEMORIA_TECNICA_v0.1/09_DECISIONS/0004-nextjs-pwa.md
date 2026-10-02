# ADR-0004 — Next.js PWA

**Estado:** ACEPTADA

## Decisión
Next.js + TypeScript como interfaz mobile-first instalable.

## Razón
Una sola base web para validar móvil y escritorio antes de apps nativas.

## Riesgos
- cache incorrecta;
- Service Worker;
- versiones desactualizadas;
- offline conflictivo.

## Mitigación
Offline por etapas, políticas explícitas y estado visible de sincronización.
