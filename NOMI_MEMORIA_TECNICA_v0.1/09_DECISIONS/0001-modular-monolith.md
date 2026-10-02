# ADR-0001 — Monolito modular

**Estado:** ACEPTADA

## Contexto
Nomi se encuentra en validación y el equipo necesita iterar rápido. El dominio financiero requiere transacciones coherentes entre Commitment, Transaction, Audit y Outbox.

## Decisión
Un backend desplegable con módulos de dominio separados. Monorepo. No microservicios por anticipación.

## Consecuencias positivas
- menor complejidad operacional;
- transacciones ACID directas;
- depuración simple;
- costo inicial menor;
- refactor de límites dentro de un mismo proceso.

## Consecuencias negativas
- disciplina obligatoria para evitar acoplamiento;
- un despliegue afecta al conjunto;
- escalado inicialmente conjunto.

## Revisión
Reconsiderar sólo cuando existan límites claros de equipo/escalado/regulación/despliegue.
