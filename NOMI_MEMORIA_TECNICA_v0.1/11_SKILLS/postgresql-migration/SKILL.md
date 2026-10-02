---
name: nomi-postgresql-migration
description: Diseña migraciones PostgreSQL/Alembic seguras y constraints coherentes con el dominio financiero de Nomi.
---

# PostgreSQL Migration Skill

## Usar cuando

- se crea/modifica tabla;
- cambia un estado;
- se añade constraint;
- se modifica dinero/FK/índice.

## Proceso

1. Identificar invariante.
2. Determinar qué puede proteger DB vs dominio.
3. Elegir tipo:
   - money → BIGINT;
   - due date → DATE;
   - event time → TIMESTAMPTZ;
   - enum → VARCHAR + CHECK.
4. Añadir PK/FK/UNIQUE/CHECK.
5. Revisar ON DELETE.
6. Diseñar índice por query real.
7. Plan expand/contract si hay datos.
8. Escribir downgrade sólo si es seguro; si no, documentar forward-fix.
9. Probar upgrade desde versión previa.
10. Smoke/reconciliation.

## Reglas Nomi

- nunca FLOAT para dinero;
- balance no negativo;
- no CASCADE accidental de historia financiera;
- reversal self-FK UNIQUE;
- migraciones destructivas requieren backup/ensayo.
