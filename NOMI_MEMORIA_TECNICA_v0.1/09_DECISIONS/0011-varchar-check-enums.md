# ADR-0011 — VARCHAR + CHECK para enums de PostgreSQL

**Estado:** ACEPTADA

## Contexto
Los valores de dominio todavía pueden evolucionar durante MVP.

## Decisión
Persistir valores como VARCHAR con CHECK. En Python usar Enum.

## Razón
Combina integridad con migraciones más simples que ENUM nativo de PostgreSQL.

## Consecuencia
Cada nuevo valor requiere migración del CHECK.
