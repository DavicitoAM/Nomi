# ADR-0003 — FastAPI

**Estado:** ACEPTADA

## Decisión
FastAPI + Python tipado + Pydantic + SQLAlchemy.

## Razones
- API-first;
- OpenAPI;
- validación tipada;
- productividad;
- buen ajuste con separación domain/application/infrastructure/api.

## Riesgo
Fragmentar seguridad/autenticación mediante demasiadas dependencias.

## Mitigación
Pocas bibliotecas, adapters propios y pruebas explícitas.
