# AGENTS.md — Nomi

Este archivo define cómo deben trabajar los asistentes de IA y agentes de desarrollo dentro del repositorio de **Nomi**.

Su objetivo es evitar decisiones improvisadas, sobreingeniería, inconsistencias entre módulos y cambios que contradigan la memoria técnica del proyecto.

---

# 1. Regla principal

La documentación del repositorio es la fuente principal de verdad del proyecto.

Antes de implementar, modificar o eliminar comportamiento, revisar primero la documentación relevante dentro de:

- `README.md`
- `DOC_INDEX.md`
- `TRACEABILITY.md`
- `docs/`
- `adr/` o `docs/adr/`
- memoria técnica de Nomi, si se conserva como carpeta independiente
- especificaciones de dominio, casos de uso, API, datos, seguridad, pruebas y arquitectura

No asumir que el README contiene todo el detalle.

No inventar decisiones cuando la documentación ya define el comportamiento.

Si existe una contradicción entre documentos, no resolverla silenciosamente. Identificarla, explicar el impacto y proponer una solución antes de modificar una decisión establecida.

---

# 2. Precedencia documental

Cuando exista información duplicada o diferente entre documentos, usar este orden de precedencia:

1. Decisiones marcadas explícitamente como **ACEPTADA**.
2. Especificaciones de **Nomi Core v0.1**.
3. ADR aceptados.
4. Documentos especializados de dominio, datos, API, seguridad y arquitectura.
5. PRD y alcance funcional.
6. Roadmap.
7. README y documentos de resumen.

Interpretación de estados:

- **ACEPTADA**: debe respetarse salvo que se apruebe explícitamente un cambio.
- **PROVISIONAL**: puede revisarse antes o durante implementación si existe una razón técnica clara.
- **PLANIFICADA**: pertenece a una fase posterior y no debe implementarse anticipadamente.

Cuando una decisión aceptada necesite cambiar, crear o actualizar el ADR correspondiente.

---

# 3. Qué es Nomi

Nomi es un SaaS web progresivo, mobile-first y tolerante a conectividad inestable para registrar, consultar y dar seguimiento a dinero pendiente.

El núcleo del producto debe permitir responder rápidamente:

- cuánto me deben;
- cuánto debo;
- qué compromisos requieren atención;
- qué ocurrió con cada saldo.

Nomi no debe convertirse durante el MVP en:

- ERP;
- sistema contable;
- sistema fiscal;
- facturación electrónica;
- pasarela de pagos;
- integración bancaria;
- buró de crédito;
- CRM generalista;
- plataforma de cobranza agresiva;
- arquitectura de microservicios.

La simplicidad del producto es una restricción de diseño, no una carencia temporal.

---

# 4. Principios del producto

Toda implementación debe favorecer:

- captura rápida;
- claridad sobre complejidad;
- mobile-first;
- accesibilidad;
- privacidad por diseño;
- portabilidad de datos;
- tolerancia a conexión inestable;
- historial financiero explicable;
- arquitectura simple y modular.

No agregar funcionalidades únicamente porque sean técnicamente interesantes.

No introducir infraestructura futura antes de que exista una necesidad demostrada.

---

# 5. Arquitectura general

Nomi se construye como un **monolito modular API-first dentro de un monorepo**.

Stack objetivo:

## Frontend

- Next.js
- TypeScript
- Tailwind CSS
- TanStack Query
- React Hook Form
- Zod
- IndexedDB
- Service Worker / PWA

## Backend

- Python
- FastAPI
- Pydantic
- SQLAlchemy 2.x
- Alembic
- PostgreSQL

## Infraestructura

- Docker
- CI/CD
- proveedor administrado para MVP
- CDN/WAF/DNS perimetral
- almacenamiento compatible con S3 cuando existan adjuntos
- Redis únicamente cuando una necesidad real lo justifique
- worker cuando se implementen tareas asíncronas

No introducir microservicios en el MVP.

---

# 6. Módulos del backend

Los principales módulos son:

```text
identity
workspaces
contacts
commitments
transactions
reminders
reporting
billing
audit
```

Cada módulo debe mantener una responsabilidad clara.

Patrón interno esperado:

```text
module/
├── domain/
├── application/
├── infrastructure/
└── api/
```

Responsabilidades:

