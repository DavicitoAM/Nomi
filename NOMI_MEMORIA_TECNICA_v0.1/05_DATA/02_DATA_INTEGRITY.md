# Integridad de datos

## Defensa por capas

### PostgreSQL

Protege invariantes locales y estructurales:

- PK/FK;
- UNIQUE;
- CHECK;
- `amount > 0`;
- `balance >= 0`;
- valores válidos;
- una reversión por Payment.

### Dominio

Protege reglas entre entidades:

- Contact y Commitment mismo Workspace;
- moneda consistente;
- Payment <= balance;
- Reversal apunta a Payment del mismo Commitment;
- permisos;
- lifecycle válido para operación.

### Aplicación/UI

Protege experiencia:

- confirmaciones;
- advertencias;
- mensajes claros;
- evitar doble clic;
- contacto similar.

## Por qué no usar PostgreSQL ENUM

Nomi aún evoluciona. `VARCHAR + CHECK` facilita migraciones de valores sin renunciar a integridad.

En Python se mantienen enums tipados.

## Money

Nunca FLOAT.

```text
BIGINT + currency_code
```

Core usa una moneda por Workspace.

## Balance materializado

Aunque puede derivarse del historial, se mantiene `balance_minor` para consultas y reglas rápidas.

La consistencia se preserva porque Payment/Reversal actualizan movimiento y saldo en la misma transacción.

## Reconciliación

Se recomienda una prueba/command administrativo futuro:

```text
recomputed_balance(commitment)
```

que recalcule usando movimientos efectivos y compare con `balance_minor`.

No debe ejecutarse como corrección automática silenciosa; si detecta divergencia, generar alerta/incidente.

## Borrado

Historia financiera no se borra mediante operaciones normales.

- Contact → archive.
- Commitment → lifecycle/soft delete según política.
- Transaction → reversible, no borrable como corrección.
- purga final → proceso de privacidad controlado.
