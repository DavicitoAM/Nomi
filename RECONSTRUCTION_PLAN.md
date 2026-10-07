# Nomi — Plan incremental de reconstrucción

Fecha: 2026-10-07. Estado: R0 concretado y R1–R4 implementados localmente; R5 con evidencia local y puerta de liberación pendiente; R6 posterior.

Actualización autorizada: el usuario eligió Android/Google Play primero y pidió construirlo.
Se abre A1 conforme a ADR-0023, después de las pruebas locales Core. Esta decisión sustituye
la exclusión anterior de Mobile para Android; no elimina la puerta remota R5 ni abre Ads/Billing.

R4: verificación, recuperación, worker de correo, contactos/archivo/restauración, cancelación y
edición descriptiva implementados y probados conforme a ADR-0021/0022. R5 incorpora límites
reales de requests, controles de seguridad, E2E/accesibilidad, carga y restore locales.
Ver [cierre y pendientes externos](docs/CORE_LOCAL_COMPLETION.md).

El usuario delegó las decisiones y autorizó construir después del diagnóstico. R0 se concretó
en ADR-0020; R1–R3 se implementaron y validaron localmente. No se creó un commit ni se descartó
el trabajo previo. La puerta remota de R5, R6 y la liberación de producción continúan pendientes. Ver evidencia en
[estado de implementación](docs/IMPLEMENTATION_STATUS.md).

Diagnóstico: [Architecture & Reconstruction Brief](docs/ARCHITECTURE_RECONSTRUCTION_BRIEF.md).

## Objetivo y restricciones

Cerrar el recorrido **RegisterUser → CreateContact → CreateCommitment → RegisterPayment → ReversePayment → GetDashboardSummary** sobre el monolito existente. Conservar la UI actual, datos, migraciones, stack y trabajo pendiente del árbol local. No crear microservicios, Redis, anuncios o compras. Android se limita al milestone A1 autorizado.

El primer cierre de una vertical no declara terminado todo Core ni todo el MVP. Mobile/AdMob/Play Billing requieren después una revisión separada; no se activan automáticamente al terminar un milestone.

## R0 — Línea base y contratos

- Inventariar y guardar una versión identificable de los cambios actuales sin descartarlos. Revisar qué se registra; no incorporar secretos, datos locales o artefactos de prueba.
- Acordar jerarquía documental y nombres de casos de uso. Mantener el endpoint de reversión ya especificado: `/api/v1/transactions/{transaction_id}/reverse`.
- Precisar expected_version obligatorio, estado de cancelados, relación pago/reversión en DTO, atomicidad del registro y timing de cerrados.
- Resolver cómo conservar intenciones con respuesta incierta y cómo representar dinero exacto extremo. Documentar alternativas y consecuencias antes de cambiar OpenAPI.
- Definir sesiones opacas como provisionales hasta completar recuperación/verificación y validar entorno TLS.

**Salida:** matriz de decisiones revisada, contrato propuesto y casos de aceptación. No cambian silenciosamente ADR aceptados. No exige rehacer los módulos que ya funcionan.

## R1 — Asegurar el recorrido existente hasta RegisterPayment

**Módulos:** identity/workspaces/contacts/commitments/transactions y cliente web.

- Conservar registro atómico, aislamiento y manejo de errores ya implementados.
- Corregir S01: conservar y reconciliar la misma intención ante respuesta perdida, cierre y recarga. La solución debe separar usuario/workspace y evitar reenvíos desde otra cuenta. Guardar sólo lo necesario y definir limpieza/privacidad.
- Corregir mensajes que prometen idempotencia para operaciones que no la tienen.
- Corregir S02 según el contrato acordado: exactitud monetaria en transporte y presentación, con límites explícitos.
- Introducir Enum Python preservando strings HTTP/DB; tipar sólo los puertos tocados por este recorrido. Evitar una refactorización transversal sin necesidad.

**Pruebas de salida:** registro crea una sola cadena User/Workspace/OWNER; contacto se aísla por Workspace; creación/retry no duplica compromiso; pago reduce una vez el saldo; concurrencia rechaza versión obsoleta; respuesta perdida + recarga conserva resultado; montos extremos conservan unidades menores; no hay fuga tras cambio de cuenta.

**Datos:** nuevas migraciones sólo si la decisión requiere esquema nuevo. No modificar retrospectivamente la migración inicial.

## R2 — ReversePayment de extremo a extremo

**Módulos:** commitments, transactions, audit y soporte idempotente/outbox; API y UI.

- Implementar transición de dominio para restaurar saldo y reabrir PAID.
- Derivar monto, moneda y compromiso del payment original autorizado.
- Reservar/reproducir idempotencia, validar versión y evitar doble reversión con aplicación + constraint existente.
- Confirmar reversal, saldo/version, audit, outbox y resultado idempotente dentro de una transacción.
- Incorporar DTO con vínculo al movimiento original, acción explícita de reversión, confirmación y errores recuperables.
- Mantener política de cancelados aprobada en R0; no reabrir CANCELLED implícitamente.

**Pruebas de salida:** pago parcial y reversión; pago total y reapertura; rechazo de doble reversión y de revertir una reversal; IDs ajenos; same key/same request; conflicto de clave; carreras reales; rollback; versión obsoleta; relación visible en historial.

