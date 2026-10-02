# Autenticación y sesiones

## Estrategia Core preferida

Sesión opaca del lado servidor para la aplicación web.

### Cookie

- `HttpOnly`;
- `Secure`;
- `SameSite=Lax` o `Strict` según flujos;
- path apropiado;
- expiración explícita.

### Servidor

`Session` contiene:

- token hash;
- user_id;
- expiración;
- revocación;
- last_seen opcional.

## Flujo de login

1. normalizar email;
2. buscar User;
3. verificar Argon2id;
4. validar status;
5. rotar/crear Session;
6. set cookie;
7. audit de autenticación sin secretos.

## Logout

Revocar Session del servidor y limpiar cookie.

## Cambio de password

- verificar identidad;
- nuevo hash;
- invalidar sesiones anteriores;
- emitir evento/audit.

## Password reset

- respuesta genérica para no enumerar emails;
- token aleatorio de un uso;
- almacenar hash del token;
- expiración corta;
- marcar `used_at`;
- revocar sesiones después de reset.

## Verificación de email

Token de un uso similar.

## CSRF

Como la cookie se envía automáticamente, POST/PATCH/DELETE requieren protección CSRF adecuada.

## `GET /me`

Devuelve un contexto mínimo:

```json
{
  "user": {},
  "workspace": {},
  "membership": {}
}
```

No expone secretos ni metadata interna de seguridad.

## OAuth/OIDC

No necesario para Core web. Puede añadirse para app nativa o integraciones futuras sin cambiar la semántica de Workspace.
