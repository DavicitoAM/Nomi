# ADR-0022 — Cierre local de Core y calidad

Estado: **ACEPTADA**, 2026-10-06, bajo la delegación explícita del usuario.

## Decisiones

- UC-007 y API especializada prevalecen sobre el antiguo DELETE: GET/PATCH de contacto,
  POST archive/restore. Notas y updated_at son aditivos. Ediciones completas de campos
  descriptivos requieren expected_updated_at; bloqueo de fila evita sobrescrituras silenciosas.
  Archivo/restauración repetidos devuelven el estado actual sin duplicar eventos.
  CreateCommitment bloquea la fila de contacto hasta commit: se serializa con archivo.
- UC-008: sólo OPEN puede cancelarse; saldo e historial no cambian, aumenta version,
  audit/outbox y respuesta idempotente se confirman juntos. No se reabre CANCELLED.
  Cancel exige Idempotency-Key y expected_version. PATCH descriptivo exige version;
  permite concepto, notas y fecha en cualquier estado, sin tocar dinero/contacto/dirección.
  Mantiene ADR-0020 frente a la posibilidad antigua de editar monto antes de pagos.
- Resumen de contacto deriva por cobrar y por pagar por separado de compromisos abiertos;
  sus agregados viajan como strings exactos. El archivo no altera esos totales.
- El límite de cuerpo (16 KiB) se aplica al flujo ASGI real antes del router, incluso sin
  Content-Length. Timeout de lectura y rechazo de compresión no soportada.
- La recuperación financiera conserva la intención ante expiración de sesión, desconexión
  o fallo de limpieza local; no crea una clave nueva. No hay sincronización offline automática.
  Añadir notas opcionales no invalida hashes de CreateCommitment anteriores: ausencia y null
  son equivalentes; cualquier texto diferente conserva el conflicto de idempotencia.
- Exportación básica local: JSON del Workspace con lectura consistente, por puertos de cada
  módulo, sin credenciales ni auditoría sensible, con máximo explícito de 10,000 filas de negocio.
  Si excede el límite se rechaza antes de construir el documento. Esta entrega acotada concreta
  portabilidad para Core pequeño; no sustituye la exportación masiva CSV asíncrona planificada.
  Descarga autenticada y auditada, sin almacenamiento público ni fórmulas de hoja de cálculo.
  Límite adicional de 10 MiB; se rechaza explícitamente, sin truncar. Se incluyen vínculos
  derivados de reversión en ambos sentidos sin persistir una segunda fuente de verdad.
- Limpieza operativa explícita con dry-run por defecto: sesiones expiradas/revocadas hace
  más de 30 días y tokens de cuenta vencidos hace más de 7 días. Son ventanas operativas,
  no una política legal de retención. No borrar users, contactos, finanzas, audit, outbox ni
  idempotencia. Purga de cuenta y eliminación física siguen requiriendo su lifecycle separado.

## Validación y límites

Pruebas de aislamiento, conflicto/replay, concurrencia archivo/creación y cancelación/pago,
rollback, agregados exactos, exportación y limpieza. E2E de los flujos nuevos y fallos de navegador;
auditoría automatizada de accesibilidad, navegación con teclado y reflow. Carga sintética local
con tiempos medidos. No certifica dispositivos físicos, lector de pantalla ni capacidad de hosting.
No cambia decisiones de sesión, infraestructura, offline, Mobile ni Billing.