```text
domain
    Entidades, value objects, invariantes y reglas puras.

application
    Casos de uso, orquestación y puertos/interfaces.

infrastructure
    Repositorios, persistencia y adaptadores externos.

api
    Rutas HTTP, schemas de transporte y dependencias de FastAPI.
```

No mover lógica de dominio hacia routers, modelos ORM o componentes frontend por conveniencia.

---

# 7. Regla de acoplamiento entre módulos

Un módulo no debe modificar directamente las tablas, entidades internas o invariantes propiedad de otro módulo salvo que exista una decisión documentada que lo permita.

Preferir comunicación mediante:

- casos de uso;
- interfaces/puertos;
- repositorios;
- eventos;
- outbox cuando corresponda.

Ejemplos:

```text
transactions
NO debe modificar contacts directamente.

dashboard/reporting
NO debe modificar compromisos.

reminders
NO debe cambiar un compromiso a PAID.

contacts
NO debe calcular pagos.
```

El monolito puede compartir una transacción de base de datos cuando el caso de uso lo requiera, pero eso no elimina los límites de responsabilidad.

---

# 8. Núcleo de dominio

Cadena conceptual principal:

```text
User
  ↓
Membership
  ↓
Workspace
  ↓
Contact
  ↓
Commitment
  ↓
Transaction
```

Interpretación:

```text
User
    Identidad autenticable.

Membership
    Relación del usuario con un Workspace.

Workspace
    Frontera de propiedad y aislamiento de datos.

Contact
    Persona u organización relacionada.

Commitment
    Obligación económica pendiente.

Transaction
    Operación que explica una modificación del saldo.
```

Todo comportamiento nuevo debe respetar esta separación.

---

# 9. Workspace y propiedad de datos

Los datos de negocio pertenecen al **Workspace**, no directamente al User.

En Core v0.1:

```text
1 User
→ 1 Membership OWNER
→ 1 Workspace personal
```

La estructura debe quedar preparada para varios miembros en el futuro, sin implementar equipos antes de tiempo.

Nunca confiar en un `workspace_id`, `owner_id` o rol recibido desde el frontend para decidir propiedad.

El backend debe resolver el Workspace desde la sesión autenticada y la Membership.

Toda consulta de un recurso perteneciente a un Workspace debe incluir el aislamiento correspondiente.

Ejemplo conceptual:

```sql
WHERE id = :resource_id
AND workspace_id = :current_workspace_id
```

Un recurso de otro Workspace debe tratarse como no accesible y no debe filtrarse su existencia.

---

# 10. Contact

`Contact` representa a una persona u organización relacionada con compromisos financieros.

No representa de forma permanente:

- cliente;
- proveedor;
- deudor;
- acreedor.

Ese rol surge de `Commitment.direction`.

Campos base:

```text
id
workspace_id
name
phone?
email?
notes?
archived_at?
created_at
updated_at
```

Reglas:

- `name` es obligatorio.
- teléfono y correo son opcionales.
- no imponer unicidad por nombre.
- no imponer unicidad a teléfono o correo del contacto.
- archivar no cancela compromisos.
- archivar no modifica saldos.
- un contacto archivado no recibe nuevos compromisos desde el flujo normal.
- restaurar contacto no altera historial.

El saldo del contacto es derivado de sus compromisos y no debe persistirse como segunda fuente de verdad.

---

# 11. Commitment

`Commitment` representa dinero pendiente.

Campos principales de Core v0.1:

```text
id
workspace_id
contact_id
direction
original_amount_minor
balance_minor
currency_code
concept?
notes?
due_date?
lifecycle_status
version
created_at
updated_at
deleted_at?
```

Dirección:

```text
receivable = me deben
payable    = yo debo
```

Estados persistidos:

```text
open
paid
cancelled
```

Estados calculados:

```text
payment_state:
    pending
    partial
    paid

timing_state:
    no_due_date
    upcoming
    due_soon
    overdue
```

No persistir `overdue`, `partial`, `due_soon` u otras condiciones que puedan derivarse.

Reglas financieras:

```text
original_amount_minor > 0

0 <= balance_minor <= original_amount_minor

OPEN
→ balance > 0

PAID
→ balance = 0

CANCELLED
→ balance puede ser > 0
  pero deja de participar en agregados activos
```

Cancelar no significa pagar.

Cancelar tampoco elimina el historial.

