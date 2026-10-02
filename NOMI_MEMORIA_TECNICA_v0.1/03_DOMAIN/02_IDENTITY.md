# Identity / User / Session

## Responsabilidad

Identity demuestra quién es la persona que realiza una petición. No decide por sí solo si puede acceder a un compromiso concreto; esa decisión utiliza Membership y Workspace.

## User

Campos Core:

```text
id
email
password_hash
display_name
status
email_verified_at
created_at
updated_at
```

### Estados propuestos

- `pending_verification`
- `active`
- `disabled`
- `deletion_pending`

### Reglas

- email normalizado y único;
- contraseña jamás en texto plano;
- hash Argon2id;
- cambio de contraseña invalida sesiones previas;
- eliminación de cuenta inicia un proceso, no un DELETE inmediato.

## Session

Estrategia preferida para la web: sesión opaca, revocable y almacenada del lado servidor.

```text
id
user_id
token_hash
created_at
last_seen_at
expires_at
revoked_at
```

La cookie contiene el secreto opaco y usa:

- `HttpOnly`;
- `Secure`;
- `SameSite`;
- protección CSRF para operaciones mutables.

No persistir tokens de sesión en `localStorage`.

## Registro

Registro crea atómicamente:

```text
User
+
Workspace
+
Membership(owner)
```

Después crea sesión y programa correo de verificación.

## Recuperación de contraseña

Entidad auxiliar:

```text
PasswordResetToken
id
user_id
token_hash
expires_at
used_at
created_at
```

El endpoint de “olvidé mi contraseña” no debe revelar si un email existe.

## Verificación de email

Misma filosofía:

```text
EmailVerificationToken
id
user_id
token_hash
expires_at
used_at
created_at
```

## Autenticación vs autorización

```text
Authentication:
¿la sesión pertenece a U1?

Authorization:
¿U1 tiene Membership en W1
y puede operar el recurso?
```

Ambas comprobaciones son obligatorias.
