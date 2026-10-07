# Primer cliente Android de Nomi

Fecha: 2026-10-07. Alcance autorizado: Android primero, después de la vertical Core
validada localmente. Decisión: [ADR-0023](adr/0023-android-first-client.md).
Esta entrega es un APK debug local; no es una publicación ni una certificación de Google Play.

## Qué se construyó

`apps/mobile` empaqueta React/TypeScript/Vite con Capacitor 8.5.3. Reutiliza componentes
cliente y estilos de `apps/web`; conserva azul tinta/lavanda y navegación móvil.
Los assets viajan dentro del APK. La app no necesita un servidor Next.js para mostrar su UI.
Sí necesita la API FastAPI y PostgreSQL para consultar/confirmar operaciones.

`NomiApiPlugin` restringe las llamadas al origen configurado y a `/api/v1`. Las sesiones
opacas y CSRF existentes se guardan cifrados AES-GCM con una clave Android Keystore;
el JavaScript no recibe credenciales. Se desactivó el CookieHandler global de Capacitor
y la aceptación de cookies en WebView: la prueba detectó inicialmente esa copia de
credenciales y comprobó la corrección. No se relajó CORS/CSRF en el backend.

El saldo confirmado, historial y cuentas permanecen en PostgreSQL. IndexedDB mantiene
intenciones financieras inciertas por cuenta/Workspace con la misma clave idempotente.
No es sincronización offline completa: no ofrece catálogo financiero persistente sin red.
Cerrar el proceso conserva sesión/intenciones; desinstalar borra datos locales y puede
perder intenciones no confirmadas. Los registros confirmados del servidor permanecen.

Atrás cierra diálogos antes de minimizar. Exportar usa el selector nativo de Android
sin permisos generales de almacenamiento. La app desactiva backups y transferencia de
datos privados; esto no reemplaza los respaldos de PostgreSQL.

## Compilar y probar en Windows

Requisitos: Node.js 24, JDK 21, Android SDK plataforma 36/build-tools 36.0.0/platform-tools.
SDK mínimo 24, target 36. Los instaladores/toolchains locales quedan ignorados en `.local`.
`scripts/android-env.ps1` los detecta; fuera de esta máquina configura `JAVA_HOME` y
`ANDROID_HOME` con tus instalaciones. El script sólo cambia el entorno del proceso.

```powershell
npm.cmd ci
.\scripts\android-build.ps1
```

El script compila/sincroniza assets, genera `:app:assembleDebug`, ejecuta cuatro pruebas
JVM y Android Lint. APK: `apps/mobile/android/app/build/outputs/apk/debug/app-debug.apk`.
Se conserva una copia de entrega local en `.local/releases/nomi-0.1.0-debug.apk`.
No subir APKs, toolchains, almacenes de claves ni datos `.local` al repositorio.

Para instalar con un emulador o teléfono autorizado conectado por USB, inicia API y
PostgreSQL conforme al README y ejecuta (sustituye el serial por el de tu dispositivo):

```powershell
. .\scripts\android-env.ps1
& "$env:ANDROID_HOME/platform-tools/adb.exe" devices
& "$env:ANDROID_HOME/platform-tools/adb.exe" -s emulator-5554 reverse tcp:8000 tcp:8000
& "$env:ANDROID_HOME/platform-tools/adb.exe" -s emulator-5554 install -r .local/releases/nomi-0.1.0-debug.apk
& "$env:ANDROID_HOME/platform-tools/adb.exe" -s emulator-5554 shell am start -n app.nomi.mobile.debug/app.nomi.mobile.MainActivity
```

Debug apunta a `http://127.0.0.1:8000` del dispositivo; `adb reverse` lo conecta con tu PC.
Sólo loopback permite HTTP. Un APK enviado por mensajería a un teléfono sin esta conexión
no puede llegar a la API de la PC. Crea una cuenta desde la app; no hay contraseña maestra
ni usuario predefinido. Desarrollo entrega los mensajes al buzón local del README.

La prueba automática exige un **emulador sintético**: crea usuarios/datos de prueba,
cierra/reabre la app, interrumpe la conexión ADB y guarda una exportación en Downloads.
No apunta a un teléfono personal ni debe ejecutarse contra producción.

```powershell
npx.cmd playwright install android
node scripts/android-smoke.mjs
```

