# UC-007 — Archive / Restore Contact

## Objetivo

Retirar un Contact del uso cotidiano sin destruir su historial.

## Archive

### Regla

`archived_at = now`.

No:

- cancela Commitments;
- modifica balances;
- elimina Transactions.

Si hay compromisos activos, la UI muestra advertencia.

### Efecto

- se oculta de listados activos;
- no se ofrece para nuevos Commitments;
- sigue disponible en historial y relaciones existentes.

## Restore

`archived_at = NULL`.

El Contact vuelve a estar disponible para nuevos Commitments.

## Errores

- `CONTACT_NOT_FOUND`
- `CONTACT_ALREADY_ARCHIVED`
- `CONTACT_NOT_ARCHIVED`

## Nota API

El contrato maestro usa DELETE para contactos, pero Core recomienda hacer explícita la semántica de archivo vía PATCH o endpoints `/archive` y `/restore`. La decisión final se documentará en OpenAPI.
