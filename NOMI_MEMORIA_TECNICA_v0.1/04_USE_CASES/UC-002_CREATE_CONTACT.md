# UC-002 — CreateContact

## Actor

Usuario autenticado con Membership válida.

## Objetivo

Registrar una contraparte para asociarle compromisos.

## Entrada

```json
{
  "name": "Juan Pérez",
  "phone": null,
  "email": null,
  "notes": null
}
```

No se acepta `workspace_id` como autoridad.

## Flujo

1. Resolver Session.
2. Resolver User/Membership/Workspace.
3. Validar nombre.
4. Validar opcionalmente email/teléfono.
5. Insertar Contact con `workspace_id` del contexto.
6. AuditEvent.
7. Responder Contact.

## Reglas

- name no vacío;
- duplicados permitidos;
- `archived_at = NULL`;
- Contact no produce cambios en dashboard.

## Errores

- `UNAUTHENTICATED`
- `WORKSPACE_NOT_AVAILABLE`
- `CONTACT_NAME_REQUIRED`
- `INVALID_CONTACT_EMAIL`

## Pruebas

- no puede crear Contact en workspace arbitrario;
- dos Contact con mismo nombre son válidos;
- email/teléfono pueden ser NULL;
- crear contacto no cambia cifras financieras.
