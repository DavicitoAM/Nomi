# Modelo PostgreSQL — Core v0.1

Este documento traduce el dominio a una propuesta concreta de persistencia. No sustituye las migraciones Alembic, pero define su objetivo.

## Convenciones

- IDs: UUID.
- Dinero: BIGINT en unidad menor.
- Fechas de negocio: DATE.
- Instantes: TIMESTAMPTZ.
- Enums de dominio en DB: VARCHAR + CHECK.
- En Python: `Enum` tipado.
- FKs financieras: RESTRICT por defecto.
- No CASCADE cotidiano sobre historia financiera.

## `users`

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(254) NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    display_name VARCHAR(120) NOT NULL,
    status VARCHAR(32) NOT NULL,
    email_verified_at TIMESTAMPTZ NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT ck_users_status CHECK (
        status IN (
            'pending_verification',
            'active',
            'disabled',
            'deletion_pending'
        )
    )
);
```

El email se normaliza en aplicación antes de persistir.

## `sessions`

```sql
CREATE TABLE sessions (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL,
    last_seen_at TIMESTAMPTZ NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    revoked_at TIMESTAMPTZ NULL
);
```

El cascade aquí es aceptable porque Session no es historia financiera y dejar sesiones huérfanas no aporta valor.

## `email_verification_tokens`

```sql
CREATE TABLE email_verification_tokens (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash TEXT NOT NULL UNIQUE,
    expires_at TIMESTAMPTZ NOT NULL,
    used_at TIMESTAMPTZ NULL,
    created_at TIMESTAMPTZ NOT NULL
);
```

## `password_reset_tokens`

Misma forma que verificación.

## `workspaces`

```sql
CREATE TABLE workspaces (
    id UUID PRIMARY KEY,
    name VARCHAR(160) NOT NULL,
    currency_code VARCHAR(3) NOT NULL,
    timezone VARCHAR(64) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT ck_workspace_currency
      CHECK (currency_code ~ '^[A-Z]{3}$')
);
```

## `memberships`

```sql
CREATE TABLE memberships (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE RESTRICT,
    role VARCHAR(16) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT uq_membership UNIQUE (user_id, workspace_id),
    CONSTRAINT ck_membership_role CHECK (role IN ('owner', 'member'))
);
```

## `contacts`

```sql
CREATE TABLE contacts (
    id UUID PRIMARY KEY,
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE RESTRICT,
    name VARCHAR(160) NOT NULL,
    phone VARCHAR(40) NULL,
    email VARCHAR(254) NULL,
    notes TEXT NULL,
    archived_at TIMESTAMPTZ NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT ck_contact_name CHECK (length(trim(name)) > 0)
);
```

## `commitments`

```sql
CREATE TABLE commitments (
    id UUID PRIMARY KEY,
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE RESTRICT,
    contact_id UUID NOT NULL REFERENCES contacts(id) ON DELETE RESTRICT,

    direction VARCHAR(16) NOT NULL,
    original_amount_minor BIGINT NOT NULL,
    balance_minor BIGINT NOT NULL,
    currency_code VARCHAR(3) NOT NULL,

    concept VARCHAR(160) NULL,
    notes TEXT NULL,
    due_date DATE NULL,

    lifecycle_status VARCHAR(16) NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,

    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    deleted_at TIMESTAMPTZ NULL,

    CONSTRAINT ck_commitment_direction
      CHECK (direction IN ('receivable', 'payable')),

    CONSTRAINT ck_commitment_original
      CHECK (original_amount_minor > 0),

    CONSTRAINT ck_commitment_balance
      CHECK (
        balance_minor >= 0
        AND balance_minor <= original_amount_minor
      ),

    CONSTRAINT ck_commitment_currency
      CHECK (currency_code ~ '^[A-Z]{3}$'),

    CONSTRAINT ck_commitment_lifecycle
      CHECK (lifecycle_status IN ('open', 'paid', 'cancelled')),

    CONSTRAINT ck_commitment_version
      CHECK (version >= 1),

    CONSTRAINT ck_commitment_state_balance
      CHECK (
        (lifecycle_status = 'open' AND balance_minor > 0)
        OR
        (lifecycle_status = 'paid' AND balance_minor = 0)
        OR
        (lifecycle_status = 'cancelled' AND balance_minor >= 0)
      )
);
```

La igualdad `workspace_id` del Contact y Commitment se valida en dominio/repositorio; un CHECK estándar no puede consultar otra fila.

## `transactions`

```sql
CREATE TABLE transactions (
    id UUID PRIMARY KEY,
    commitment_id UUID NOT NULL
      REFERENCES commitments(id) ON DELETE RESTRICT,

    type VARCHAR(16) NOT NULL,
    amount_minor BIGINT NOT NULL,
    currency_code VARCHAR(3) NOT NULL,

    note TEXT NULL,
    occurred_at TIMESTAMPTZ NOT NULL,
    created_by UUID NULL REFERENCES users(id) ON DELETE SET NULL,

    reversal_of_transaction_id UUID NULL
      REFERENCES transactions(id) ON DELETE RESTRICT,

    created_at TIMESTAMPTZ NOT NULL,

    CONSTRAINT uq_transaction_reversal
      UNIQUE (reversal_of_transaction_id),

    CONSTRAINT ck_transaction_type
      CHECK (type IN ('payment', 'reversal')),

    CONSTRAINT ck_transaction_amount
      CHECK (amount_minor > 0),

    CONSTRAINT ck_transaction_currency
      CHECK (currency_code ~ '^[A-Z]{3}$'),

    CONSTRAINT ck_transaction_reversal_shape
      CHECK (
        (type = 'payment' AND reversal_of_transaction_id IS NULL)
        OR
        (type = 'reversal' AND reversal_of_transaction_id IS NOT NULL)
      )
);
```

`reversed_at` no se guarda: la existencia y fecha de la fila reversal es la fuente de verdad.

## `audit_events`

```sql
CREATE TABLE audit_events (
    id UUID PRIMARY KEY,
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE RESTRICT,
    actor_user_id UUID NULL REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(96) NOT NULL,
    entity_type VARCHAR(64) NOT NULL,
    entity_id UUID NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL
);
```

## `outbox_events`

```sql
CREATE TABLE outbox_events (
    id UUID PRIMARY KEY,
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE RESTRICT,
    event_type VARCHAR(96) NOT NULL,
    payload JSONB NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL,
    processed_at TIMESTAMPTZ NULL,
    attempts INTEGER NOT NULL DEFAULT 0,
    CONSTRAINT ck_outbox_attempts CHECK (attempts >= 0)
);
```

## `idempotency_records`

```sql
CREATE TABLE idempotency_records (
    id UUID PRIMARY KEY,
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE RESTRICT,
    operation VARCHAR(64) NOT NULL,
    idempotency_key UUID NOT NULL,
    request_hash VARCHAR(128) NOT NULL,
    resource_type VARCHAR(64) NULL,
    resource_id UUID NULL,
    http_status INTEGER NULL,
    created_at TIMESTAMPTZ NOT NULL,
    expires_at TIMESTAMPTZ NULL,
    CONSTRAINT uq_idempotency
      UNIQUE (workspace_id, operation, idempotency_key)
);
```

## Índices

```sql
CREATE INDEX ix_contacts_active
ON contacts(workspace_id, archived_at);

CREATE INDEX ix_commitments_dashboard
ON commitments(workspace_id, lifecycle_status, due_date);

CREATE INDEX ix_commitments_contact
ON commitments(workspace_id, contact_id, created_at);

CREATE INDEX ix_transactions_history
ON transactions(commitment_id, occurred_at, created_at);

CREATE INDEX ix_audit_workspace
ON audit_events(workspace_id, created_at);

CREATE INDEX ix_outbox_pending
ON outbox_events(processed_at, occurred_at)
WHERE processed_at IS NULL;
```

Los índices se validarán contra planes de ejecución y volumen real.
