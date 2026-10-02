# ADR-0017 — Workspace como frontera de propiedad

**Estado:** ACEPTADA

## Decisión
Contacts y Commitments pertenecen a Workspace, no directamente a User.

## Motivo
Permitir futuro multiusuario sin migrar propiedad financiera.

## Seguridad
Toda query de recurso usa current_workspace. No confiar en workspace_id enviado por cliente.