---

# 12. Dinero y currency_code

El dinero se almacena como enteros en unidad monetaria menor.

Ejemplo:

```text
$1,250.50 MXN
→ 125050
```

Usar PostgreSQL `BIGINT`.

No usar:

```text
FLOAT
REAL
DOUBLE PRECISION
```

Para Core v0.1:

```text
currency_code VARCHAR(3)
CHECK uppercase ISO-like format
```

No usar PostgreSQL ENUM para monedas.

El MVP utiliza una moneda principal por Workspace.

Regla de dominio:

```text
Transaction.currency_code
==
Commitment.currency_code
==
Workspace.currency_code
```

La moneda principal no debe cambiar libremente después de existir información financiera sin un proceso de migración explícito.

---

# 13. Estados y ENUM

En Python pueden utilizarse `Enum` para tipado y validación.

En PostgreSQL, para Core v0.1, preferir:

```text
VARCHAR + CHECK
```

en lugar de ENUM nativo.

Ejemplos:

```text
direction
    receivable
    payable

lifecycle_status
    open
    paid
    cancelled

transaction.type
    payment
    reversal
```

Motivo: conservar integridad de datos sin dificultar migraciones futuras del dominio.

---

# 14. Transaction

En Core v0.1, una Transaction financiera puede ser:

```text
payment
reversal
```

No implementar todavía ajustes financieros avanzados salvo decisión posterior documentada.

Campos principales:

```text
id
commitment_id
type
amount_minor
currency_code
note?
occurred_at
created_by
reversal_of_transaction_id?
created_at
```

`amount_minor` siempre es positivo.

Una reversión NO utiliza monto negativo.

Ejemplo:

```text
PAYMENT
amount = 250000

REVERSAL
amount = 250000
reversal_of_transaction_id = <payment_id>
```

El signo semántico lo determina `type`.

---

# 15. Reversiones

Los movimientos financieros no se editan ni eliminan silenciosamente.

Una corrección se registra mediante una nueva Transaction de tipo `reversal`.

`reversal_of_transaction_id` debe ser una FK autorreferenciada hacia `transactions.id`.

Debe ser nullable para pagos normales y UNIQUE para impedir dos reversiones del mismo movimiento.

Regla conceptual:

```text
PAYMENT
→ reversal_of_transaction_id IS NULL

REVERSAL
→ reversal_of_transaction_id IS NOT NULL
```

El caso de uso `ReverseTransaction` debe comprobar además:

```text
original.type == payment

same commitment

same currency

same amount

same workspace through commitment

original has no previous reversal
```

Los valores de la reversión deben derivarse del movimiento original; no confiar en monto o moneda enviados libremente por el cliente.

No usar `reversed_at` como una segunda fuente de verdad si `reversal_of_transaction_id` ya expresa formalmente la relación.

---

# 16. Regla financiera principal

**El saldo nunca cambia solo.**

Todo cambio de saldo debe poder explicarse mediante una operación de dominio registrada.

En Core v0.1:

```text
saldo inicial
= original_amount_minor

PAYMENT
→ reduce balance

REVERSAL de PAYMENT
→ restaura el importe correspondiente
```

Nunca ejecutar un cambio arbitrario del tipo:

```sql
UPDATE commitments
SET balance_minor = ...
```

sin una operación financiera que explique ese resultado.

El historial debe permitir explicar el saldo actual.

---

# 17. Atomicidad

Las operaciones financieras deben ejecutarse dentro de una transacción de base de datos.

Ejemplo conceptual de `RegisterPayment`:

```text
BEGIN

INSERT transaction

UPDATE commitment balance/version

INSERT audit_event

INSERT outbox_event

COMMIT
```

Si cualquiera de las operaciones críticas falla:

```text
ROLLBACK
```

Nunca permitir un estado donde:

- existe movimiento pero no cambió saldo;
- cambió saldo pero no existe movimiento;
- se confirma la operación de negocio y se pierde el evento requerido.

---

# 18. Concurrencia

`Commitment.version` implementa bloqueo optimista.

Base:

```text
version INTEGER NOT NULL DEFAULT 1
CHECK version >= 1
```

Las actualizaciones sensibles deben comprobar la versión esperada.

Ejemplo conceptual:

