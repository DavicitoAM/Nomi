# ADR-0002 — PostgreSQL como fuente de verdad

**Estado:** ACEPTADA

## Contexto
Nomi maneja relaciones, integridad referencial, dinero, auditoría y transacciones.

## Decisión
PostgreSQL es la base transaccional primaria.

## Motivos
- ACID;
- FK/CHECK/UNIQUE;
- queries agregadas;
- madurez;
- bloqueo/concurrencia;
- JSONB para metadata controlada.

## Alternativas
MongoDB o almacenes propietarias serverless.

## Consecuencia
Se deben diseñar y operar migraciones. No se modelará el dominio como documentos desnormalizados por comodidad.
