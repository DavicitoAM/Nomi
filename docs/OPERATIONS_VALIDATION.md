# Ensayo de recuperación y HTTPS

Fecha: 2026-10-06. Alcance: entorno local aislado, con datos sintéticos.

Revalidación 2026-10-07 tras ADR-0022 y cryptography 50.0.2: aprobada en 25.941 s,
restauración/esquema 3.536 s y caída/recuperación 1.732 s. Evidencia:
`.local/operational-drills/05b94c65138f4b6c92d2c48318569ee7/report.json`.
Ver [cierre actualizado y carga local](CORE_LOCAL_COMPLETION.md). Los resultados siguientes
conservan el historial del primer ensayo.
El usuario confirmó que todavía no dispone de hosting ni SMTP. No se crearon recursos
de pago ni se enviaron correos externos. No se declara staging remoto validado.

## Resultado local

Ensayo aprobado: comparación exacta de las 13 tablas, siete comprobaciones de integridad,
TLS y cookies, recuperación tras parada inmediata de PostgreSQL y smoke contra la API restaurada.
El saldo de $7,500 MXN y los tres movimientos se conservaron; repetir el pago no creó otro movimiento.
Se recuperó el token pendiente de contraseña, se revocó la sesión y se conservaron las finanzas.

Primera ejecución completa aprobada: 22.323 s totales; respaldo/cifrado/comprobaciones negativas
0.264 s; restauración y revisión de esquema 2.732 s; recuperación tras parada abrupta 1.692 s.
Estos tiempos corresponden exclusivamente al conjunto sintético pequeño.
Evidencia local: `.local/operational-drills/28c0b3fdb85f4555be60df471c0eadb4/report.json`.

Repetición final tras reforzar limpieza y diagnósticos: aprobada en 22.671 s
(restauración/esquema: 2.594 s; recuperación del proceso: 1.580 s).
Evidencia: `.local/operational-drills/2523ab92fd69403a9f17aa4967f1dcfe/report.json`.
Se comprobó que los clústeres del ensayo quedaron detenidos y la API, web y buzón habituales
siguieron respondiendo HTTP 200. Ruff y formato aprobados. Las 88 pruebas backend y 8 E2E
son la validación anterior del producto; esta entrega agrega el ensayo operativo independiente,
sin modificar código de aplicación ni volver a declarar esas suites como ejecutadas.

En las ejecuciones iniciales se corrigieron dos problemas del propio ensayo: herencia de pipes
de `pg_ctl` en Windows y extensiones faltantes del certificado de prueba para la validación
estricta de Python. No se desactivó la validación TLS ni se cambió el comportamiento del producto.

## Repetir el ensayo

Requiere las dependencias de desarrollo del repositorio y binarios de PostgreSQL 18.

```powershell
.\.venv\Scripts\python.exe scripts/operational_drill.py
```

En otros sistemas, indicar la carpeta de binarios mediante `--pg-bin`.
El script necesita permisos para iniciar procesos y escuchar en loopback.

El ensayo crea un clúster nuevo bajo `.local/operational-drills/<id>/postgres`, en un puerto
libre y con dos bases sintéticas. No usa el `DATABASE_URL` del usuario, no copia datos de Nomi
y no detiene su PostgreSQL habitual. Al terminar cierra la API y el clúster que creó.
Los archivos se conservan para inspección; repetir crea un directorio nuevo.

## Qué se comprueba

1. Migrar una base vacía a la revisión actual y arrancar una API real con TLS,
   `ENVIRONMENT=staging` y cookies seguras. Es una configuración de prueba local,
   no un despliegue de staging. No se inicia el worker y el destino SMTP es loopback inactivo.
2. Registrar/verificar una cuenta sintética; crear contacto y compromiso de $10,000 MXN;
   pagar $2,500, revertir y pagar de nuevo. Saldo esperado: $7,500 y tres movimientos.
3. Validar la CA privada del ensayo y el hostname. Rechazar CA desconocida y hostname incorrecto,
   sin usar `verify=False`. No instalar la CA en Windows ni en el navegador.
4. Comprobar cookies Secure/HttpOnly/SameSite, omisión de cookies Secure en solicitudes HTTP
   construidas por el cliente, CSRF, Origin y bloqueo de cuenta sin verificar.
5. Exportar una instantánea consistente con `pg_dump -Fc --snapshot` y cifrarla con Fernet.
   Comparar conteo y SHA-256 de **todas** las filas de cada tabla en esa misma instantánea.
6. Rechazar respaldo truncado o clave equivocada. Restaurar el archivo cifrado desde disco
   en otra base usando `pg_restore --single-transaction --exit-on-error`.
   Ejecutar migraciones y `alembic check`; comparar todas las tablas y reglas financieras.
7. Abrir una transacción sin confirmar en la base restaurada; detener abruptamente sólo el
   clúster sintético con `pg_ctl -m immediate`, reiniciarlo y verificar recuperación WAL:
   cambios confirmados conservados y cambio sin commit descartado.
