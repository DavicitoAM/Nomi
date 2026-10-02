# ERD completo — Core y extensiones

## Core v0.1

```mermaid
erDiagram
    USER ||--o{ SESSION : abre
    USER ||--o{ EMAIL_VERIFICATION_TOKEN : recibe
    USER ||--o{ PASSWORD_RESET_TOKEN : solicita
    USER ||--o{ MEMBERSHIP : posee

    WORKSPACE ||--o{ MEMBERSHIP : contiene
    WORKSPACE ||--o{ CONTACT : posee
    WORKSPACE ||--o{ COMMITMENT : posee
    WORKSPACE ||--o{ AUDIT_EVENT : registra
    WORKSPACE ||--o{ OUTBOX_EVENT : emite
    WORKSPACE ||--o{ IDEMPOTENCY_RECORD : protege

    CONTACT ||--o{ COMMITMENT : relaciona
    COMMITMENT ||--o{ TRANSACTION : recibe
    USER ||--o{ TRANSACTION : crea

    TRANSACTION o|--o| TRANSACTION : revierte
```

## Extensión MVP

```mermaid
erDiagram
    USER ||--o{ NOTIFICATION_PREFERENCE : configura
    COMMITMENT ||--o{ REMINDER : programa
    WORKSPACE ||--o| SUBSCRIPTION : contrata
```

## Contexto de cada entidad

| Entidad | Propietario lógico | Función |
|---|---|---|
| User | plataforma | identidad |
| Session | User | sesión revocable |
| EmailVerificationToken | User | verificar correo |
| PasswordResetToken | User | recuperación |
| Workspace | plataforma/User owner | frontera de datos |
| Membership | User + Workspace | acceso |
| Contact | Workspace | contraparte |
| Commitment | Workspace | obligación |
| Transaction | Commitment | cambio de saldo |
| AuditEvent | Workspace | trazabilidad |
| OutboxEvent | Workspace | efectos asíncronos |
| IdempotencyRecord | Workspace | deduplicación |
| Reminder | Commitment | aviso |
| NotificationPreference | User | preferencias |
| Subscription | Workspace | plan |

## Cardinalidades clave

### User — Membership — Workspace

N:M preparada para futuro, aunque Core use 1:1 práctico.

### Workspace — Contact

1:N.

### Contact — Commitment

1:N.

### Workspace — Commitment

1:N redundante intencional para aislamiento y consultas rápidas.

### Commitment — Transaction

1:N.

### Transaction — Transaction

Reversal autorreferenciado 0..1 → 1. `reversal_of_transaction_id` es UNIQUE, por lo que un Payment no tiene más de una reversión.

### Workspace — Subscription

0..1 en diseño inicial.
