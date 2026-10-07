# Índice documental de Nomi

La memoria técnica conserva las decisiones de producto y arquitectura. Los documentos de implementación describen evidencia y límites; no reemplazan decisiones aceptadas.

- [Instrucciones para agentes](AGENTS.md).
- [Arranque y validación local](README.md).
- [Índice completo de la memoria v0.1](NOMI_MEMORIA_TECNICA_v0.1/DOC_INDEX.md).
- [Estado de la primera entrega](docs/IMPLEMENTATION_STATUS.md).
- [Rediseño UI y diagnóstico priorizado](docs/UI_REWORK_AND_REVIEW.md).
- [Contratos provisionales, ADR-0019](docs/adr/0019-first-slice-contracts.md).
- [Contratos aceptados de reconstrucción, ADR-0020](docs/adr/0020-core-reconstruction-contracts.md).
- [Cuentas y correo durable, ADR-0021](docs/adr/0021-account-lifecycle-and-mail-worker.md).
- [Pruebas y operación de cuentas](docs/ACCOUNT_LIFECYCLE_VALIDATION.md).
- [Cierre funcional, seguridad, carga y accesibilidad locales](docs/CORE_LOCAL_COMPLETION.md).
- [Lifecycle de Core y calidad local, ADR-0022](docs/adr/0022-core-lifecycle-and-local-quality.md).
- [Cliente Android, ADR-0023](docs/adr/0023-android-first-client.md).
- [APK Android: instalación, validación y puerta Google Play](docs/ANDROID_VALIDATION.md).
- [Restauración, caída de PostgreSQL y HTTPS local; requisitos de staging](docs/OPERATIONS_VALIDATION.md).
- [Diagnóstico de reconstrucción](docs/ARCHITECTURE_RECONSTRUCTION_BRIEF.md).
- [Plan incremental y avance](RECONSTRUCTION_PLAN.md).
- [Contrato OpenAPI ejecutable](docs/api/openapi.json).
- [Trazabilidad entre requisitos, código y pruebas](TRACEABILITY.md).

La sesión sigue provisional para liberación hasta validar staging/TLS del proveedor; lifecycle
y TLS sintético local ya están probados. Registro atómico y timing
de cerrados quedan aceptados por ADR-0020. La implementación cubre la vertical extendida con
reversión, recuperación de operaciones inciertas y Dashboard; no todo el alcance Core/MVP.
