# Menú Digital QR — SaaS multi-tenant para restaurantes

## Resumen del producto

Plataforma SaaS donde varios restaurantes (tenants) publican su menú digital accesible por código QR. El cliente escanea el QR en su mesa, ve el menú, ordena y paga desde el navegador (sin salir de la página), la cocina recibe el ticket en tiempo real, y el pedido se entrega en la mesa o se marca listo para retiro (el mecanismo de aviso al cliente para retiro está pendiente de definir).

## Stack técnico

- **Backend**: FastAPI (Python), async
- **Base de datos**: PostgreSQL + SQLAlchemy (async) — Postgres desde el inicio por soporte multi-tenant robusto y JSON fields
- **Frontend**: React (Vite)
- **Tiempo real**: WebSockets (FastAPI nativo) para actualizar la pantalla de cocina sin refrescar
- **Pasarela de pago**: Tilopay (SDK JS embebido, sin redirección) — soporta tarjetas + SINPE Móvil + Apple Pay
- **Notificación de "pedido listo"**: fuera de alcance del MVP, pendiente de definir (ver sección "Notificación al cliente — pendiente de definir")
- **Despliegue**: Docker / docker-compose para desarrollo local

## Modelo de datos (borrador para SQLAlchemy)

Todas las tablas de negocio llevan `restaurante_id` para aislar datos entre tenants.

```
Restaurante
- id (PK)
- nombre
- slug (subdominio / identificador único, ej. "pizzeria-luna")
- tilopay_llave_api (encriptada)
- tilopay_usuario_api (encriptada)
- tilopay_password_api (encriptada)
- creado_en

Mesa
- id (PK)
- restaurante_id (FK)
- numero (o null si es solo "para retirar")
- codigo_qr (identificador único usado en la URL del QR)

Categoria
- id (PK)
- restaurante_id (FK)
- nombre
- orden

Item
- id (PK)
- restaurante_id (FK)
- categoria_id (FK)
- nombre
- descripcion
- precio
- disponible (bool)
- imagen_url (opcional)

Cliente
- id (PK)
- restaurante_id (FK)
- nombre
- correo
- telefono
- consentimiento_datos (bool)
- creado_en

Pedido
- id (PK)
- restaurante_id (FK)
- mesa_id (FK, nullable si es para retirar)
- cliente_id (FK)
- estado (enum: recibido, en_cocina, listo, entregado, cancelado)
- metodo_pago (enum: tarjeta, sinpe, apple_pay, efectivo_en_restaurante)
- monto_total
- tilopay_transaction_id (nullable)
- tipo_entrega (enum: mesa, retiro)
- creado_en
- actualizado_en

ItemPedido
- id (PK)
- pedido_id (FK)
- item_id (FK)
- cantidad
- precio_unitario (snapshot del precio al momento de ordenar)
- notas (opcional, ej. "sin cebolla")
```

## Flujos principales

### 1. Cliente escanea QR y ordena
1. QR codifica una URL tipo `/r/{restaurante_slug}/mesa/{codigo_qr}`
2. Frontend carga el menú del restaurante (categorías + items disponibles)
3. Cliente arma su carrito y pasa a checkout
4. Checkout pide: nombre, correo, teléfono, checkbox de consentimiento de datos (requerido para guardar Cliente)
5. Cliente selecciona método de pago: Tarjeta (SDK Tilopay embebido) / SINPE Móvil / Apple Pay (si el navegador lo soporta) / Efectivo en el restaurante
6. Si es pago online: se procesa con Tilopay usando las credenciales del restaurante específico; al confirmar, el pedido pasa a estado `recibido`
7. Si es efectivo: el pedido pasa directo a `recibido` sin proceso de pago

### 2. Cocina recibe el pedido
1. Al crearse un Pedido en estado `recibido`, se emite un evento por WebSocket a la pantalla de cocina de ese restaurante
2. Pantalla de cocina (accesible vía navegador, sin instalar nada) muestra el ticket con items, cantidades y notas
3. Personal de cocina marca el pedido como `en_cocina` y luego `listo`

