# Nomi — Memoria técnica y arquitectura de referencia

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
