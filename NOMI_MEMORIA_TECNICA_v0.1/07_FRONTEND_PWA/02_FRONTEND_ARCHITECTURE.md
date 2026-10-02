# Arquitectura frontend

## Stack

- Next.js App Router;
- TypeScript;
- Tailwind CSS;
- TanStack Query;
- React Hook Form;
- Zod;
- IndexedDB repository;
- Service Worker.

## Organización por feature

```text
src/
├── app/
├── components/
├── features/
│   ├── auth/
│   ├── contacts/
│   ├── commitments/
│   ├── transactions/
│   ├── dashboard/
│   └── settings/
├── offline/
├── lib/
├── telemetry/
└── types/
```

## Estado

### Server state

TanStack Query:

- contacts;
- commitments;
- dashboard;
- histories.

### Form state

React Hook Form + Zod.

### Local UI state

Mantenerlo local cuando sea posible. No introducir store global por reflejo.

### Auth

Frontend no guarda secreto en localStorage. Usa cookie segura y `/me`.

## Actualización después de Payment

El endpoint devuelve Payment + Commitment actualizado. Frontend puede:

1. actualizar cache del Commitment;
2. invalidar dashboard;
3. invalidar resumen del Contact;
4. insertar movimiento en historial local.

## Errores

Mapear `problem.code` a UI estable.

Ejemplo `VERSION_CONFLICT`:

> El saldo cambió desde que abriste esta pantalla. Actualizamos la información; revisa el monto antes de volver a guardar.

## PWA

Service Worker no debe cachear indiscriminadamente respuestas sensibles. Definir políticas por ruta y tipo de recurso.
