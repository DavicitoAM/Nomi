# Backup y recuperación

## Principios

Configurar backups no es suficiente; hay que ensayar restauración.

## Estrategia inicial

- PostgreSQL administrado;
- backups cifrados;
- retención limitada;
- export lógico antes de migraciones de alto riesgo;
- runbook documentado.

## Objetivos alfa

Hipótesis iniciales del documento maestro:

- RPO hasta 24 h;
- RTO hasta 8 h.

Antes de monetizar deben revisarse según promesa comercial.

## Restore drill

Periódicamente:

1. seleccionar backup;
2. restaurar en entorno aislado;
3. ejecutar migraciones;
4. smoke tests;
5. validar conteos/invariantes;
6. documentar tiempo real.

## Integridad después de restore

Comprobar:

- Commitment balances válidos;
- FK;
- una reversión máxima;
- memberships;
- outbox;
- sessions según política.

## Incidentes

Restaurar no sustituye investigar causa raíz.
