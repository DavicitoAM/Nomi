# ADR-0019 — Contratos de la primera slice

Estado: **PROVISIONAL**, validación local. Complementa ADR-0005, 0013, 0014 y 0016; no los reemplaza.

## Contexto

El repositorio necesita demostrar el recorrido de AGENTS.md §34. Los documentos dejan abiertos el transporte de version, la reproducción de idempotencia, el timing de compromisos cerrados y ciertos detalles de sesión/registro.

## Implementación evaluada

1. Sesión opaca PostgreSQL y CSRF ligado a sesión; cookies HttpOnly/Secure/SameSite. Secure se desactiva únicamente en desarrollo HTTP local.
2. `expected_version` obligatorio en body de Payment, sin contrato If-Match paralelo.
3. Reserva idempotente atómica y snapshot del DTO de respuesta en JSONB. La clave continúa scoped por Workspace/operation y su hash incluye el ID de recurso. Errores con rollback no consumen la clave.
4. Compromisos cerrados devuelven `timing_state=null`, expresando que no requieren seguimiento temporal activo.
5. Registro extiende el commit de User/Workspace/Membership a Session, Audit y Outbox para no perder intención de verificación. No envía correo dentro de la transacción.
6. MXN y America/Mexico_City son valores iniciales de Workspace; no se expone cambio de moneda ni edición de monto.

## Alternativas y costes

- Tokens en cookies siguen siendo alternativa de ADR-0005. Sesiones opacas añaden consulta de servidor y requieren una política de limpieza futura.
- Guardar sólo el ID de recurso ahorra almacenamiento pero no reproduce el resultado original después de cambios. El snapshot conserva datos financieros del DTO: exige aislamiento, retención y purga coherentes. No almacena la solicitud original ni secretos.
- Mantener el registro dividido exige recuperar de forma explícita fallos entre commits. Ampliar atomicidad simplifica la primera slice; el correo externo sigue fuera.
- Calcular timing de cerrados como si siguieran activos confundiría la UI. `null` obliga al cliente a contemplar que no aplica.

## Validación y revisión

Pruebas de replay después de pagos adicionales, misma clave concurrente, rollback, cookie/CSRF y pagos exactos. La decisión de sesión sigue provisional hasta validar staging/TLS y el ciclo completo de recuperación/verificación. Reversión de cancelados y edición financiera siguen abiertas y no se implementan aquí.
