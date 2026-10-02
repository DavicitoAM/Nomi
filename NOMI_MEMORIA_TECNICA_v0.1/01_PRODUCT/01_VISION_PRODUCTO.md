# Visión de producto

## Qué es Nomi

Nomi es un SaaS web progresivo, mobile-first y tolerante a conectividad inestable para **registrar, consultar y dar seguimiento al dinero pendiente**. Maneja tanto dinero por cobrar como dinero por pagar sin pretender convertirse en un ERP, un sistema contable, fiscal o bancario.

La experiencia debe responder rápidamente:

1. ¿Cuánto me deben?
2. ¿Cuánto debo?
3. ¿Qué requiere atención?
4. ¿Qué ocurrió con un saldo determinado?

## Problema

El usuario objetivo suele distribuir información entre chats, hojas de cálculo, libretas, notas y memoria. Esto produce:

- obligaciones olvidadas;
- pagos/abonos que no se reflejan correctamente;
- dificultad para reconstruir el historial;
- falta de claridad sobre vencimientos;
- fricción para conocer la posición pendiente actual.

Nomi no intenta “contabilizar” la empresa. Su función es mantener una representación simple y trazable de **compromisos financieros declarados por el usuario**.

## Usuarios iniciales

### Profesional independiente

Cobra por proyecto, anticipo o entregable. Necesita conocer saldos y vencimientos sin entrar en terminología contable.

### Negocio con venta a crédito

Registra fiado, abonos y pagos parciales. Opera principalmente desde celular y necesita historial por persona.

### Segmentos posteriores

- arrendadores;
- prestadores recurrentes;
- préstamos informales;
- equipos pequeños.

## Principios de producto

### Captura rápida

La primera captura debe ser clara y las capturas posteriores deben aspirar a menos de 20 segundos.

### Claridad antes que complejidad

El vocabulario de UI favorece:

- “Me deben”;
- “Yo debo”;
- “Pendiente”;
- “Abono”;
- “Vence”;
- “Pagado”;
- “Cancelado”.

La implementación interna puede usar nombres técnicos sin trasladarlos innecesariamente a la interfaz.

### Mobile-first

La aplicación se diseña para celular desde el inicio. Escritorio es una expansión del layout, no el modelo principal.

### Offline-tolerant

Offline no significa “todo funciona sin servidor”. Significa:

- consulta reciente;
- captura básica;
- cola durable;
- sincronización explícita;
- conflictos visibles.

### Portabilidad

Exportar y eliminar datos no son funciones premium de retención.

### Privacidad por diseño

Guardar lo mínimo necesario. No asumir que el usuario desea compartir datos de sus contactos con terceros.

## Lo que Nomi NO es

Nomi Core/MVP no es:

- ERP;
- contabilidad;
- facturación fiscal;
- pasarela de pago;
- banco;
- buró de crédito;
- CRM generalista;
- cobranza automática agresiva;
- mensajería automática a deudores;
- integración bancaria;
- marketplace;
- microservicios.

## Regla para nuevas funcionalidades

Antes de aceptar una función se debe preguntar:

> ¿Ayuda directamente a registrar, explicar, consultar, recordar o controlar un pendiente?

Si la respuesta es no, probablemente no pertenece a Core/MVP.
