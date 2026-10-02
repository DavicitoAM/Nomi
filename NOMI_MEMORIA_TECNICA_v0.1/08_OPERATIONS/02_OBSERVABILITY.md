# Observabilidad

## Objetivos

- detectar fallos;
- correlacionar frontend/API/worker;
- medir latencia;
- identificar errores de sincronización;
- proteger PII financiera.

## OpenTelemetry

Instrumentación vendor-neutral con OTLP.

## Logs estructurados

Ejemplo:

```json
{
  "timestamp": "...",
  "level": "INFO",
  "service": "nomi-api",
  "environment": "production",
  "request_id": "...",
  "trace_id": "...",
  "route": "/api/v1/commitments",
  "method": "POST",
  "status_code": 201,
  "duration_ms": 142
}
```

No incluir concepts, nombres, emails, phone, tokens ni payload financiero completo.

## Métricas técnicas

- request rate;
- p50/p95/p99;
- error rate;
- DB pool;
- slow queries;
- outbox lag;
- reminder lag;
- sync conflicts.

## Métricas de producto

Separadas de logs de seguridad:

- activación;
- primer compromiso;
- WAU;
- pagos registrados;
- recordatorios configurados;
- exportaciones.

## Alertas

- 5xx sostenidos;
- error budget;
- outbox atrasada;
- backup fallido;
- DB storage bajo;
- anomalía de login failures.

## Request ID

Toda respuesta/API log debe poder correlacionarse con `X-Request-ID`.
