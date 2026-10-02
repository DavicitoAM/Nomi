# Estrategia de migraciones

## Herramienta

Alembic.

## Principios

- toda modificación de esquema está versionada;
- staging antes de producción;
- migraciones revisadas;
- no asumir rollback destructivo seguro;
- preferir expand-and-contract.

## Expand and contract

Ejemplo para renombrar un campo crítico:

1. agregar nuevo campo compatible;
2. aplicación escribe ambos si hace falta;
3. backfill separado;
4. cambiar lectura;
5. validar;
6. eliminar campo antiguo en una liberación posterior.

## Constraints

Añadir constraints sobre tablas con datos requiere validar primero que los datos existentes cumplen.

## Cambios financieros

Migraciones que afectan:

- amount;
- currency;
- balance;
- transactions;
- foreign keys;

requieren:

- backup/export lógico;
- staging con dataset sintético representativo;
- prueba de restore;
- plan de forward-fix.

## Seeds

No mezclar datos personales reales en staging. Seeds deben ser sintéticos.

## Primera migración

La primera migración Core debe incluir únicamente tablas necesarias para la vertical slice y su seguridad. Reminders/Billing pueden entrar después para evitar un esquema “futuro imaginario”.