```sql
UPDATE commitments
SET
    balance_minor = :new_balance,
    version = version + 1
WHERE id = :id
  AND workspace_id = :workspace_id
  AND version = :expected_version;
```

Si ninguna fila fue actualizada:

```text
VERSION_CONFLICT
```

No resolver silenciosamente conflictos financieros mediante `last write wins`.

---

# 19. Idempotencia

Las escrituras financieras deben soportar `Idempotency-Key`.

Casos prioritarios:

```text
CreateCommitment
RegisterPayment
ReverseTransaction
```

Usar un mecanismo reutilizable, preferiblemente mediante una entidad/tabla dedicada como:

```text
IdempotencyRecord

id
workspace_id
operation
idempotency_key
request_hash
resource_type
resource_id
http_status
created_at
expires_at?
```

Constraint conceptual:

```text
UNIQUE (
    workspace_id,
    operation,
    idempotency_key
)
```

Mismo key + mismo request:

```text
→ devolver el resultado previamente producido
```

Mismo key + request diferente:

```text
→ IDEMPOTENCY_KEY_CONFLICT
```

No guardar cuerpos financieros completos innecesariamente para implementar idempotencia; utilizar un hash determinista del request normalizado.

---

# 20. Fechas y zonas horarias

Usar:

```text
due_date
→ PostgreSQL DATE
```

porque representa una fecha de negocio.

Usar:

```text
created_at
updated_at
occurred_at
expires_at
sent_at
...
→ TIMESTAMPTZ
```

Los instantes se almacenan en UTC.

La zona horaria del Workspace determina la interpretación de:

```text
hoy
mañana
vence hoy
vencido
próximo a vencer
```

No reescribir timestamps históricos cuando cambia la zona horaria.

---

# 21. Borrado y archivo

Evitar cascadas destructivas en operaciones financieras normales.

Preferir:

```text
ON DELETE RESTRICT
```

en relaciones financieras importantes.

`Contact` se archiva.

`Commitment` conserva historial y puede usar borrado lógico conforme a la política del proyecto.

La purga física pertenece al lifecycle de cuenta/workspace y a las políticas de retención, no a operaciones CRUD cotidianas.

---

# 22. Autenticación

La aplicación web debe usar credenciales gestionadas mediante cookies seguras.

No persistir tokens de autenticación en `localStorage`.

Requisitos:

```text
HttpOnly
Secure
SameSite apropiado
CSRF para operaciones mutables
sesiones revocables
```

Contraseñas:

```text
Argon2id
```

Nunca almacenar contraseña en texto plano.

Recuperación y verificación:

- tokens de un solo uso;
- expiración;
- almacenamiento seguro;
- revocación adecuada de sesiones tras cambio de contraseña.

La estrategia exacta de sesión opaca vs. tokens dentro de cookie debe seguir el ADR vigente. Si sigue marcada como provisional, no cerrarla silenciosamente.

---

# 23. Autorización

Autenticación y autorización son conceptos diferentes.

```text
Authentication
→ ¿quién eres?

Authorization
→ ¿puedes operar este recurso?
```

Autenticarse no concede acceso global.

Denegar por defecto.

Toda operación debe comprobar Workspace y permisos apropiados.

No confiar en IDs de propiedad proporcionados por el cliente.

Crear pruebas negativas contra IDOR/BOLA.

---

# 24. Logs, auditoría y privacidad

No registrar en logs operativos:

- contraseñas;
- tokens;
- cookies;
- cuerpos financieros completos;
- importes innecesarios;
- nombres;
- teléfonos;
- correos;
- secretos.

Distinguir:

```text
Application logs
```

de:

```text
Audit events
```

La auditoría debe registrar acciones relevantes de seguridad y modificaciones financieras sin convertirse en una copia indiscriminada de datos sensibles.

---

# 25. Outbox y tareas asíncronas

Cuando una operación de negocio necesita producir trabajo posterior:

```text
guardar cambio de negocio
+
guardar OutboxEvent
```

dentro de la misma transacción.

Después el worker procesa la outbox.

Un fallo de:

- correo;
- push;
- analítica;
- proveedor externo;

no debe revertir una operación financiera ya confirmada.

Los recordatorios nunca deben bloquear la captura financiera.

---

# 26. Dashboard y reporting

El Dashboard es una proyección/consulta, no una segunda fuente de verdad.

