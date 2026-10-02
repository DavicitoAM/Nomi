# Flujos posteriores a Core — Reminder y Export

## Reminder

```mermaid
sequenceDiagram
    participant S as Scheduler
    participant DB
    participant W as Worker
    participant E as Email Provider

    S->>DB: localizar reminders due
    S->>DB: reservar/mark processing
    W->>E: enviar aviso
    alt éxito
      W->>DB: status=sent, sent_at
    else fallo temporal
      W->>DB: attempts+1, reschedule
    else fallo terminal
      W->>DB: status=failed
    end
```

Un CommitmentFullyPaid puede cancelar reminders futuros.

## Export CSV

Flujo:

1. usuario solicita exportación;
2. authorization/workspace;
3. crear job;
4. worker genera CSV;
5. almacenamiento temporal si hace falta;
6. URL firmada corta;
7. expiración/borrado.

Nunca generar una exportación gigante síncronamente si bloquea API.

## Offline

Export y procesamiento de reminders son funcionalidades de servidor; no se prometen offline.
