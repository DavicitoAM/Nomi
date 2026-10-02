# Reporting y Dashboard

## Principio

Dashboard es una proyección de lectura. No almacena una segunda verdad financiera.

## Métricas Core

- saldo por cobrar activo;
- saldo por pagar activo;
- saldo vencido;
- saldo por vencer en siete días;
- número de compromisos activos.

## Fuente

Principalmente `commitments`:

```text
workspace_id = current
lifecycle_status = open
deleted_at IS NULL
```

Después se agrupa por `direction`, balance y due_date.

## Exclusiones

No sumar:

- `paid`;
- `cancelled`;
- soft-deleted;
- otro workspace.

## Contact summary

Por contacto:

- total receivable activo;
- total payable activo;
- vencido;
- cantidad de compromisos;
- actividad reciente.

## No compensación automática

`10,000 receivable` y `3,000 payable` se muestran separados. Un neto puede existir como dato secundario futuro, nunca como sustituto de las obligaciones.

## Evolución

Si la escala exige optimización pueden introducirse:

- índices;
- views;
- materialized views;
- read models.

Pero sólo cuando medición lo justifique. Nunca crear una tabla manual de Dashboard desde el inicio.
