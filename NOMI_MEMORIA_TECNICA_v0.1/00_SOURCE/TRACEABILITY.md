# Trazabilidad de la memoria técnica

## Fuente

La memoria deriva de `NOMI_PAQUETE_COMPLETO.md`, documento maestro de producto y arquitectura, y desarrolla con mayor precisión las decisiones trabajadas durante el diseño del núcleo.

El documento fuente ya establece:

- definición y límites de Nomi;
- PRD e hipótesis;
- alcance MVP y fuera de alcance;
- requisitos no funcionales;
- arquitectura monolítica modular;
- stack;
- C4;
- ERD inicial;
- API;
- seguridad;
- privacidad;
- observabilidad;
- backup;
- offline;
- monetización;
- roadmap;
- pruebas;
- DevOps;
- ADR;
- riesgos y definición de terminado.

## Refinamientos incorporados en esta memoria

La presente carpeta desarrolla y formaliza, entre otros, los siguientes puntos que en el documento fuente estaban resumidos o ambiguos:

1. Separación entre `lifecycle_status`, `payment_state` y `timing_state`.
2. Definición de `Contact` como entidad neutral: no es permanentemente cliente/proveedor/deudor.
3. Workspace como propietario de datos, con Membership como vínculo de identidad.
4. Una moneda por Workspace en Core v0.1.
5. Bloqueo del cambio de moneda una vez existen operaciones financieras.
6. Modelo detallado de `Transaction`.
7. `PAYMENT` y `REVERSAL` como tipos Core iniciales.
8. Reversión autorreferenciada mediante `reversal_of_transaction_id`.
9. Eliminación de `reversed_at` como fuente duplicada de verdad.
10. Prohibición de edición destructiva de movimientos financieros.
11. Cancelación distinta de pago: un cancelado puede conservar saldo histórico.
12. Idempotencia con registro genérico y `request_hash`.
13. Sesiones revocables del lado servidor como estrategia preferida para web.
14. Casos de uso UC-001 a UC-008.
15. Failure/edge case pass del núcleo.
16. Estrategia PostgreSQL `VARCHAR + CHECK` frente a ENUM nativo.
17. Constraints concretos para montos, balance y coherencia de estados.
18. Reglas explícitas de dependencia entre módulos.

## Regla de mantenimiento

Cuando una implementación contradiga esta memoria, no se debe “corregir el documento después” sin análisis. Debe abrirse una decisión:

1. identificar por qué la implementación requiere apartarse;
2. analizar impacto;
3. crear/actualizar ADR;
4. actualizar ERD/API/casos de uso;
5. aplicar migración o refactor;
6. actualizar esta memoria en el mismo cambio.
