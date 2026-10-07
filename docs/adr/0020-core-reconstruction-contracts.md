# ADR-0020 — Cierre del recorrido financiero Core

Estado: **ACEPTADA**, 2026-10-06. El usuario delegó expresamente las decisiones y la implementación.

## Problema y contexto

El brief detecta reversión ausente, intención volátil del navegador, agregados potencialmente
inexactos y diferencias entre UC-006, ADR-0013/0016 y ADR-0019. Conservar el monolito y los
datos existentes; completar primero RegisterUser → Contact → Commitment → Payment →
ReversePayment → Dashboard. No habilitar Mobile, AdMob o Billing.

## Decisiones

1. ReversePayment es el nombre del caso que implementa ReverseTransaction de UC-006:
   POST `/api/v1/transactions/{transaction_id}/reverse`, Idempotency-Key UUID y
   expected_version obligatorios. Nota opcional. Monto/moneda/compromiso derivados del pago.
   Reversión completa, positiva, única e inmutable; nunca revertir una reversal.
   PAID vuelve a OPEN; CANCELLED rechaza la operación. El servidor asigna la fecha de reversión.
2. Pago/reversión, CAS de Commitment, Audit, Outbox y snapshot idempotente son atómicos.
   Autorización en cada replay; deduplicación antes de versión/estado. Conservar los registros
   idempotentes durante la vida del Workspace: no caducar claves automáticamente.
3. Navegador conserva en IndexedDB una sola intención financiera pendiente por usuario/Workspace,
   con clave, ruta y body mínimo necesario para reproducirla. Sin tokens ni cookies.
   Antes de enviar debe persistirla; no enviar si el almacenamiento falla. Recuperación explícita
   tras recarga mediante la misma clave/body. No permitir otra operación financiera hasta resolverla.
   Web Locks serializa pestañas del mismo origen. Logout no borra una operación incierta;
   otra cuenta no la consulta ni reenvía. Se elimina sólo al confirmar éxito o rechazo definitivo.
   No es sincronización offline ni autorización: el backend siempre autoriza la sesión actual.
4. PostgreSQL sigue usando enteros. Los cuatro agregados monetarios de Dashboard se serializan
   como strings decimales no negativos en unidades menores, y la web formatea con BigInt.
   Los montos individuales continúan como JSON integer, limitados a 9e12 unidades menores.
   Este refinamiento sustituye el transporte JSON numérico de agregados; no altera ADR-0009.
5. Historial ordenado por created_at ascendente y UUID como desempate. Cursor UUID resuelve
   su posición sólo dentro del compromiso autorizado. occurred_at se muestra por separado.
   DTO incluye reversal_of_transaction_id y reversed_by_transaction_id derivado, sin nueva columna.
6. Se aceptan registro con sesión/audit/outbox en un commit y timing_state=null para cerrados.
   Sustituye esos puntos provisionales de ADR-0019 y refina ADR-0013 para expresar «no aplica».
   Sesión opaca sigue provisional hasta recuperación/verificación y validación TLS.
7. Cuentas pending_verification pueden operar sólo en development. Fuera de desarrollo,
   autenticar permite consultar perfil/cerrar sesión pero no operar datos de negocio sin verificación.
   No declarar liberable producción mientras falte el flujo completo de verificación/recuperación.
8. Monto original, moneda y dirección permanecen inmutables en la API actual. Cancelar mantiene
   saldo/historial y exige versión; no habilita borrado ni reapertura implícita.
   La jerarquía de AGENTS prevalece; saldo inicial se establece al crear Commitment,
   los cambios posteriores se explican con payment/reversal.

## Alternativas y costes

Rehacer el stack no corrige estas brechas. Guardar sólo una clave local impide reproducir el
request normalizado; guardar nada pierde la intención tras recarga. IndexedDB guarda temporalmente
datos financieros: requiere dispositivo confiable, CSP, aislamiento y limpieza tras resolución.
Sin soporte de almacenamiento/Web Locks la captura financiera falla explícitamente, no pierde garantías.
Los strings de agregados rompen clientes que esperen number: regenerar OpenAPI y cliente juntos.
No truncar ni redondear agregados para conservar compatibilidad. No expirar automáticamente una
intención incierta evita duplicados tardíos a cambio de retención hasta reconciliar.

## Impacto y migración

Dominio Commitment, aplicación/repositorio/API Transactions, Dashboard DTO, formularios e historial,
cliente generado y pruebas. La FK de reversión ya existe: no necesita columna ni migración nueva.
No eliminar datos, reescribir migraciones anteriores ni cambiar la paleta/UI general.
ADR-0014/0015/0016/0017/0018 se preservan. El brief queda como diagnóstico histórico.

## Validación requerida

$10,000 → $7,500 → $10,000; pago total/reapertura, doble reversión, reversión de reversal,
cancelados, versión, sesiones/CSRF, otro Workspace, retries, concurrencia y rollback audit/outbox.
E2E escritorio/móvil y recuperación de respuesta perdida después de recarga, sin duplicados.
Agregados mayores a 2^53 conservan el último centavo. No equivale a certificación de producción.