No mantener manualmente totales financieros durante Core v0.1 salvo que una optimización posterior esté justificada y documentada.

Derivar de compromisos activos:

```text
por cobrar
por pagar
vencidos
próximos
```

Los compromisos `cancelled` no participan en totales activos.

Los compromisos `paid` tienen balance cero.

No compensar automáticamente dinero por cobrar y por pagar de un mismo contacto como si fueran una sola obligación.

---

# 27. API

Base:

```text
/api/v1
```

Principios:

- JSON UTF-8;
- UUID;
- montos enteros en unidades menores;
- fechas ISO;
- `due_date` como `YYYY-MM-DD`;
- `Idempotency-Key` donde corresponda;
- `X-Request-ID`;
- paginación por cursor;
- errores estructurados mediante Problem Details cuando corresponda;
- contratos explícitos con Pydantic;
- OpenAPI como contrato de integración.

No crear endpoints alternativos si el caso de uso ya tiene un recurso coherente documentado.

Cuando se modifica el contrato, actualizar OpenAPI y cliente generado si corresponde.

---

# 28. Frontend

La experiencia es mobile-first.

No diseñar Nomi como una aplicación contable tradicional.

Las pantallas deben priorizar:

```text
saldo
contacto
fecha
estado
acción
```

Todo flujo debe contemplar:

- loading;
- empty state;
- success;
- error;
- accesibilidad;
- teclado cuando aplique;
- responsividad;
- estados offline cuando correspondan.

La captura de compromisos debe conservar el objetivo de ser rápida.

---

# 29. Offline

No implementar offline financiero de forma improvisada.

Estrategia objetivo:

```text
IndexedDB
   ↓
cola durable local
   ↓
UUID + Idempotency-Key
   ↓
sincronización
   ↓
versionado optimista
   ↓
resolución explícita de conflictos
```

Cambios financieros no deben resolverse automáticamente con `last write wins`.

Implementar offline progresivamente:

```text
1. aplicación online sólida
2. lectura offline
3. creación offline de datos simples
4. operaciones financieras offline
5. resolución avanzada de conflictos
```

No introducir la complejidad completa desde el primer milestone.

---

# 30. Testing

No considerar una funcionalidad terminada únicamente porque el happy path funciona.

Para operaciones financieras probar como mínimo, cuando corresponda:

```text
happy path
input inválido
workspace incorrecto
sesión inválida
reintento idempotente
idempotency conflict
sobrepago
concurrencia
rollback
reversión
doble reversión
estado pagado
estado cancelado
fechas/timezone
fallos de servicios secundarios
```

Tipos de prueba esperados:

```text
unitarias
integración
contrato/OpenAPI
E2E
seguridad
rendimiento
accesibilidad
```

Las pruebas del dominio financiero tienen prioridad sobre perseguir un porcentaje de cobertura arbitrario.

---

# 31. Migraciones

Toda modificación del esquema debe tener migración Alembic.

Antes de crear una migración:

```text
1. revisar entidad
2. revisar caso de uso
3. revisar invariantes
4. revisar ADR
5. revisar índices
6. revisar FKs
7. revisar estrategia de rollback/forward-fix
```

No editar retrospectivamente migraciones ya aplicadas en ambientes compartidos para ocultar cambios de diseño.

Preferir migraciones compatibles y estrategia expand/contract cuando el sistema ya esté desplegado.

---

# 32. PostgreSQL

PostgreSQL es la fuente de verdad transaccional.

La base debe proteger invariantes locales mediante:

```text
PRIMARY KEY
FOREIGN KEY
UNIQUE
CHECK
NOT NULL
índices apropiados
```

Ejemplos que deben protegerse también en DB cuando sea práctico:

```text
original_amount_minor > 0
balance_minor >= 0
balance_minor <= original_amount_minor
amount_minor > 0
version >= 1
valores permitidos de estado/tipo
una única reversión por movimiento
email de usuario único
```

Las invariantes que cruzan entidades pueden permanecer en dominio/aplicación cuando un CHECK normal no sea suficiente.

Evitar triggers complejos salvo necesidad demostrada.

---

# 33. Definition of Done

Una funcionalidad no está terminada hasta que, según aplique:

