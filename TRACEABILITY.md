# Trazabilidad de implementación

Actualizada: 2026-10-07. Fuente: [memoria técnica](NOMI_MEMORIA_TECNICA_v0.1/DOC_INDEX.md) y [trazabilidad documental original](NOMI_MEMORIA_TECNICA_v0.1/00_SOURCE/TRACEABILITY.md).

| Requisito | Implementación | Evidencia |
| --- | --- | --- |
| Monolito modular, AGENTS §5–7 | `apps/api/app/modules/*/{domain,application,infrastructure,api}`; sólo capas con código | Revisión de imports y prueba de fronteras |
| Registro, sesión, Workspace personal | Identity y Workspaces; cookie opaca, CSRF y Membership owner | Registro atómico, expiración, revocación, BOLA/IDOR y contraseña sin normalización |
| Verificación y recuperación, ADR-0021 | Identity, tokens hasheados y entrega cifrada; worker de correo | Enlaces de un uso, expiración/reenvío, reset/login concurrentes y revocación de sesiones |
| Persistencia de cuentas | PostgreSQL + migración 3da72910ea21 + reservas de worker | Nuevo proceso API/worker, caída posterior a entrega y migración con datos conservados |
| Backup/recuperación y TLS local, Operations §04 / ADR-0005 | `scripts/operational_drill.py` sobre clúster sintético aislado | Restore cifrado, comparación de 13 tablas, caída inmediata/WAL, replay sin duplicado, certificados y cookies seguras; ver `docs/OPERATIONS_VALIDATION.md` |
| Contacto neutral | Contacts | Duplicados permitidos y rechazo de nuevos compromisos para archivados |
| Lifecycle de contactos, UC-007/ADR-0022 | Contacts + web | Edición/versiones, archivo/restauración, resumen y carreras con creación de compromisos |
| Edición descriptiva/cancelación, UC-008/ADR-0022 | Commitments + audit/outbox/idempotencia | Saldo conservado, exclusión de agregados, cancelación/pago concurrentes y rollback |
| Portabilidad acotada, ADR-0022 | Reporting y puertos de lectura | Snapshot consistente, aislamiento, límite explícito y exportación de vínculos de reversión |
| Limpieza de credenciales, ADR-0022 | Identity + CLI maintenance | Dry-run, lotes, credenciales vigentes y finanzas conservadas |
| Límite real de request | Middleware ASGI | Cuerpo fragmentado, Content-Length ausente/incorrecto, compresión y timeout |
| Seguridad repetible | pip-audit, npm audit, Bandit, detect-secrets + CI | Dependencia corregida, baseline revisada y sonda sintética detectada |
| Calidad web | axe, diálogo y recuperación IndexedDB | Tab/Shift+Tab, Escape, 320 px, sesión vencida, desconexión, almacenamiento lleno/bloqueado y dos pestañas |
| Rendimiento local | scripts/load_drill.py | 10,001 compromisos, ocho clientes, 360 lecturas y 100 pagos con integridad comprobada |
| Compromisos y dinero entero | Commitments/domain y constraints PostgreSQL | Rango, tipo estricto, estados, moneda, versión y sobrepago |
| Abono atómico | Transactions/application, UnitOfWork, Audit y Outbox | Rollback de efectos críticos, carrera entre pagos y saldo final |
| Idempotencia, ADR-0014 | Reserva única y hash normalizado | Replay tras pagos posteriores, clave conflictiva y reintentos simultáneos |
| Zona horaria | Estado temporal en Workspace; instantes normalizados UTC | Fechas límite y reintentos equivalentes con offsets distintos |
| Dashboard derivado, ADR-0018 | Reporting mediante consulta de Commitments | Exclusión de pagados/cancelados y agregados por dirección |
| Reversión, ADR-0015/0016/0020 | Transactions + Commitment.reverse_payment + CAS | Pago parcial/total, doble reversión, rollback, carreras y Workspace ajeno |
| Recuperación de intención | IndexedDB scoped + Web Locks + idempotencia PostgreSQL | E2E respuesta perdida/recarga/cambio de cuenta, un solo pago |
| Exactitud de agregados | Dashboard strings + BigInt web | Integración SUM mayor a 2^53 y E2E centavos exactos |
| Búsqueda y nombres | Puertos Contacts/Commitments | Filtros por Workspace, fechas, paginación y coincidencias fuera de primera página |
| Primera vertical, AGENTS §34 | Web Next.js + API FastAPI + PostgreSQL | E2E escritorio/móvil: $10,000 → abono $2,500 → $7,500 → reversión → $10,000 e historial |
| Contrato API | OpenAPI y cliente TypeScript generado | Regeneración sin diferencias; compilación de producción |
| Android primero, ADR-0023 | apps/mobile React/Capacitor + adaptador HTTP/Keystore | scripts/android-smoke.mjs en emulador: vertical, PATCH, sesión y saldo tras cierre, desconexión/recuperación, exportación y logout |
| Seguridad del transporte Android | RequestPolicy, SessionVault, MainActivity y configuración debug/release | JVM: origen HTTPS/rutas; WebView: cookies ausentes, vault cifrado y rechazo de destino ajeno; Android Lint |

Pruebas: [núcleo](apps/api/tests/test_core.py), [regresiones](apps/api/tests/test_regressions.py), [reconstrucción](apps/api/tests/test_reconstruction.py), [cuentas/persistencia](apps/api/tests/test_account_lifecycle.py), [lifecycle y calidad](apps/api/tests/test_core_lifecycle.py), [E2E financieros](tests/e2e/core.spec.ts), [E2E de cierre/accesibilidad](tests/e2e/lifecycle.spec.ts). Ver [cierre actual](docs/CORE_LOCAL_COMPLETION.md) para resultados y límites. CI está configurado; su ejecución remota y el smoke test de staging siguen pendientes.

No se modificó la migración inicial en la reconstrucción. [ADR-0020](docs/adr/0020-core-reconstruction-contracts.md) concreta la autorización del usuario y refina explícitamente las decisiones afectadas de ADR-0013/0019; la memoria original conserva el contexto histórico. Las operaciones pendientes no se declaran implementadas por el hecho de tener tablas preparadas.