### 3. Entrega al cliente
- Si `tipo_entrega = mesa`: el mesero lleva el pedido a la mesa, se marca `entregado`
- Si `tipo_entrega = retiro`: al pasar a estado `listo`, el pedido queda visible como "listo para retirar" (por ejemplo en una pantalla del local con el número de orden). El mecanismo exacto de aviso al cliente está pendiente de definir — ver sección siguiente

## Pagos — detalle de integración Tilopay

- Cada restaurante se afilia a Tilopay de forma independiente y activa SINPE Móvil en su cuenta
- Sus credenciales (Llave API, Usuario API, Contraseña API) se guardan encriptadas en la tabla `Restaurante`
- El frontend carga el SDK JS de Tilopay y renderiza el formulario de pago embebido en la misma página de checkout (sin redirección)
- Apple Pay aparece automáticamente como opción si el navegador lo soporta (Safari/iOS) — no requiere lógica adicional
- Modo sandbox de Tilopay para pruebas antes de producción (tarjetas de prueba Visa/Mastercard/Amex)
- El dinero de cada venta llega directamente a la cuenta bancaria del restaurante — la plataforma nunca retiene fondos de terceros

## Notificación al cliente — pendiente de definir

Cómo se le avisa al cliente que su pedido de retiro está listo aún no está decidido. Una opción bajo consideración es una pantalla física en el local que muestre el número de orden cuando pasa a estado `listo` (similar a un letrero de "órdenes listas"). No implementar notificaciones por WhatsApp ni ningún canal externo en esta fase — dejar el campo `estado` del Pedido como la única fuente de verdad, de forma que cualquier mecanismo de aviso (pantalla, futura notificación, etc.) se pueda construir después leyendo ese estado sin cambiar el modelo de datos.

## Consideraciones de privacidad

- Costa Rica tiene la Ley 8968 (Ley de Protección de la Persona frente al Tratamiento de sus Datos Personales) — se requiere consentimiento explícito para guardar correo/teléfono con fines de análisis. Implementar checkbox de consentimiento visible y editable en el checkout (marcado por defecto, pero el cliente puede desmarcarlo)
- Los datos de Cliente y Pedido están scopeados por `restaurante_id` — cada restaurante solo accede a sus propios clientes, sin mezcla entre tenants

## Alcance del MVP (fase 1)

Incluir:
- [ ] CRUD de Restaurante, Categoría, Item (sin panel de administración elaborado, puede ser endpoints simples o un panel mínimo)
- [ ] Generación de QR por mesa (o "para retirar") vinculado a un restaurante
- [ ] Vista pública de menú por restaurante (React)
- [ ] Checkout embebido con Tilopay (tarjeta + SINPE + Apple Pay) y opción de "pagar en el restaurante"
- [ ] Modelo Cliente con consentimiento de datos
- [ ] Pantalla de cocina en tiempo real vía WebSocket (accesible desde cualquier navegador/tablet)
- [ ] Estados de pedido: recibido → en_cocina → listo → entregado (sin mecanismo de notificación externa aún — ver sección "Notificación al cliente — pendiente de definir")

Fuera del MVP (fases posteriores):
- Panel de administración completo para que cada restaurante gestione su menú sin tocar la base de datos directamente
- Onboarding self-service de nuevos restaurantes (hoy se puede crear manualmente en la base de datos)
- Impresora de tickets como alternativa a la pantalla de cocina
- Dashboard de analítica de clientes y ventas (fase futura, aprovechando el trasfondo de BI del propietario del proyecto)
- Reembolsos y contracargos
- Multi-idioma

## Notas para la implementación

- Priorizar que el checkout nunca redirija fuera de la página — es un requisito explícito del producto
- Todas las consultas y modelos deben incluir `restaurante_id` desde el día uno, incluso en el MVP, para no tener que migrar el aislamiento multi-tenant después
