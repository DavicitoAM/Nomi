# Rediseño y revisión pendiente

Fecha: 2026-10-06. Alcance: nueva distribución visual y paleta azul tinta/lavanda elegida por el usuario. La revisión de arquitectura es un diagnóstico para la siguiente etapa; no modifica decisiones aceptadas.

## UI entregada

- Navegación horizontal en escritorio y fija inferior en móvil.
- Saldos por cobrar y por pagar destacados, sin compensación; vencimientos en bloque independiente.
- Accesos desde las tarjetas a filtros de pendientes, incluido próximo vencimiento.
- Lista a todo el ancho, búsqueda agrupada con filtros y selección accesible mediante `aria-pressed`.
- Vencimiento visible también en móvil; moneda visible en las tarjetas.
- Contactos, acceso y formularios usan la misma paleta. Historial interpreta instantes con la zona del Workspace.
- Enlace para saltar al contenido, foco visible, Escape en diálogos y estados de carga/error/vacío.
- Aviso visible cuando búsqueda/filtros sólo abarcan páginas cargadas; carga adicional de nombres de contactos.

No hay migraciones ni cambios al contrato HTTP en esta entrega. Evidencia: build de producción, TypeScript y E2E de escritorio/móvil con registro, captura, pago, historial, navegación, filtros y cierre de sesión; revisión visual de capturas. No equivale a auditoría exhaustiva WCAG ni a pruebas en dispositivos iOS reales.

## Fallos y limitaciones observados en código

Son hallazgos por inspección de los archivos indicados; no todos se reprodujeron mediante inyección de fallos. P1 requiere atención antes de uso con información real; P2 debe corregirse al completar Core.

| Prioridad | Hallazgo e impacto | Evidencia | Próximo cambio propuesto |
| --- | --- | --- | --- |
| P1 | La clave idempotente vive en `useRef`: si un pago se confirma en servidor pero se pierde la respuesta, cerrar/reabrir el formulario o recargar genera otra clave. Si queda saldo suficiente, repetirlo puede producir otro abono. La protección del servidor funciona mientras se conserva la clave. | `apps/web/src/features/commitments/forms.tsx`, `PaymentForm` y `CommitmentForm` | Conservar y reconciliar la intención de una operación con resultado incierto; probar respuesta perdida, recarga y reapertura. Diseñar alcance y privacidad de persistencia conforme al ADR de offline, sin introducir todavía sincronización completa. |
| P1 | La suma del Dashboard no tiene límite de representación exacta en JavaScript. Cada operación está limitada, pero suficientes operaciones pueden superar `Number.MAX_SAFE_INTEGER`; JSON se interpreta como `number` y puede perder unidades menores. | `apps/api/app/modules/commitments/infrastructure/repository.py`, `summary`; `apps/web/src/lib/api.ts`, `money` | Definir contrato de serialización exacta de agregados y pruebas de frontera antes de escalar. Requiere evaluar API/cliente y documentar la decisión, no cambiar a strings silenciosamente. |
| P2 | Búsqueda y filtros se aplican después de paginar; un total global puede mostrar vencidos aunque la página cargada no los contenga. La UI ahora explica ese alcance. | `apps/web/src/app/page.tsx`, `filtered` y consultas por cursor | Incorporar búsqueda/filtros en una consulta del servidor con aislamiento y cursor coherente; sincronizar OpenAPI. |
| P2 | Un pendiente puede mostrar “Contacto” hasta cargar la página correspondiente de contactos. Añadir un botón permite recuperarlo, pero no resuelve la relación de forma robusta. | `apps/web/src/app/page.tsx`, `names` | Resolver datos de presentación del contacto en una consulta autorizada; evitar descargar todo el catálogo o introducir N+1. |
| P2 | El historial pagina por UUID aleatorio, mientras la UI ordena por `created_at` sólo lo descargado. Cargar otra página puede intercalar movimientos anteriores y no permite leer un orden temporal continuo. | `apps/api/app/modules/transactions/infrastructure/repository.py`, `history`; `Detail` en `page.tsx` | Cursor estable compuesto por fecha y UUID; definir si manda fecha de registro o de ocurrencia y probar empates/paginación. |
| P2 | El texto de error de red promete no duplicar abonos incluso para registro/contactos, que no son idempotentes. La promesa tampoco cubre la pérdida de intención indicada arriba. | `apps/web/src/lib/api.ts`, bloque `catch` | Mensajes por operación y estado de confirmación; prueba de reintento de contactos sin imponer unicidad prohibida por el dominio. |
| P2 | El Dashboard conserva montos correctos, pero “Vencidos” y “Por vencer” suman ambas direcciones. No existe desglose visual de por cobrar/por pagar en esas categorías. | `summary` y `DashboardOut` | Evaluar desglose de consulta para evitar ambigüedad de seguimiento; nunca presentar la suma como saldo neto. |

## Alcance funcional aún pendiente

Son funcionalidades ausentes, no regresiones del rediseño:

1. Reversión de pagos, cancelación y archivo/restauración; no se debe editar ni borrar movimientos como sustituto.
2. Verificación y recuperación de cuenta, tokens de un uso y revocación tras cambio de contraseña. Actualmente se permite operar en `pending_verification`.
3. Consumidor operativo de outbox, recordatorios y política de retención/purga.
4. Exportación y offline por etapas, después de resolver operaciones online con resultado incierto.

## Arquitectura y operación: siguiente revisión

- `shared/ports.py` usa `Any` para todos los repositorios. Definir puertos tipados propiedad de cada módulo y mantener UnitOfWork como composición transaccional.
- `page.tsx` concentra consultas, presentación y detalle. Separar por features una vez aceptada la nueva distribución; evitar otra reorganización visual simultánea.
- Los métodos de consulta de varios routers acceden al UoW directamente. Evaluar queries de aplicación consistentes cuando se incorporen filtros y proyecciones; no añadir abstracciones sin un caso de uso.
- Completar observabilidad: el logger de solicitudes no configura su salida propia y los spans usan sólo OpenTelemetry API. Configurar logs estructurados sin PII, proveedor/exportador y mediciones antes de afirmar cobertura operativa.
- El rate limiter es por proceso/IP; detrás del proxy local las peticiones pueden compartir IP. Definir comportamiento con el proxy de despliegue y no confiar en headers arbitrarios. Redis sólo si una necesidad demostrada lo requiere.
- El límite de tamaño comprueba `Content-Length`; no cubre por sí solo un cuerpo enviado sin esa cabecera. Revisar límite efectivo de servidor/proxy y pruebas de streaming antes de exposición pública.
- Confirmar CI remoto, staging/TLS, smoke tests, backup/restore y revisión completa de accesibilidad. Los resultados locales no prueban esas condiciones.

## Decisiones documentales que siguen abiertas

- Sesión opaca continúa provisional (ADR-0005/0019).
- Definir reversión de un compromiso cancelado antes de implementar ese caso.
- Resolver edición de monto inicial frente a la regla “el saldo nunca cambia solo”.
- Revisar `timing_state=null` en cerrados y el snapshot de respuesta idempotente del ADR-0019 provisional.

Orden recomendado tras aprobar la UI: continuidad idempotente y precisión monetaria → consultas/paginación/historial → operaciones restantes de Core → ciclo de cuenta → observabilidad y staging → offline gradual. Esta lista no autoriza cerrar decisiones provisionales como aceptadas.
