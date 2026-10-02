# Nomi — Primera slice ejecutable

Fecha: 2026-10-02. Estado: implementación local; no liberación de producción.

## Alcance implementado

RegisterUser → Workspace/Membership owner → CreateContact → CreateCommitment → RegisterPayment → Dashboard.

Incluye login/logout, sesión revocable, `/me`, listados por cursor, detalle, historial, cookies, CSRF, validación de origen, Problem Details, cliente TypeScript generado desde OpenAPI, auditoría y outbox transaccionales, replay idempotente y optimistic locking. La interfaz es mobile-first y distingue carga, vacío, error, éxito y conflicto.

El primer milestone sigue AGENTS.md §34. Foundation y los pasos intermedios son tareas internas de esa entrega. Auditoría/outbox y controles de acceso entran junto a cada escritura, aunque las enumeraciones del roadmap los sitúen después.

## Contratos concretados para la slice

Ver [ADR-0019 provisional](adr/0019-first-slice-contracts.md). No sustituye decisiones aceptadas.

- `expected_version` viaja en el body de RegisterPayment.
- El hash idempotente incluye el recurso objetivo y el payload normalizado; el registro se reclama con INSERT ON CONFLICT dentro de la transacción. Otro request con la misma clave espera su resolución en PostgreSQL. Rollback elimina la reserva.
- `response JSONB` conserva el DTO necesario para reproducir el resultado confirmado, incluso después de pagos posteriores. No se guarda el request completo, tokens ni credenciales. No hay expiración automática en esta slice: eliminar claves permitiría duplicaciones tardías.
- La respuesta de pago contiene Transaction + Commitment. El historial conserva montos positivos y tipo semántico.
- `timing_state=null` para compromisos no abiertos. No se añade otro valor al enum temporal.
- El monto máximo por operación es 9,000,000,000,000 unidades menores. Los montos de formulario se convierten mediante aritmética entera. Los agregados de grandes volúmenes requieren revisar el límite de serialización antes de escalar.
- Se usa sesión opaca provisional con secreto hasheado y CSRF ligado a sesión. No se persisten secretos en localStorage.
- User, Workspace, Membership, Session, auditoría e intención de verificación se crean en un único commit. UC-001 describía sesión/verificación después del commit: se amplía la atomicidad para evitar cuentas sin sesión por fallo parcial. Una respuesta perdida se recupera mediante login; el registro no se presenta como idempotente.
- Se permite operar como `pending_verification` en la demo local. La intención EmailVerificationRequested queda durable; todavía no hay envío ni confirmación de correo.
- El esquema inicial contiene sólo campos usados por esta slice. Los campos auxiliares de perfil, notas, actualización de contacto y tokens de recuperación entrarán con sus casos de uso y nuevas migraciones.

## Fronteras

Cada módulo es dueño de sus modelos y repositorios. Los casos de uso trabajan a través de UnitOfWork. Reporting usa una consulta pública del repositorio de Commitments, sin escribir su estado. Transactions obtiene un Commitment autorizado y aplica su operación de dominio antes de guardar el movimiento. No hay SQL de negocio en los routers.

## Validación local

- Pruebas unitarias y de integración con `nomi_test`, PostgreSQL real y migración Alembic.
- Carreras reales de dos pagos; reintentos simultáneos con la misma clave; replay después de cambios posteriores.
- Inyección de fallos de auditoría/outbox y registro; rollback integral.
- Autorización de otro Workspace, expiración, revocación, CSRF, origen y validación sin reflejar secretos.
- E2E de escritorio y viewport móvil; capturas en `.local/`.
- Build de Next.js, TypeScript, Ruff y comparación de esquema Alembic.

La suite elimina datos exclusivamente de `nomi_test`; se niega a ejecutarse sobre otro nombre. E2E crea cuentas y contactos sintéticos en la base usada por la API local.

## Pendientes explícitos

Core completo aún requiere reversión, cancelación, archivo/restauración, edición permitida, recuperación/verificación por correo, y resolver sus ambigüedades documentadas. No se exponen endpoints de esas operaciones.

También faltan worker operativo/consumidores outbox, retención y purga, exportación, PWA/offline, SAST/secret scanning formal, despliegue en staging, restore drill, medición de SLO y revisión completa de accesibilidad. El rate limiter actual es local a un proceso. OpenTelemetry API delimita spans; no hay exportador/collector configurado. No se declara cumplimiento completo de Definition of Done de lanzamiento.

No usar la demo como único registro de dinero real. No se publicaron servicios ni se desplegó a producción.
