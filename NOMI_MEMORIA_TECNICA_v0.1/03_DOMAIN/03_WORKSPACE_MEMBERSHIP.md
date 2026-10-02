# Workspace y Membership

## Workspace

Workspace es el contenedor lógico de los datos.

```text
id
name
currency_code
timezone
created_at
updated_at
```

No debe confundirse con User.

## Modelo Core

```text
1 User
  ↓
1 Membership(owner)
  ↓
1 Workspace personal
```

El usuario no tiene que configurar manualmente una “empresa” para empezar.

## Modelo futuro

```text
Workspace
 ├─ Owner
 ├─ Member
 └─ Member
```

Los contactos y compromisos siguen perteneciendo al Workspace, no a quien los creó.

## Moneda

Core v0.1: una moneda principal por Workspace.

```text
Commitment.currency_code == Workspace.currency_code
Transaction.currency_code == Commitment.currency_code
```

La moneda predeterminada para mercado inicial es MXN.

Una vez existen operaciones financieras, el cambio de moneda queda bloqueado en Core. Multi-divisa requiere un diseño explícito futuro.

## Timezone

`Workspace.timezone` es el reloj de negocio para:

- determinar “hoy”;
- calcular vencidos;
- calcular próximos vencimientos;
- programar recordatorios;
- mostrar timestamps.

`due_date` es una fecha; timestamps de eventos se guardan en UTC.

## Membership

```text
id
user_id
workspace_id
role
created_at
```

Roles de workspace:

- `owner`
- `member` (preparado para futuro)

`support_admin` debe ser rol de plataforma, no una Membership artificial en todos los workspaces.

## Invariantes

- un recurso financiero siempre pertenece a un Workspace;
- un User necesita Membership para operar;
- frontend no decide la propiedad enviando `workspace_id`;
- Contact y Commitment relacionados deben pertenecer al mismo Workspace;
- soporte no obtiene acceso financiero implícito.
