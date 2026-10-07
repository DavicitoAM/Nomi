# Nomi — Primera slice ejecutable

Fecha: 2026-10-07. Estado: implementación local; no liberación de producción.

## Alcance implementado

RegisterUser → Workspace/Membership owner → CreateContact → CreateCommitment → RegisterPayment → ReversePayment → Dashboard.

El cierre posterior añade detalle/edición/archivo/restauración de contactos, resumen por contacto,
edición descriptiva/cancelación de compromisos, exportación consistente, mantenimiento acotado
de credenciales y controles de seguridad/carga/accesibilidad. Ver [evidencia actual](CORE_LOCAL_COMPLETION.md)
y [ADR-0022](adr/0022-core-lifecycle-and-local-quality.md).

Incluye login/logout, sesión revocable, `/me`, listados por cursor, detalle, historial, cookies, CSRF, validación de origen, Problem Details, cliente TypeScript generado desde OpenAPI, auditoría y outbox transaccionales, replay idempotente y optimistic locking. La interfaz es mobile-first y distingue carga, vacío, error, éxito y conflicto.

El primer milestone sigue AGENTS.md §34. Foundation y los pasos intermedios son tareas internas de esa entrega. Auditoría/outbox y controles de acceso entran junto a cada escritura, aunque las enumeraciones del roadmap los sitúen después.

## Contratos concretados para la slice

Ver [ADR-0020 aceptado](adr/0020-core-reconstruction-contracts.md), que concreta las decisiones delegadas por el usuario y refina los puntos indicados de ADR-0013/0019. La sesión sigue provisional.

- `expected_version` viaja en el body de RegisterPayment y ReversePayment.
- El hash idempotente incluye el recurso objetivo y el payload normalizado; el registro se reclama con INSERT ON CONFLICT dentro de la transacción. Otro request con la misma clave espera su resolución en PostgreSQL. Rollback elimina la reserva.
- `response JSONB` conserva el DTO necesario para reproducir el resultado confirmado, incluso después de pagos posteriores. No se guarda el request completo, tokens ni credenciales. No hay expiración automática en esta slice: eliminar claves permitiría duplicaciones tardías.
- La respuesta de pago contiene Transaction + Commitment. El historial conserva montos positivos y tipo semántico.
- `timing_state=null` para compromisos no abiertos. No se añade otro valor al enum temporal.
- El monto máximo por operación es 9,000,000,000,000 unidades menores. Los montos de formulario se convierten mediante aritmética entera. Los cuatro agregados monetarios del Dashboard viajan como strings decimales de unidades menores y se formatean con BigInt; no pierden centavos por encima de 2^53.
- Se usa sesión opaca provisional con secreto hasheado y CSRF ligado a sesión. No se persisten secretos en localStorage.
- User, Workspace, Membership, Session, auditoría e intención de verificación se crean en un único commit. UC-001 describía sesión/verificación después del commit: se amplía la atomicidad para evitar cuentas sin sesión por fallo parcial. Una respuesta perdida se recupera mediante login; el registro no se presenta como idempotente.
- Se permite operar como `pending_verification` únicamente en development. Fuera de ese entorno la sesión permite consultar perfil, cerrar sesión y reenviar verificación; los datos de negocio exigen cuenta verificada. La intención EmailVerificationRequested queda durable y la procesa el worker. Verificación, reenvío y recuperación están implementados según ADR-0021; el modo local utiliza el buzón de pruebas.
- El esquema inicial contiene sólo campos usados por esta slice. Los tokens y campos de verificación/actualización de User entran en la migración aditiva 3da72910ea21. Notas y updated_at de contacto entran en 4eb83021fb32 con edición, archivo y restauración.

## Fronteras

Cada módulo es dueño de sus modelos y repositorios. Los casos de uso trabajan a través de UnitOfWork. Reporting usa una consulta pública del repositorio de Commitments, sin escribir su estado. Transactions obtiene un Commitment autorizado y aplica su operación de dominio antes de guardar el movimiento. No hay SQL de negocio en los routers.

