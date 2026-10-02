# Respuesta a incidentes

## Flujo

1. detectar;
2. clasificar severidad;
3. contener;
4. preservar evidencia mínima;
5. erradicar causa;
6. restaurar;
7. verificar integridad;
8. comunicar según obligaciones;
9. postmortem;
10. acciones correctivas.

## Incidentes financieros

Prioridad:

- detener nuevas escrituras si la integridad está en riesgo;
- preservar Transaction/Audit;
- no “arreglar” saldos con UPDATE manual sin registro;
- ejecutar herramienta de reconciliación;
- aplicar corrección auditada.

## Incidente de aislamiento

Si un usuario ve datos de otro Workspace:

- severidad crítica;
- contener endpoint/feature;
- investigar alcance mediante logs/audit sanitizados;
- revocar sesiones si aplica;
- corregir y añadir test negativo permanente.

## Postmortem

Debe explicar sistema y condiciones, no buscar culpables.

Campos:

- timeline;
- impacto;
- detección;
- causa raíz;
- factores contribuyentes;
- mitigación;
- acciones con owner/fecha.
