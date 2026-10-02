# Nomi — aplicación y memoria técnica

La primera slice funcional ya está implementada en `apps/api` y `apps/web`:

**Registro → Workspace → Contacto → Compromiso → Abono → Historial y Dashboard.**

Consulta [estado y límites de la implementación](docs/IMPLEMENTATION_STATUS.md) y [contratos provisionales](docs/adr/0019-first-slice-contracts.md). La memoria técnica sigue siendo la fuente arquitectónica; su entrada está en [DOC_INDEX](NOMI_MEMORIA_TECNICA_v0.1/DOC_INDEX.md).

## Ejecutar localmente

Requisitos probados: Python 3.14, Node.js 24 y PostgreSQL 18. Docker Compose es opcional para la base.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock
.\.venv\Scripts\python.exe -m pip install --no-deps -e .
npm.cmd ci
Copy-Item .env.example .env
docker compose up -d
.\.venv\Scripts\python.exe -m alembic upgrade head
.\scripts\dev.ps1
```

Abre **http://localhost:3000** y crea una cuenta local. API: **http://127.0.0.1:8000/docs**. No hay cuentas ni contraseñas de usuario predefinidas.

Si Docker está detenido y tienes PostgreSQL 18 instalado en Windows, puedes usar `.\scripts\local-postgres.ps1` en lugar de `docker compose up -d`. Crea un clúster independiente dentro de `.local/postgres`, en loopback y puerto 54329, sin alterar el servicio PostgreSQL existente. Usa autenticación trust únicamente para desarrollo local. Para detener esa instancia: `& 'C:\Program Files\PostgreSQL\18\bin\pg_ctl.exe' -D 'C:\Nomi\.local\postgres' stop`.

En macOS/Linux inicia API y web en dos terminales: `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --no-access-log` y `npm run dev`, con el entorno virtual activado. `.env` es leído por la API. Para Next.js, configura `API_INTERNAL_URL` en el entorno o en `apps/web/.env.local` sólo si cambias el puerto/destino de la API.

## Validación

Crea una base dedicada `nomi_test` (el script Windows ya lo hace). Con Docker: `docker compose exec postgres createdb -U nomi nomi_test`.

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check apps/api scripts
.\.venv\Scripts\python.exe -m alembic check
npm.cmd run typecheck
npm.cmd run build
npm.cmd run test:e2e
```

E2E requiere API y web iniciadas, y Microsoft Edge instalado. Usa datos sintéticos nuevos en cada ejecución. Las pruebas PostgreSQL se limitan a `nomi_test`; `TEST_DATABASE_URL` permite configurar su conexión, conservando ese nombre de base.

Para regenerar contratos: `python scripts/export_openapi.py` y `npx openapi-typescript docs/api/openapi.json -o apps/web/src/lib/schema.d.ts`. CI comprueba que no se desvíen.

Esta entrega es local. Todavía no se ha validado en staging ni cumple el alcance completo de Core: verificación/recuperación de correo, reversión/cancelación, archivo, worker y offline están pendientes. No se envían correos ni se publican datos a proveedores.

Referencias técnicas consultadas: [instalación Next.js](https://nextjs.org/docs/app/getting-started/installation), [CSP Next.js](https://nextjs.org/docs/app/guides/content-security-policy), [DTOs FastAPI](https://fastapi.tiangolo.com/tutorial/response-model/).

## Memoria técnica de referencia

Las rutas de la sección siguiente son relativas a `NOMI_MEMORIA_TECNICA_v0.1/`.

**Versión documental:** 0.1  
**Fecha base:** 2 de octubre de 2026  
**Estado:** Diseño de dominio congelable para `Nomi Core v0.1`; MVP completo aún en evolución.  
**Fuente primaria:** `00_SOURCE/NOMI_PAQUETE_COMPLETO.md`

> Nomi es la forma más simple de controlar el dinero pendiente.

Esta carpeta es la **fuente técnica principal del proyecto Nomi**. No es un README promocional ni un resumen superficial: documenta el producto, los límites del MVP, la arquitectura, el modelo de dominio, el ERD, los contratos entre módulos, los casos de uso, las reglas financieras, la estrategia de persistencia, seguridad, offline, pruebas, despliegue, ADR y habilidades de trabajo recomendadas.

## Cómo usar esta documentación

1. **Producto y alcance:** comenzar en `01_PRODUCT/`.
2. **Arquitectura general:** continuar con `02_ARCHITECTURE/`.
3. **Entidades y reglas:** leer `03_DOMAIN/`.
4. **Comportamiento ejecutable:** revisar `04_USE_CASES/`.
5. **Persistencia y PostgreSQL:** consultar `05_DATA/`.
6. **API, identidad y seguridad:** `06_API_SECURITY/`.
7. **Frontend/PWA/offline:** `07_FRONTEND_PWA/`.
8. **Pruebas, observabilidad y operación:** `08_OPERATIONS/`.
9. **Decisiones arquitectónicas:** `09_DECISIONS/`.
10. **Orden de implementación:** `10_ROADMAP/`.
11. **Skills de desarrollo y revisión:** `11_SKILLS/`.

## Principio rector

La arquitectura está diseñada alrededor de una cadena de responsabilidades:

```text
IDENTITY
   ↓
USER
   ↓
MEMBERSHIP
   ↓
WORKSPACE
   ↓
CONTACT
   ↓
COMMITMENT
   ↓
TRANSACTION
   ↓
AUDIT / OUTBOX / REPORTING
```

Cada módulo tiene una responsabilidad clara. Los módulos están conectados, pero no deben invadir las reglas ni las tablas internas de los demás. Las operaciones que cruzan límites se coordinan mediante **casos de uso**, repositorios/puertos y, cuando corresponde, **eventos/outbox**.

## Decisiones importantes de Core v0.1

- Monolito modular API-first.
- Next.js + TypeScript para PWA; FastAPI + Python para API.
- PostgreSQL como fuente de verdad.
- Dinero en `BIGINT` usando unidad monetaria menor; nunca `FLOAT`.
- Una moneda por Workspace en Core v0.1.
- `VARCHAR + CHECK` en PostgreSQL para enums de dominio; `Enum` tipado en Python.
- Estados persistidos del compromiso: `open`, `paid`, `cancelled`.
- Estados de pago y tiempo derivados, no duplicados en la base.
- Movimientos Core: `payment` y `reversal`.
- Reversión como nueva transacción autorreferenciada; no edición destructiva de movimientos.
- `reversal_of_transaction_id` nullable, FK y `UNIQUE`.
- `balance_minor` protegido por `0 <= balance <= original_amount`.
- Idempotencia por registro dedicado + hash de petición.
- Bloqueo optimista con `version`.
- Autenticación web orientada a sesión segura en cookie HttpOnly.
- Workspace como frontera de propiedad y aislamiento de datos.
- Dashboard derivado de compromisos; no es una segunda fuente financiera.
- Offline se implementa por etapas y nunca debe sobrescribir silenciosamente movimientos financieros.

## Estado de decisiones

Esta memoria usa tres etiquetas:

- **ACEPTADA:** decisión base del documento maestro o decisión ya adoptada para Core v0.1.
- **PROVISIONAL:** dirección preferida que debe validarse durante la primera implementación.
- **PLANIFICADA:** pertenece a MVP posterior o versiones futuras.

Cuando una decisión cambie, debe actualizarse el ADR correspondiente y los documentos afectados.
