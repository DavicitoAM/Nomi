# Idempotencia y concurrencia

## Problema de idempotencia

Red móvil:

```text
POST payment
servidor procesa
respuesta se pierde
cliente reintenta
```

Sin protección, el saldo se descuenta dos veces.

## Registro dedicado

Clave lógica:

```text
(workspace_id, operation, idempotency_key)
```

Se conserva `request_hash`.

### Caso 1

Misma key y mismo hash:

> devolver el resultado previo; no repetir efecto.

### Caso 2

Misma key y hash diferente:

> `IDEMPOTENCY_KEY_CONFLICT`.

## Alcance

Aplicar a escrituras financieras:

- CreateCommitment;
- RegisterPayment;
- ReverseTransaction;
- futuras operaciones equivalentes.

## Concurrencia optimista

Commitment incluye `version`.

Ejemplo:

```text
balance = 1000
version = 4
```

A y B leen version 4.

A escribe:

```sql
UPDATE commitments
SET balance_minor = 300,
    version = version + 1
WHERE id = :id
  AND workspace_id = :workspace
  AND version = 4;
```

A afecta 1 fila.

B intenta con version 4 y afecta 0.

Resultado:

```text
VERSION_CONFLICT
```

## Por qué no “fusionar” automáticamente Payments concurrentes

Aunque ambos montos quepan, el saldo cambió respecto de la decisión original del segundo usuario/dispositivo. Core prefiere:

1. rechazar segundo write;
2. recargar saldo;
3. pedir reconfirmación.

Esto es conservador y explicable.

## Locks

No introducir locking pesimista global de forma predeterminada. Puede utilizarse un bloqueo de fila dentro del repositorio si las pruebas demuestran una carrera no resuelta, pero el contrato de dominio seguirá usando versionado/idempotencia.

## Offline

La operación local genera:

- UUID;
- idempotency key;
- payload durable;
- expected version.

Al sincronizar, el servidor sigue siendo árbitro final.
