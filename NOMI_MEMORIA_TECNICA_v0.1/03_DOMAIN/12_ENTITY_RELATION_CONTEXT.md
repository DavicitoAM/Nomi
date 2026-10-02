# Contexto relacional de entidades

Este documento explica por qué existen relaciones que podrían parecer redundantes.

## Commitment tiene `workspace_id` y `contact_id`

Aunque Contact ya conoce su Workspace, Commitment conserva `workspace_id` porque:

- refuerza aislamiento;
- simplifica dashboard;
- permite índices eficientes;
- reduce joins de autorización.

La aplicación debe garantizar:

```text
commitment.workspace_id == contact.workspace_id
```

## Transaction no tiene `workspace_id`

Su propiedad se deriva:

```text
Transaction → Commitment → Workspace
```

En operaciones, el repositorio carga Transaction a través de Commitment scoped por Workspace.

Si profiling futuro demuestra necesidad, se puede desnormalizar de forma consciente, no anticipada.

## Audit tiene workspace y actor

`workspace_id` define contexto del dato; `actor_user_id` identifica quién ejecutó.

Actor puede ser NULL si existe una acción de sistema legítima, pero `action` y metadata deben explicarla.

## Outbox tiene workspace

Permite procesar/filtrar contexto y aplicar aislamiento en tareas asíncronas.

## Membership como tabla intermedia

Aunque Core sea 1 usuario/1 workspace, Membership evita que el futuro multiusuario exija mover todos los datos financieros.

## Subscription → Workspace

El plan compra capacidad del espacio, no la identidad personal del User.

## NotificationPreference → User

Preferencias de recepción son personales incluso si varios usuarios comparten un Workspace.
