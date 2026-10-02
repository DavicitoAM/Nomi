# Modelo de seguridad

## Objetivo

Aplicar defensa en profundidad sobre datos personales y financieros declarados por el usuario.

## Fronteras

### Navegador → API

Amenazas:

- robo de sesión;
- CSRF;
- XSS;
- abuso de endpoints.

Controles:

- cookie segura;
- CSP;
- CSRF;
- CORS explícito;
- headers de seguridad;
- validación de input;
- rate limiting.

### API → DB

Amenazas:

- IDOR/BOLA;
- reglas omitidas;
- manipulación de saldo;
- SQL injection.

Controles:

- aislamiento por Workspace en queries;
- ORM parametrizado;
- constraints;
- UoW;
- optimistic locking;
- tests negativos.

## Aislamiento por Workspace

Patrón:

```sql
WHERE id = :id
AND workspace_id = :current_workspace
```

No cargar primero por ID y “confiar” después.

## Support admin

Rol de plataforma separado.

No obtiene acceso financiero automático. Cualquier acceso de soporte debe:

- ser temporal;
- justificarse;
- auditarse;
- aplicar mínimo privilegio.

## Logs

Nunca registrar:

- passwords;
- tokens;
- cookies;
- cuerpos financieros completos;
- PII sin necesidad.

## Secretos

Fuera del repo, por variables/secret manager.

## Browser headers

Objetivo:

- HSTS;
- CSP estricta;
- X-Content-Type-Options;
- Referrer-Policy;
- Permissions-Policy;
- CORS mínimo.

## Rate limiting

Prioridades:

- login;
- password reset;
- registro;
- exportaciones;
- endpoints susceptibles de abuso.

Redis sólo cuando el despliegue distribuido lo necesite.

## Seguridad de dependencias

CI:

- secret scanning;
- SAST;
- dependency scanning;
- imágenes contenedor;
- SBOM para producción cuando se formalice.
