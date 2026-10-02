# Transaction

## Definición

Transaction registra una operación que explica un cambio de saldo de un Commitment.

Core v0.1 usa únicamente:

- `payment`
- `reversal`

Los ajustes avanzados se posponen.

## Campos

```text
id
commitment_id
type
amount_minor
currency_code
note?
occurred_at
created_by?
reversal_of_transaction_id?
created_at
```

## Payment

Reduce saldo:

```text
new_balance = current_balance - amount
```

Reglas:

- amount > 0;
- amount <= current_balance;
- Commitment debe estar `open`;
- moneda idéntica;
- misma transacción de BD para Transaction + Commitment + Audit + Outbox.

## Reversal

No edita ni elimina el Payment. Crea una segunda Transaction que lo deshace.

```text
T1 payment  2,500
T2 reversal 2,500 → reversal_of = T1
```

### Reglas

- el original debe ser `payment`;
- debe pertenecer al mismo Commitment;
- amount y currency se derivan del original;
- sólo una reversión por Payment;
- no se puede revertir una reversión;
- si el compromiso estaba `paid`, una reversión puede reabrirlo.

## `reversal_of_transaction_id`

FK autorreferenciada:

```text
transactions.reversal_of_transaction_id
→ transactions.id
```

Es nullable y UNIQUE.

Esto garantiza que un Payment sólo tenga una reversión.

## `occurred_at` vs `created_at`

`occurred_at`: cuándo ocurrió realmente el pago.

`created_at`: cuándo se registró en Nomi.

Ambos pueden diferir.

## Regla central

> El saldo nunca cambia solo.

No existe un `UPDATE balance` de negocio sin una Transaction que explique la modificación.