```text
cumple criterios de aceptación
tiene pruebas
autoriza por objeto/workspace
no filtra datos sensibles
actualiza OpenAPI
incluye telemetría útil
funciona en móvil
considera accesibilidad
maneja loading/error/empty
considera offline
incluye migración correcta
está documentada
pasa revisión
pasa CI
pasa smoke tests en staging
```

No marcar una tarea como completa si únicamente compila.

---

# 34. Flujo vertical inicial

La primera vertical slice prioritaria de Nomi Core es:

```text
RegisterUser
    ↓
crear Workspace personal
    ↓
crear Membership OWNER
    ↓
CreateContact
    ↓
CreateCommitment
    ↓
RegisterPayment
    ↓
GetDashboardSummary
```

El primer milestone ejecutable debe demostrar como mínimo:

```text
Usuario se registra.

Se crea su Workspace.

Crea "Juan Pérez".

Registra:
"Juan me debe $10,000 MXN".

Dashboard muestra:
Por cobrar $10,000.

Registra un pago de $2,500.

Saldo pasa a $7,500.

El historial explica exactamente cómo se obtuvo ese saldo.
```

Desarrollar verticalmente antes de extender horizontalmente todos los módulos.

---

# 35. Orden de implementación recomendado

No implementar todo Nomi a la vez.

Orden recomendado:

```text
Foundation
↓
Identity / Session
↓
Workspace / Membership
↓
Contacts
↓
Commitments
↓
Transactions
↓
Audit
↓
Reporting / Dashboard
↓
Outbox
↓
Reminders / Worker
↓
PWA / Offline
↓
Export
↓
Hardening
↓
Beta
↓
Billing
```

Respetar el roadmap actualizado si existe uno más reciente.

---

# 36. Cómo debe trabajar el agente

Para cada tarea:

```text
1. Leer documentación relevante.

2. Identificar módulos afectados.

3. Identificar casos de uso e invariantes.

4. Revisar ADR aplicables.

5. Inspeccionar el código existente antes de modificarlo.

6. Explicar brevemente el plan.

7. Implementar el cambio mínimo coherente.

8. Añadir o actualizar pruebas.

9. Ejecutar validaciones relevantes.

10. Revisar seguridad y aislamiento.

11. Actualizar OpenAPI/documentación/ADR si corresponde.

12. Resumir exactamente qué cambió.
```

No generar grandes cantidades de código especulativo.

No refactorizar áreas no relacionadas sin una razón clara.

No cambiar patrones arquitectónicos globales durante una tarea local.

---

# 37. Cambios arquitectónicos

Si se detecta una mejora importante que contradice o sustituye una decisión aceptada, no implementarla silenciosamente.

Presentar primero:

```text
Problema

Contexto

Propuesta

Alternativas

Ventajas

Desventajas

Impacto

Migración necesaria

Archivos afectados

ADR afectado
```

Si el cambio es significativo, crear un ADR nuevo que reemplace explícitamente la decisión anterior.

---

# 38. Sobreingeniería

Evitar introducir anticipadamente:

```text
microservicios
Kubernetes
event sourcing completo
CQRS completo
Redis sin necesidad
Kafka
service mesh
bases adicionales
caches distribuidas
sistemas complejos de permisos
IA
multi-moneda
equipos completos
billing
adjuntos
```

salvo que la fase actual lo requiera y la documentación lo apruebe.

Diseñar puntos de extensión razonables es válido.

Implementar el futuro antes de necesitarlo no lo es.

---

# 39. Antes de comenzar una tarea

El agente debe ser capaz de responder brevemente:

```text
¿Qué comportamiento estoy implementando?

¿Qué módulo lo posee?

¿Qué invariantes protege?

¿Qué tablas toca?

¿Qué otros módulos consulta?

¿Qué errores pueden ocurrir?

¿Qué pruebas deben pasar?

¿Qué documento respalda esta decisión?
```

Si alguna respuesta importante no está clara, revisar documentación antes de escribir código.

---

# 40. Regla final

Nomi debe mantenerse:

```text
simple para el usuario
estricto con el dinero
seguro con los datos
modular en el código
explicable en sus decisiones
```

Cuando exista tensión entre una implementación rápida y una invariante financiera o de seguridad, preservar la invariante.

Cuando exista tensión entre una arquitectura sofisticada y una solución simple que cumple el dominio actual, preferir la solución simple.

Cuando exista duda sobre intención del producto, volver a la documentación antes de inventar comportamiento.
