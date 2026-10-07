# Cierre funcional y calidad local de Nomi Core

Fecha: 2026-10-07. Implementación y evidencia local; no liberación de producción.
Decisiones: [ADR-0022](adr/0022-core-lifecycle-and-local-quality.md), que complementa
[ADR-0020](adr/0020-core-reconstruction-contracts.md) y
[ADR-0021](adr/0021-account-lifecycle-and-mail-worker.md).

## Capacidades completadas

| Capacidad | Comportamiento y protección |
| --- | --- |
| Contactos | Detalle, búsqueda, edición, notas, archivo/restauración y resumen por dirección. Archivo no cambia dinero; bloqueo de fila serializa archivo y creación de compromisos. Edición detecta versiones obsoletas. |
| Compromisos | Edición de concepto, notas y fecha. Cancelación explícita de abiertos, idempotente y versionada; conserva saldo e historial y excluye agregados activos. No reabre cancelados ni permite editar importes. |
| Recuperación web | Conserva la misma intención ante pérdida de respuesta, sesión vencida y desconexión. Almacenamiento bloqueado/lleno impide enviar; dos pestañas no confirman al mismo tiempo. No equivale a una cola offline completa. |
| Exportación | Descarga JSON autenticada y auditada de contactos, compromisos y movimientos del Workspace. Instantánea consistente, relaciones de reversión en ambos sentidos y ningún secreto de cuenta. |
| Limpieza operativa | CLI con simulación por defecto, lotes de hasta 1,000 por tabla y eliminación sólo de credenciales antiguas. No purga finanzas, auditoría, outbox ni idempotencia. |
| Seguridad | Límite real de 16 KiB antes de parsear, incluso sin Content-Length; tiempo máximo de lectura de 10 s y rechazo de compresión no soportada. Auditorías de dependencias, SAST y secretos repetibles. |
| Accesibilidad | Etiquetas de errores, títulos de diálogo únicos, regreso del foco, ciclo Tab/Shift+Tab y Escape. Comprobaciones axe en los estados ejercitados y reflow a 320 px. |

La migración aditiva `4eb83021fb32` incorpora notas y `contacts.updated_at`.
Se aplicó a las bases locales; Alembic no detectó diferencias pendientes. No se reescribieron
migraciones anteriores para introducir estos campos. La normalización de CreateCommitment
conserva reintentos antiguos sin el campo notes; notes ausente y null son equivalentes,
pero un texto diferente produce conflicto de idempotencia.

## Evidencia

- Backend: 113 pruebas aprobadas en la suite completa y dos pruebas adicionales de
  concurrencia archivo/creación aprobadas después: **115 casos aprobados** en total.
  Incluyen aislamiento, sobrepago, reversión/doble reversión, carreras, rollback de efectos,
  migraciones con datos, snapshot de exportación, límites y limpieza.
- Browser: **16 E2E aprobados en 39.7 s**, con build de producción local y ocho escenarios
  en escritorio y viewport móvil. Las pruebas crean cuentas sintéticas. Detectaron y permitieron
  corregir la salida del foco al retroceder desde el primer control de un diálogo.
  Tras separar visualmente el botón de exportación de su explicación, build y los dos E2E
  afectados volvieron a pasar (10.5 s). La captura móvil se revisó a 320 px.
- TypeScript, build Next.js, Ruff y formato aprobados. Contrato OpenAPI y tipos regenerados.
- Respaldos: ensayo actualizado aprobado en **25.941 s**; restauración y esquema **3.536 s**;
  recuperación tras caída **1.732 s**. Comparación de 13 tablas y siete invariantes.
  Evidencia local: `.local/operational-drills/05b94c65138f4b6c92d2c48318569ee7/report.json`.
- Carga: 5,001 contactos, 10,001 compromisos y 10,003 movimientos iniciales; ocho clientes,
  360 lecturas y 100 pagos. Todos los pagos conservan saldo/historial y restricciones.
  Evidencia: `.local/operational-drills/bb925a894c59445d9aad691be9f4448e/load-report.json`.

| Operación de carga | Muestras | p95 local |
| --- | ---: | ---: |
| Dashboard | 120 | 71.47 ms |
| Búsqueda | 120 | 83.77 ms |
| Historial | 120 | 74.12 ms |
| Pago | 100 | 81.61 ms |

