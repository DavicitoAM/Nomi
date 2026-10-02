# Contact

## Definición

Contact representa a una persona u organización con la que existe una relación económica.

No es sinónimo de cliente, proveedor, deudor ni acreedor. El rol económico se determina en cada Commitment.

## Campos

```text
id
workspace_id
name
phone?
email?
notes?
archived_at?
created_at
updated_at
```

## Reglas

- `name` obligatorio;
- email/teléfono opcionales;
- no hay UNIQUE por nombre, teléfono o correo;
- puede haber dos contactos llamados igual;
- un contacto puede tener compromisos por cobrar y por pagar a la vez;
- no se almacena `balance` en Contact;
- archivar no cancela compromisos;
- archivar no modifica saldos;
- un contacto archivado no recibe nuevos compromisos por el flujo normal;
- puede restaurarse.

## Saldo agregado

Se deriva:

```text
Juan
 ├─ receivable 5,000
 ├─ receivable 2,000
 └─ payable    1,000
```

Resumen:

```text
Por cobrar: 7,000
Por pagar:  1,000
```

No compensar automáticamente en un único neto como verdad de negocio.

## Duplicados

Core permite duplicados legítimos. La UI puede advertir “contacto similar” sin bloquear la creación.

No se implementa MergeContacts en v0.1.

## Archivo vs eliminación

Archivo = operación cotidiana reversible.

Eliminación física = proceso de privacidad/purga controlada.

## Casos de uso

- CreateContact
- UpdateContact
- GetContact
- ListContacts
- ArchiveContact
- RestoreContact
- GetContactSummary
- GetContactActivity