8. Arrancar un nuevo proceso de API sobre la base restaurada. Verificar dashboard, historial,
   sesión, replay de un pago anterior sin duplicarlo y recuperación de contraseña usando
   el token persistido y la clave de correo recuperada por separado. Comprobar revocación
   de sesión, rechazo de contraseña anterior y conservación de saldos.

El informe `report.json` guarda resultados, tiempos, conteos y hashes; no contiene contraseñas,
tokens ni cuerpos financieros. Los logs no incluyen accesos HTTP ni valores de parámetros SQL.

## Claves y límites del ensayo

Los datos son sintéticos. Para hacer el ensayo autocontenido, `backup.key` y `account-mail.key`
se conservan junto a sus artefactos locales, fuera de PostgreSQL. **Esto no es la custodia de
claves de producción**: allí deben residir en un gestor de secretos con acceso separado del
almacenamiento de respaldos. En Windows se heredan las ACL del directorio; `0600` no sustituye
una política de ACL. La CA de prueba y su certificado no son certificados públicos.

El dump se cifra en memoria; no se escribe una copia del archivo de respaldo sin cifrar.
La base restaurada contiene necesariamente datos descifrados. Este script es un ensayo pequeño,
no una herramienta de respaldo de bases grandes ni un scheduler de backups.

La comparación exacta incluye sesiones, idempotencia, auditoría, tokens y outbox. Se conserva
la sesión en el ensayo para probar su persistencia, y posteriormente se comprueba su revocación
al restablecer contraseña. En una recuperación operativa pública se deben revocar sesiones y
enlaces pendientes antes de reabrir acceso para evitar resucitar credenciales revocadas después
del punto de respaldo. Conservar las claves idempotentes y todo el historial financiero.

La parada inmediata ensaya caída del proceso de PostgreSQL; no reproduce pérdida eléctrica,
corrupción de almacenamiento, pérdida de región, failover administrado ni recuperación PITR.
Los tiempos de una base sintética no demuestran RTO de producción; este ensayo no demuestra
un RPO, frecuencia/retención de respaldos ni copia externa. Los objetivos alfa documentados
(RPO hasta 24 h y RTO hasta 8 h) siguen pendientes de validación operativa.

## Staging y correo real: procedimiento pendiente

Cuando existan hosting, dominio y proveedor SMTP:

1. Crear frontend, API, worker y PostgreSQL separados de producción. Usar datos sintéticos
   y un buzón controlado por el usuario. No copiar producción a staging.
2. Configurar dominio/certificado público y un solo origen web; enrutar `/api/v1` a la API.
   Mantener base y acceso interno a la API privados. Configurar la confianza del proxy
   según la topología real; no confiar indiscriminadamente en cabeceras reenviadas.
3. Configurar secretos en el proveedor: `DATABASE_URL`, `ACCOUNT_MAIL_KEY`, credenciales SMTP;
   `ENVIRONMENT=staging`, `COOKIE_SECURE=true`, `APP_ORIGIN=https://<dominio>`,
   `MAIL_BACKEND=smtp`, `SMTP_HOST`, `SMTP_PORT`, `SMTP_FROM`, `SMTP_USERNAME`, `SMTP_PASSWORD`.
   El worker y la API deben compartir la clave de correo. No publicar el buzón local.
4. Aplicar migraciones; comprobar readiness; ejecutar el flujo financiero y de cuenta en
   navegador de escritorio y móvil por HTTPS, incluida sesión, CSRF, reintento y reversión.
   Verificar redirección HTTP, certificado/cadena, cabeceras, proxies y política HSTS del dominio.
5. Validar remitente y DNS con el proveedor (SPF/DKIM/DMARC). Enviar verificación, recuperación
   y aviso de cambio únicamente al buzón de prueba autorizado. Confirmar recepción y apertura;
   aceptación por SMTP por sí sola no demuestra entregabilidad. Registrar Message-ID/estado,
   sin guardar el token en evidencias. Probar reintento ante interrupción temporal del proveedor.
6. Configurar respaldos administrados cifrados, custodia separada de claves, retención y alertas.
   Restaurar uno en un entorno aislado sin consumidores de correo activos. Validar conteos,
   invariantes y smoke; medir tiempos y antigüedad del respaldo. No promover automáticamente
   esa base ni reactivar efectos externos. Revisar sesiones/enlaces antes de abrir acceso.
7. Registrar evidencia de CI remoto, TLS, entrega/recepción y restauración del proveedor.
   Sólo entonces revisar el estado provisional de la estrategia de sesión.

## Referencias

- [Política del proyecto](../NOMI_MEMORIA_TECNICA_v0.1/08_OPERATIONS/04_BACKUP_RECOVERY.md).
- [Despliegue y ambientes](../NOMI_MEMORIA_TECNICA_v0.1/08_OPERATIONS/03_DEVOPS_DEPLOYMENT.md).
- [ADR-0021](adr/0021-account-lifecycle-and-mail-worker.md).
- [PostgreSQL 18: pg_dump](https://www.postgresql.org/docs/18/app-pgdump.html) y
  [pg_restore](https://www.postgresql.org/docs/18/app-pgrestore.html). El formato custom permite
  restauración selectiva; el dump lógico no incluye roles globales ni sustituye el respaldo
  administrado/PITR de producción.