La revisión del 6 de octubre corrigió la distribución plana inicial: dominio en `domain/`, casos de uso en `application/`, modelos/repositorios en `infrastructure/` y schemas/rutas en `api/`. El router raíz sólo compone los módulos. No se crean capas vacías. Esa redistribución inicial mantuvo contrato y esquema. La reconstrucción posterior amplía OpenAPI; el esquema financiero sigue igual. ADR-0021 añade tablas auxiliares de cuenta y metadatos de entrega mediante una nueva migración. Las invariantes de monto entero, saldo, estado y versión se validan también al construir la entidad, incluso fuera de HTTP.

## Validación local

- Pruebas unitarias y de integración con `nomi_test`, PostgreSQL real y migración Alembic.
- Carreras reales de dos pagos; reintentos simultáneos con la misma clave; replay después de cambios posteriores.
- Inyección de fallos de auditoría/outbox y registro; rollback integral.
- Autorización de otro Workspace, expiración, revocación, CSRF, origen y validación sin reflejar secretos.
- E2E de escritorio y viewport móvil; capturas en `.local/`.
- Build de Next.js, TypeScript, Ruff y comparación de esquema Alembic.

La entrega de cuentas aprobó 88 pruebas de backend y ocho E2E. El cierre posterior amplía
la validación: ver los [resultados actuales](CORE_LOCAL_COMPLETION.md). TypeScript, build y
Ruff aprobados; Alembic sin diferencias pendientes entre modelos y esquema. La API y el cliente
se regeneraron desde el mismo contrato. Permanece un aviso de deprecación del adaptador HTTPX
de Starlette. CI remoto y staging no están verificados.

Los E2E prueban el recorrido $10,000 → $7,500 → $10,000, búsqueda del servidor, historial enlazado, respuesta perdida después de commit con recarga/logout/cambio de cuenta y recuperación sin segundo pago, y presentación exacta de 9,007,199,254,740,993 unidades menores. Las carreras de reversión/pago, doble reversión, rollback, cancelados e IDOR se prueban contra PostgreSQL real.

La intención financiera se conserva en IndexedDB con una sola operación pendiente por usuario/Workspace; Web Locks serializa pestañas. Fallar al persistir impide enviar. Éxito o rechazo definitivo elimina la intención; errores inciertos y logout la conservan. No es una cola offline completa y borrar manualmente los datos del navegador elimina esta recuperación local. El servidor mantiene la deduplicación por clave.

El historial usa created_at + UUID y muestra la relación de reversión; la contraparte se deriva por consulta, no se añade reversed_at. Los filtros y búsqueda operan en el servidor y la lista incluye nombres de contacto sin depender de la página cargada en la web.

La suite elimina datos exclusivamente de `nomi_test`; se niega a ejecutarse sobre otro nombre. E2E crea cuentas y contactos sintéticos en la base usada por la API local.

## Pendientes explícitos

Cancelación, archivo/restauración y edición descriptiva están implementados y probados según
ADR-0020/0022. No se implementan edición financiera silenciosa ni reapertura de cancelados.

El worker de correo está operativo localmente. Exportación JSON acotada, limpieza de credenciales
antiguas, SAST/secret scanning, accesibilidad automatizada/teclado y carga local están implementados.
Faltan consumidores de otros efectos cuando se necesiten, política general de retención y purga,
exportación masiva, PWA/offline, staging, restauración del proveedor, SLO desplegado y validación con
lector de pantalla/dispositivos físicos. El ensayo local aislado de restore cifrado, caída de PostgreSQL
y TLS ya pasó; ver [resultados y límites](OPERATIONS_VALIDATION.md). El rate limiter actual es local
a un proceso. OpenTelemetry API delimita spans; no hay exportador/collector configurado.
No se declara cumplimiento completo de Definition of Done de lanzamiento.

No usar la demo como único registro de dinero real. No se publicaron servicios ni se desplegó a producción.

## Entrega de cuentas y persistencia

Se completaron verificación/reenvío, recuperación con tokens de un uso, revocación de sesiones y worker con reintentos persistidos. El buzón local está en http://localhost:8025. Se conservan las finanzas al migrar y al recuperar acceso. Ver [pruebas y límites](ACCOUNT_LIFECYCLE_VALIDATION.md) y [ADR-0021](adr/0021-account-lifecycle-and-mail-worker.md). La sesión opaca sigue provisional para liberación hasta validar TLS/staging; no se habilitó un proveedor real.