Con más de un emulador configura `NOMI_EMULATOR`. El emulador debe estar iniciado y el APK
instalado; la API local debe estar disponible en el puerto 8000. El test usa Playwright
Android WebView y el selector de archivos nativo. Evidencia: `.local/android-evidence/`.

## Evidencia y límites

- APK compilado e instalado en Android 16/API 36, emulador x86_64 con WebView 133.
- Cuatro pruebas JVM de destino fijo HTTPS, bloqueo de rutas/redirecciones, HTTP local
  sólo en debug y rechazo de orígenes/métodos inválidos.
- E2E Android: registro, contacto, compromiso de $10,000, edición descriptiva PATCH,
  abono de $2,500, saldo $7,500, cierre/reinicio del proceso, reversión y saldo $10,000.
- Desconexión real de ADB, intención durable tras reinicio y recuperación única de otro
  abono de $100: saldo $9,900. No se simula aquí pérdida de respuesta después del commit;
  esa prueba ya existe en E2E web.
- Credenciales fuera de cookies WebView/localStorage, archivo de sesión cifrado, destino
  ajeno rechazado, cierre de sesión conservado tras reinicio.
- Exportación mediante selector nativo: archivo JSON con un contacto, saldo $9,900 y
  tres movimientos (dos pagos y una reversión).
- Build web y las 16 pruebas E2E web pasaron después de añadir el adaptador compartido.
  Sin cambios de backend, migraciones u OpenAPI en este milestone.
- CI tiene un job Android de build/JVM/lint y artefacto debug. No se ejecutó CI remoto
  ni E2E Android en CI; la evidencia del emulador es local.
- Resultado final: 12 comprobaciones Android E2E, 4 pruebas JVM y 16 E2E web aprobadas;
  Android Lint con 0 errores y 16 advertencias. `npm audit`: 0 vulnerabilidades reportadas;
  revisión de secretos: 320 archivos, sin hallazgos sin revisar.
- `bundleRelease --dry-run` rechazó correctamente la ausencia de orígenes HTTPS reales.
  SHA-256 del APK de entrega:
  `E1A82EDC327BB5F40066DC878836DE43EE86D7827E0D6304B4040CE000CFFFC2`.

El build Vite avisa sobre `use client` en los componentes compartidos: aquí todo ese
código se ejecuta en cliente; no se importan componentes servidor. Android Lint conserva
avisos de recursos generados por Capacitor y versión del wrapper; no se ocultan con baseline.
La compilación Windows de Gradle 8.14.3 presentó su incidencia de renombrado de caché;
se recuperó localmente. No se deshabilitó antivirus ni se considera resuelta en otras PCs.

No se ha validado un teléfono físico, versiones Android antiguas, TalkBack, restauración
en dispositivos de distintos fabricantes, pérdida de la clave Keystore ni un proveedor
HTTPS real. Los controles de backup se revisaron, sin un ensayo de transferencia D2D.
La captura revisada muestra la app real en emulador, no una maqueta web.

## Puerta de publicación

1. Backend/PostgreSQL alojados con HTTPS, SMTP real, monitoreo, restore y smoke de staging.
2. Identidad final de paquete y firma de upload custodiada por el propietario. Definir
   `NOMI_API_URL` y `NOMI_WEB_ORIGIN` HTTPS al compilar. `android-build.ps1 -Release`
   genera un bundle **sin firma de producción configurada**, no listo para cargar a Play.
3. Eliminación de cuenta/datos y retención explícita, privacidad y declaraciones Data Safety.
4. App Links HTTPS con dominio verificado para correo: el esquema `nomi://account` sólo
   existe en debug. Los correos actuales siguen abriendo la web; falta integración nativa
   de enlaces de producción. No usar un esquema personalizado para tokens en release.
5. Pruebas en dispositivos, accesibilidad nativa, bundle de release, ficha/capturas y el
   canal de pruebas aplicable a la cuenta de Play Console.

AdMob, Play Billing e iOS no se implementaron. La publicación y requisitos vigentes de la
cuenta deben validarse en Play Console cuando exista; este documento no afirma aprobación.

Referencias: [Capacitor Android](https://capacitorjs.com/docs/android),
[Playwright Android](https://playwright.dev/docs/api/class-android),
[reglas de backup Android](https://developer.android.com/identity/data/autobackup),
[incidencia Gradle Windows](https://github.com/gradle/gradle/issues/38921).
