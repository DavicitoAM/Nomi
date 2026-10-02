# Índice de Architecture Decision Records

| ADR | Estado | Decisión |
|---|---|---|
| 0001 | ACEPTADA | Monolito modular |
| 0002 | ACEPTADA | PostgreSQL como fuente de verdad |
| 0003 | ACEPTADA | FastAPI |
| 0004 | ACEPTADA | Next.js PWA |
| 0005 | PROVISIONAL | Sesión opaca segura en cookie para web |
| 0006 | ACEPTADA | Outbox transaccional |
| 0007 | ACEPTADA | OpenTelemetry |
| 0008 | PLANIFICADA | Facturación alojada |
| 0009 | ACEPTADA | Dinero en unidad menor BIGINT |
| 0010 | ACEPTADA | No microservicios en MVP |
| 0011 | ACEPTADA | VARCHAR + CHECK en DB para enums |
| 0012 | ACEPTADA | Una moneda por Workspace en Core |
| 0013 | ACEPTADA | Estado de ciclo separado de estados derivados |
| 0014 | ACEPTADA | IdempotencyRecord genérico |
| 0015 | ACEPTADA | Reversal mediante self-FK UNIQUE |
| 0016 | ACEPTADA | Optimistic locking con version |
| 0017 | ACEPTADA | Workspace como frontera de propiedad |
| 0018 | ACEPTADA | Dashboard derivado, no fuente de verdad |

## Plantilla

Cada ADR responde:

- Contexto
- Decisión
- Alternativas
- Consecuencias positivas
- Consecuencias negativas
- Mitigación
- Disparadores de revisión
