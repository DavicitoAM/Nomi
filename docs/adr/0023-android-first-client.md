# ADR-0023 — Primer cliente Android

Estado: **ACEPTADA para implementación y pruebas locales**, 2026-10-07.
Autorización: el usuario eligió Google Play/Android primero y pidió construir la app.

## Contexto y cambio de alcance

ADR-0020/0022 y el plan anterior excluían Mobile del cierre Core. La vertical ya pasó
pruebas PostgreSQL y E2E; esta autorización abre el siguiente milestone. Sustituye esa
exclusión de alcance únicamente para Android. Ads, Billing e iOS siguen posteriores.
El documento de producto proponía Capacitor provisionalmente: se adopta para esta
primera app, con validación Android explícita antes de afirmar preparación para tienda.

## Decisión

- apps/mobile usa React, TypeScript, Vite y Capacitor. Empaqueta assets locales: no utiliza
  server.url para cargar una web remota. Next.js mantiene su frontend web y SSR.
- Reutiliza temporalmente componentes cliente, tipos OpenAPI, formularios y estilos de
  apps/web mediante imports de compilación. No ejecuta Next.js en Android. Esta dependencia
  explícita evita duplicar la UI; extraer packages compartidos cuando haya divergencia real.
- La API FastAPI y PostgreSQL continúan como fuente de verdad. No cambia el contrato
  financiero, la autorización, las migraciones ni el modelo transaccional.
- Un adaptador Android restringido llama exclusivamente /api/v1 del servidor configurado
  en compilación. Conserva sesiones opacas existentes y CSRF en almacenamiento privado
  cifrado mediante Android Keystore; no entrega cookies ni tokens al JavaScript.
  Incluye Origin del servidor web configurado para mantener el contrato HTTP actual.
  Origin sigue siendo defensa del navegador; no sustituye autenticar/autorizar al cliente.
- HTTP sólo para debug por loopback con adb reverse. Release exige servidor HTTPS y
  origen explícitos. Sin redirecciones de credenciales ni navegación remota en WebView.
- Intenciones financieras conservan IndexedDB scoped, claves idempotentes y resolución
  explícita existentes. Sin backups Android de datos privados; desinstalar elimina datos
  locales, pero los commits permanecen en PostgreSQL.
- Atrás cierra primero diálogos. El enlace nomi://account se limita a debug para pruebas;
  release esperará App Links HTTPS verificados cuando exista dominio propio. El correo
  actual mantiene enlaces web; no se declara integrada su apertura nativa de producción.
  Exportación usa el selector de archivos Android, sin permisos generales de almacenamiento.
- Se desactiva el CookieHandler global que instala Capacitor y la aceptación de cookies
  del WebView: incluso con CapacitorCookies deshabilitado en JS, su transporte HTTP
  puede copiar Set-Cookie al WebView. La prueba Android comprueba ese aislamiento.

## Alternativas e impacto

Kotlin/Compose y React Native exigen recrear la UI; son válidos si futuras necesidades
justifican ese coste. Cargar una URL remota deja el arranque dependiente de la web y no
es esta decisión. Capacitor aprovecha la UI, pero requiere probar WebView, teclado,
sesiones, cierre de procesos y almacenamiento en Android, no sólo en Playwright.

Cambios: apps/mobile, adaptadores mínimos en cliente compartido, pruebas y documentación.
Sin migración de datos ni relajación de cookies/CORS/CSRF de la web. El identificador de
debug no implica propiedad de un dominio; definir identidad y firma de producción antes
de la primera publicación. Eliminar cuenta, privacidad/Data Safety, backend alojado,
App Links verificados, firma custodiada y pruebas de Play son requisitos de release separados.

## Puerta de validación

Build web sin regresiones; build Android; registro/contacto/compromiso/pago/reversión/dashboard
desde el cliente móvil, persistencia de sesión y saldo tras reinicio, logout y bloqueo de URLs
ajenas. Documentar qué se ejecutó en WebView/dispositivo y qué quedó sólo en navegador/JVM.
Un APK debug no equivale a un AAB firmado de producción ni a aprobación de Google Play.
