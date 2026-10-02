# Ciclo de una petición

## Comando financiero típico

Ejemplo: registrar un pago.

```text
HTTP Request
  ↓
Request ID / validación de forma
  ↓
Autenticación de Session
  ↓
Resolución User + Membership + Workspace
  ↓
CSRF / autorización
  ↓
Idempotency lookup
  ↓
Application Use Case
  ↓
Carga Commitment aislado por workspace
  ↓
Reglas de dominio
  ↓
BEGIN
    INSERT Transaction
    UPDATE Commitment + version
    INSERT AuditEvent
    INSERT OutboxEvent
    INSERT/complete IdempotencyRecord
  COMMIT
  ↓
Response DTO
```

## Efectos secundarios

Correo, push o analítica no se ejecutan dentro del camino crítico. El worker procesa la outbox después del commit.

Si el proveedor de correo falla:

- la operación financiera continúa confirmada;
- el evento permanece/reintenta;
- se observa el fallo;
- el usuario no pierde un abono por un servicio secundario.

## Query típico

Ejemplo: dashboard.

```text
Request
 ↓
Auth Context
 ↓
Workspace
 ↓
Reporting Query
 ↓
SELECT/aggregate commitments
 ↓
Derived states
 ↓
Response
```

La query no modifica estados sólo porque el tiempo cambió.

## Regla 401 / 403 / 404

- Sin sesión válida: `401`.
- Acción autenticada sin privilegio global explícito: `403` cuando revelar la existencia es seguro.
- Recurso perteneciente a otro workspace: preferentemente `404` para evitar enumeración.
