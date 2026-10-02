# ADR-0005 — Sesión opaca en cookie para web

**Estado:** PROVISIONAL

## Contexto
La PWA web necesita sesiones revocables y no requiere todavía OAuth para terceros.

## Decisión preferida
Cookie HttpOnly/Secure/SameSite con identificador opaco; registro de Session en servidor.

## Razones
- revocación sencilla;
- evita token persistente accesible a JS;
- gestión de múltiples sesiones;
- encaja con password reset y logout remoto.

## Consecuencias
- requiere CSRF;
- persistencia/limpieza de sesiones;
- consulta por sesión en requests.

## Alternativa
Access + refresh tokens en cookies.

## Revisión
Validar con spike técnico antes de congelar OpenAPI de auth.
