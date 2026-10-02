# PRD — Nomi MVP

## Objetivo

Validar si una experiencia extremadamente simple de control de pendientes mejora el seguimiento financiero de freelancers y microempresas.

## Trabajo principal del usuario

Cuando surge una obligación, el usuario necesita registrarla sin fricción. Cuando ocurre un pago o abono, necesita actualizar el saldo sin recalcular. Cuando abre Nomi, necesita localizar vencidos y próximos compromisos. Cuando habla con un contacto, necesita reconstruir su historial.

## MVP funcional

El MVP completo contempla:

- registro, acceso, recuperación y cierre de sesión;
- perfil y preferencias básicas;
- contactos;
- compromisos por cobrar y por pagar;
- pagos/abonos parciales;
- saldo automático;
- estados/condiciones de pago y tiempo;
- dashboard;
- historial y auditoría esencial;
- recordatorios in-app y correo;
- PWA instalable;
- lectura offline;
- cola offline para altas y abonos;
- exportación CSV;
- eliminación de cuenta;
- panel administrativo mínimo.

## Nomi Core v0.1

Antes del MVP completo se construirá una rebanada vertical mínima:

```text
RegisterUser
    ↓
Workspace personal
    ↓
CreateContact
    ↓
CreateCommitment
    ↓
RegisterPayment
    ↓
GetDashboardSummary
```

Incluye además:

- reversión;
- cancelación;
- archivo de contactos;
- auditoría;
- idempotencia;
- aislamiento por workspace;
- concurrencia optimista.

No incluye aún:

- recurrencias;
- adjuntos;
- PDF;
- multiusuario funcional;
- suscripción real;
- multimoneda;
- ajustes financieros avanzados;
- IA/predicción.

## Criterios de éxito de producto

Las metas del piloto permanecen como hipótesis:

- activación mediante primer compromiso;
- tiempo corto hasta primer valor;
- captura posterior rápida;
- retorno semanal;
- baja tasa de errores no recuperados;
- comprensión del saldo por usuarios reales.

## Métrica principal

Usuarios activos semanales que consultan o actualizan al menos un compromiso vigente.

No se usa “monto cobrado” como única métrica porque Nomi no procesa necesariamente el cobro.