Son mediciones sintéticas locales con HTTPS y conexiones persistentes, no capacidad ni SLO
de producción. El presupuesto de regresión del ensayo es 3,000 ms p95. Los scripts crean
y detienen su propio clúster y nunca toman la base habitual como destino de carga/restore.

## Seguridad reproducible

Se actualizó cryptography de 49.0.0 a 50.0.2 tras detectar
[GHSA-g6cj-pr64-35w5](https://github.com/pyca/cryptography/security/advisories/GHSA-g6cj-pr64-35w5).
El aviso afecta PKCS7; Nomi utiliza Fernet, pero se actualizó igualmente la dependencia
y se volvió a probar cifrado/restauración. pip-audit y npm audit quedaron sin vulnerabilidades
conocidas en el alcance consultado. Eso no demuestra ausencia de vulnerabilidades desconocidas.

Bandit revisa código de aplicación; se documenta una supresión B105 por el valor `None` del
token de una notificación sin enlace. No es una contraseña incrustada. El escaneo de secretos
usa detect-secrets sin verificaciones de red y sólo archivos versionables (incluidos nuevos).
La baseline conserva hashes, tipo, ubicación y motivo de los falsos positivos revisados:
credenciales sintéticas de pruebas/desarrollo, IDs Alembic y etiquetas internas de correo.
Resultado final: 245 archivos versionables escaneados, 20 coincidencias revisadas en baseline
y cero coincidencias sin revisar.
No se ignoraron directorios de código ni familias enteras de detectores. Un valor sintético
nuevo hizo fallar el control; retirarlo restauró el resultado aprobado. El escaneo no recorre
el historial Git ni archivos ignorados con secretos locales deliberados.

```powershell
python -m venv .local/security-tools
.\.local\security-tools\Scripts\python.exe -m pip install -r requirements-security.txt
.\.local\security-tools\Scripts\python.exe -m pip_audit -r requirements.lock --no-deps --disable-pip
.\.local\security-tools\Scripts\python.exe -m bandit -r apps/api/app -q
.\.local\security-tools\Scripts\python.exe scripts/check_secrets.py
npm.cmd audit --audit-level=low
```

CI incorpora esos controles y los E2E con axe. Está configurado; no se declara una ejecución
remota aprobada. Los resultados locales de dependencias están en `.local/pip-audit-final.json`
y `.local/npm-audit.json`; SAST en `.local/bandit-final.json`.

## Uso y límites explícitos

- Contactos → seleccionar → Editar, Archivar o Restaurar. El resumen mantiene por cobrar y
  por pagar separados. Los contactos archivados conservan sus pendientes existentes.
- Pendiente → Editar pendiente o Cancelar pendiente. Cancelar requiere confirmación y conserva
  el importe sin crear un pago ficticio. Para corregir pagos se sigue usando Revertir abono.
- Exportar mis datos descarga `nomi-workspace.json`, con máximo total de 10,000 filas de negocio
  y 10 MiB. Exceder cualquiera devuelve `EXPORT_LIMIT_EXCEEDED`; nunca entrega datos truncados.
  No es un respaldo restaurable de la cuenta ni implementa importación/CSV masivo.
- `python -m app.maintenance` simula; `python -m app.maintenance --apply` borra hasta 1,000
  sesiones y 1,000 tokens de cada tipo por ejecución. Sólo sesiones expiradas/revocadas hace
  más de 30 días y tokens vencidos hace más de 7 días. En la base habitual se ejecutó únicamente
  simulación: cero elegibles y cero borrados. El modo apply se probó en `nomi_test`.
- `python scripts/load_drill.py` repite carga; `python scripts/operational_drill.py` repite
  respaldo/restauración, caída y TLS. No representan monitoreo ni backups programados.

## Pendiente fuera de este cierre

Hosting/dominio/SMTP y entregabilidad real, ejecución remota de CI, smoke de staging,
respaldos del proveedor y custodia de claves, alertas y telemetría desplegada, SLO del hosting,
lector de pantalla y dispositivos físicos. Axe y viewports no sustituyen esas validaciones.
El rate limiter sigue limitado a un proceso. Persiste el aviso de deprecación HTTPX/TestClient
de Starlette; la suite pasa. La sesión opaca sigue provisional para liberación pública.

PWA/offline completo, purga de cuenta/retención general, exportación masiva y demás fases
posteriores conservan su propio alcance. Mobile, AdMob y Play Billing no se iniciaron.
