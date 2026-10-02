---
name: nomi-security-review
description: Revisa seguridad de una feature de Nomi, especialmente sesión, CSRF, BOLA/IDOR, workspace isolation, secretos y PII.
---

# Security Review Skill

## Checklist

### Auth
- sesión válida;
- expiración;
- revocación;
- rotación cuando corresponda.

### Authorization
- query scoped por Workspace;
- deny by default;
- test de recurso ajeno;
- role checks.

### Browser
- CSRF para mutaciones;
- CSP;
- CORS explícito;
- cookie HttpOnly/Secure/SameSite.

### Input
- Pydantic schema;
- límites de tamaño;
- archivos limitados;
- no confiar en IDs de owner.

### Output
- no stack traces;
- 404 para recursos ajenos;
- Problem Details.

### Logging
- no tokens/cookies/passwords;
- no bodies financieros;
- PII mínima.

### Abuse
- rate limit;
- idempotencia;
- cuotas cuando apliquen.

## Entregable

Lista de hallazgos por severidad + test preventivo por hallazgo.
