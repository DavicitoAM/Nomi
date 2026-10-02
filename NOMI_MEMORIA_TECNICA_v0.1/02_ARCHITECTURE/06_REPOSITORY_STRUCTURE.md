# Estructura del monorepo

## Objetivo

Reflejar límites de producto y dominio sin crear una jerarquía ceremonial excesiva.

```text
nomi/
├── README.md
├── docs/
├── apps/
│   ├── web/
│   ├── api/
│   └── worker/
├── packages/
│   ├── api-client/
│   ├── ui/
│   ├── config/
│   └── schemas/
├── infrastructure/
└── .github/
```

## API

```text
apps/api/
├── app/
│   ├── core/
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── security.py
│   │   ├── telemetry.py
│   │   └── errors.py
│   ├── modules/
│   │   ├── identity/
│   │   ├── workspaces/
│   │   ├── contacts/
│   │   ├── commitments/
│   │   ├── transactions/
│   │   ├── reporting/
│   │   ├── audit/
│   │   ├── reminders/
│   │   └── billing/
│   ├── shared/
│   └── main.py
├── alembic/
└── tests/
```

## Web

```text
apps/web/src/
├── app/
├── components/
├── features/
├── offline/
├── lib/
├── telemetry/
└── types/
```

## Worker

No necesita existir en el primer commit si aún no procesa nada. Debe agregarse al implementar outbox/reminders de forma operativa.

## Regla

La estructura crece cuando existe código que ubicar. No crear docenas de carpetas vacías para “parecer enterprise”.