**Migraciones:** la self-FK y UNIQUE ya existen. Revisar si basta el esquema actual; no crear una migración vacía ni otra columna `reversed_at`.

## R3 — GetDashboardSummary e historial coherentes

**Módulos:** reporting y puertos de lectura de commitments/transactions/contacts; web.

- Demostrar que el resumen se actualiza tras pago/reversión, sin almacenar totales paralelos.
- Resolver cursor temporal estable con desempate por UUID; acordar fecha de registro/ocurrencia y ordenar consistentemente en API/UI.
- Llevar filtros/búsqueda al servidor para consultar el Workspace completo. Resolver nombres de contactos sin depender de cargar manualmente todas sus páginas.
- Evaluar el desglose por cobrar/por pagar de vencimientos; cualquier ampliación actualiza OpenAPI y cliente generado.

**Puerta vertical E2E:** registro → contacto Juan → compromiso MXN 1,000,000 unidades menores → Dashboard 1,000,000 → payment 250,000 → saldo 750,000 → reversal 250,000 → saldo 1,000,000. Historial conserva las dos transacciones enlazadas y positivas; Dashboard vuelve al importe inicial. Ejecutar en escritorio y viewport móvil, incluyendo un Workspace distinto y reintentos.

Superar esta puerta completa la vertical pedida, no da permiso para saltar directamente a Mobile/Ads.

## R4 — Completar el alcance de Core

- Identity: verificación, recuperación, tokens de un uso/expiración y revocación tras password change; política de pending_verification explícita y probada por ambiente.
- Contacts: detalle, edición, archive/restore y resumen; duplicados permitidos; archivo no altera saldos ni historia.
- Commitments: cancelación con versión, confirmación, audit/outbox y exclusión de agregados sin poner saldo en cero; edición sólo conforme a reglas aprobadas.
- Añadir campos auxiliares cuando su caso de uso los utilice, mediante nuevas migraciones; definir borrado lógico/purga por separado.
- Processor mínimo de outbox para los efectos realmente usados, con reintentos y consumidores idempotentes. Un fallo externo no revierte un pago confirmado.

**Salida:** contratos, pruebas unitarias/integración/seguridad y E2E de cada capacidad; ninguna operación monetaria editable o eliminable como corrección silenciosa.

## R5 — Calidad operativa y puerta de liberación de Core

- Entorno explícito, TLS/cookies seguras, límites efectivos de requests y rate limiting con proxy confiable.
- Logs estructurados sin PII y OpenTelemetry operativo; métricas de latencia, errores y backlog.
- CI remoto con evidencia, migración desde versión previa y base vacía, smoke tests en staging, backup y restauración verificados.
- Pruebas de accesibilidad, teclado, dispositivos/tamaños y rendimiento; análisis de dependencias/secretos y revisión de seguridad.
- Revisar política de retención de sesión, auditoría, outbox e idempotencia; no eliminar claves sin definir reintentos tardíos.

**Salida:** Definition of Done verificable para Core. Sin esta evidencia no declarar listo para producción.

## R6 — Offline y extensiones posteriores

Sólo tras estabilizar Core: lectura offline → creación de datos simples → compromisos → pagos, siempre con cola durable, identidad de operación, versión y conflictos explícitos. Exportación básica y portabilidad se preservan. Este milestone requiere su propio alcance y pruebas; R1 sólo resuelve operaciones online con resultado incierto, no implementa toda la sincronización offline.

AdMob, Play Billing e iOS siguen fuera del plan ejecutable. Android entra por A1, sin anticipar
sincronización offline completa ni monetización.

## A1 — Primer Android instalable

- React/TypeScript/Capacitor con assets locales, reutilizando UI y API; ADR-0023.
- Sesión nativa cifrada con Android Keystore, navegación Atrás, exportación al selector nativo.
- Prueba en WebView real de la vertical, proceso reiniciado, desconexión e intención durable.
- APK debug y build repetible; CI de compilación/JVM configurado, ejecución remota pendiente.
- Evidencia y próximos pasos: [validación Android](docs/ANDROID_VALIDATION.md).

La publicación requiere backend HTTPS/SMTP, identidad/firma de producción, enlaces HTTPS
verificados, lifecycle de eliminación de cuenta, privacidad, formularios y pruebas de Play.
No se sustituye esa validación por un build exitoso de debug.

## Disciplina por milestone

1. Especificar criterios y resolver contradicciones pertinentes.
2. Aplicar un cambio pequeño que funcione de extremo a extremo.
3. Validar dominio, integración PostgreSQL, autorización y fallos; actualizar OpenAPI/cliente si cambia contrato.
4. Añadir migración cuando corresponda y validar forward-fix/retención de datos.
5. Pasar lint/types/build y E2E afectados; documentar límites y evidencia real.
6. Revisar antes de abrir el siguiente alcance. No confundir ausencia de fallo en happy path con cumplimiento de Core.

No se fijan fechas sin dimensionar el entorno de staging. La próxima puerta es completar R5 en
el proveedor elegido, conservando la vertical validada y sus regresiones. No reiniciar Foundation
ni rehacer otra vez la UI. R6 y Mobile/Ads no se activan automáticamente.
