# Máquinas de estado

## Commitment lifecycle

```mermaid
stateDiagram-v2
    [*] --> Open
    Open --> Paid: payment deja balance=0
    Paid --> Open: reversal deja balance>0
    Open --> Cancelled: cancel
```

Core no soporta `Cancelled → Open` todavía.

## Payment state derivado

```mermaid
stateDiagram-v2
    [*] --> Pending: balance=original
    Pending --> Partial: payment parcial
    Partial --> Partial: payment parcial
    Partial --> Paid: balance=0
    Pending --> Paid: payment total
    Paid --> Partial: reversal parcial
    Paid --> Pending: reversal deja balance=original
```

No se persiste como máquina independiente; se calcula desde balance/original.

## Timing state derivado

```text
due_date = null                     → no_due_date
due_date > today + 7                → upcoming
today <= due_date <= today + 7      → due_soon
due_date < today && balance > 0
&& lifecycle=open                   → overdue
```

## Contact archive

```mermaid
stateDiagram-v2
    Active --> Archived: archive
    Archived --> Active: restore
```

Archivo no toca historia financiera.

## Session

```mermaid
stateDiagram-v2
    Active --> Expired: expires_at
    Active --> Revoked: logout/admin/password change
```

## User

```mermaid
stateDiagram-v2
    PendingVerification --> Active: verify email
    Active --> Disabled: administrative action
    Active --> DeletionPending: request deletion
    DeletionPending --> Active: recover within window
```
