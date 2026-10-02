# Privacidad y datos

> Documento técnico de diseño; no sustituye revisión legal aplicable en México.

## Categorías

### Cuenta
- nombre;
- correo;
- password hash.

### Preferencias
- moneda;
- timezone;
- notificaciones.

### Contactos de terceros
- nombre;
- teléfono opcional;
- email opcional;
- notas.

### Finanzas declaradas
- montos;
- conceptos;
- fechas;
- saldos;
- movimientos.

### Técnica
- request IDs;
- errores;
- eventos de seguridad;
- IP sólo cuando sea necesaria y con retención limitada.

### Billing
- IDs del proveedor; no datos completos de tarjeta.

## Principios

- minimización;
- propósito específico;
- acceso restringido;
- portabilidad;
- retención limitada;
- purga verificable;
- transparencia.

## Eliminación

`DELETE /me` inicia un proceso:

```text
confirmar identidad
→ deletion_pending
→ revocar sesiones
→ ventana de recuperación
→ purga controlada
```

No fijar duración legal/operativa sin revisión.

## Backups

Una purga no implica reescribir inmediatamente backups históricos si la estrategia de backups usa expiración; debe existir política de retención y restauración coherente.

## Logs

No usar datos financieros como “debug”.
