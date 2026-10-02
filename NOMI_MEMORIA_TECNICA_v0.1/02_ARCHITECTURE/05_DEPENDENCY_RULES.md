# Reglas de dependencia y diseño interno

## Patrón por módulo

```text
module/
├── domain/
│   ├── entities
│   ├── value_objects
│   ├── enums
│   ├── policies
│   └── domain_errors
├── application/
│   ├── use_cases
│   ├── commands_queries
│   └── ports
├── infrastructure/
│   ├── repositories
│   ├── models
│   └── adapters
└── api/
    ├── routes
    ├── schemas
    └── dependencies
```

## Domain

Debe poder probarse sin levantar FastAPI ni PostgreSQL. Contiene reglas puras.

## Application

Orquesta casos de uso. Decide qué repositorios/puertos participan y delimita transacciones.

## Infrastructure

Implementa persistencia y proveedores externos. No define reglas de negocio.

## API

Traduce HTTP a comandos/queries y traduce resultados/errores a HTTP.

## Shared

`shared/` sólo contiene primitivas verdaderamente transversales:

- IDs;
- clock abstraction;
- unit of work;
- problem details;
- tracing context.

No debe convertirse en una carpeta donde todo módulo comparte sus modelos internos.

## Regla antiacoplamiento

Si un módulo necesita internals de otro, primero preguntar:

1. ¿Debe usar un caso de uso público?
2. ¿Debe usar un puerto/query explícito?
3. ¿Es un efecto secundario que debería escuchar un evento?
4. ¿Estamos violando una frontera de dominio?

## Eventos

Un evento describe algo que ya ocurrió:

- `CommitmentCreated`;
- `PaymentRegistered`;
- `TransactionReversed`;
- `CommitmentFullyPaid`;
- `CommitmentCancelled`.

No usar eventos para ocultar una transacción que en realidad necesita consistencia síncrona.
