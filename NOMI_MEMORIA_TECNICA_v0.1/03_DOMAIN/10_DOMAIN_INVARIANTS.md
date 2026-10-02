# Invariantes de dominio

Estas reglas deben tener pruebas y, cuando sea posible, constraints de base.

## Propiedad

1. Todo Contact pertenece a un Workspace.
2. Todo Commitment pertenece a un Workspace.
3. Contact y Commitment asociados pertenecen al mismo Workspace.
4. Ninguna petición confía en `workspace_id` del cliente como autoridad.
5. Los recursos de otro Workspace no se revelan.

## Dinero

6. `original_amount_minor > 0`.
7. `balance_minor >= 0`.
8. Core: `balance_minor <= original_amount_minor`.
9. `paid → balance = 0`.
10. `open → balance > 0`.
11. Payment tiene `amount_minor > 0`.
12. Payment no excede saldo.
13. Moneda de Transaction = moneda de Commitment.
14. Core: moneda de Commitment = moneda del Workspace.

## Historia

15. Saldo no cambia sin movimiento.
16. Payment no se edita destructivamente.
17. Payment no se elimina como corrección.
18. Reversal crea nueva Transaction.
19. Un Payment sólo puede revertirse una vez.
20. Reversal apunta a un Payment del mismo Commitment.

## Tiempo

21. `due_date` es fecha de negocio.
22. `overdue` se deriva usando timezone del Workspace.
23. Compromiso pagado no es overdue aunque la due_date esté en pasado.
24. Sin due_date no existe overdue.

## Contact

25. Archivar no cancela compromisos.
26. Archivar no modifica saldos.
27. Contact archivado no acepta nuevos compromisos por flujo normal.

## Concurrencia e idempotencia

28. Una misma idempotency key con mismo request produce un solo efecto.
29. Misma key con payload diferente produce conflicto.
30. Escritura financiera valida `version`.
31. Conflicto de version no aplica silenciosamente sobre datos nuevos.

## Atomicidad

32. Payment + balance + audit + outbox forman una unidad transaccional.
33. Si una parte crítica falla, rollback.
34. Fallo de email/push posterior no revierte una operación financiera confirmada.
