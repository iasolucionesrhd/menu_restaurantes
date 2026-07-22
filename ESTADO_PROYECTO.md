# Estado del proyecto — 2026-07-21

Este archivo existe para poder retomar el trabajo desde cualquier máquina (basta con `git pull`). No es documentación permanente del proyecto, solo una foto del punto en que quedamos. Se reescribe cada vez que se actualiza — no es un changelog acumulado (para eso está `git log`).

## Último commit en `main`
```
f2ecdd2 Add order cancellation from kitchen with PIN gate and credit-note stub
c9bf2ef Rewrite ESTADO_PROYECTO.md as a clean current-state snapshot
```
Todo lo anterior ya está en GitHub. **Lo de esta sesión (ingredientes/receta + control de inventario + tiempos de cocina) todavía NO está commiteado** — son cambios locales pendientes de revisar/commitear.

## Qué se hizo en esta sesión
**Nueva feature 1: receta de ingredientes + control de inventario por item.**
- Tabla `ingrediente` (nombre, unidad, stock_actual, stock_minimo) y tabla `item_ingrediente` (receta: cuánto de cada ingrediente requiere una unidad de un item). Migración `3fa6a3a36f72_add_ingredientes_receta_y_tiempos_de_.py`.
- CRUD de ingredientes en `/api/admin/ingredientes` (nuevo router `backend/app/routers/ingredientes.py`) y tab "Ingredientes" en el panel admin, con alerta visual (`stock_bajo`, fila resaltada) cuando `stock_actual <= stock_minimo`.
- Editor de receta por item: botón "Definir receta"/"Receta (n)" en el tab Items del panel admin, endpoint `PUT /api/admin/items/{id}/ingredientes` que reemplaza la lista completa de la receta.
- Al confirmar un pedido, se descuenta `cantidad_requerida × cantidad_pedida` de cada ingrediente de la receta (`descontar_stock` en `pedido_service.py`). **No bloquea la venta** aunque falte stock — el stock puede quedar negativo, solo se alerta visualmente en el admin (decisión explícita del usuario).
- Al **cancelar** un pedido (recibido/en_cocina), el stock descontado se devuelve automáticamente (`restaurar_stock`) — mismo principio que la nota de crédito: cancelar revierte el pedido por completo.
- Los updates de stock usan `UPDATE ... SET stock_actual = stock_actual - :delta` (atómico a nivel de fila), no read-then-write, para evitar carreras entre pedidos concurrentes.

**Nueva feature 2: tracking de tiempos de cocina, con cronómetro en vivo.**
- `Pedido` ahora tiene `en_cocina_en` y `listo_en` (además de `creado_en` que ya existía pero no se exponía en `PedidoOut` — se agregó). Se llenan automáticamente en `transicionar_estado` al entrar a cada estado.
- Cada ticket en `/cocina` muestra un cronómetro en vivo (`⏱️ X min esperando / en cocina / listo`) que se actualiza cada 15s, calculado desde el timestamp del estado actual del pedido.
- El mensaje WebSocket `estado_actualizado` ahora manda el `PedidoOut` completo (antes solo mandaba `pedido_id` + `estado`) para que todos los clientes conectados vean el mismo timestamp, no uno calculado localmente.

**Verificación:**
- 56 tests de backend pasan (48 anteriores + 8 nuevos: `test_ingredientes_stock.py`, `test_pedido_tiempos_cocina.py`).
- `tsc --noEmit` sin errores en el frontend.
- Probado en vivo en Docker: se creó el ingrediente "Mozzarella" (stock 2000g), se le definió receta a "Pizza Margarita" (200g), se hizo un pedido → stock bajó a 1800g, se pasó el pedido a "en cocina" → cronómetro cambió de "esperando" a "en cocina" en tiempo real, se canceló → stock volvió a 2000g.
- Nota al margen (no relacionado a esta feature): varios items demo (Pizza Margarita, Pepperoni, Hawaiana, Refresco natural) estaban marcados `disponible=false` en la base de datos local desde antes de esta sesión — se reactivó Pizza Margarita manualmente para poder probar. Si en la otra máquina el menú público se ve con pocos items, revisar el checkbox "Disponible" en el tab Items del admin.

## Qué funciona ya verificado (de sesiones anteriores, sigue vigente)
- `docker-compose up` levanta db + backend + frontend. Migraciones + seed corren solos al levantar el backend.
- Flujo completo cliente: menú público → carrito → checkout (invitado o Google) → confirmar pedido → pantalla de cocina en tiempo real (WebSocket) → transición de estados recibido → en_cocina → listo → entregado (o cancelado).
- Cancelar pedido desde cocina (solo recibido/en_cocina): admin sin restricción, cocina con PIN configurable en tab "Seguridad". Genera nota de crédito interna si el pedido tenía factura.
- Panel admin: login, categorías/items (precio inline, receta de ingredientes), mesas + QR, ingredientes (inventario), seguridad (PIN), roles con página 403 propia.
- Snapshot de precio inmutable en pedidos ya creados.
- Consentimiento de datos (Ley 8968) + marketing.
- Captura de datos de factura en checkout (solo captura, no emite comprobante real).
- Sign-In con Google en checkout, aislado por tenant, con autorelleno de perfil en pedidos repetidos.

## Pendiente para la próxima sesión
1. **Revisar y hacer commit** de los cambios de esta sesión (ingredientes/inventario + tiempos de cocina) — están en el working tree, no en git todavía.
2. Sigue pendiente de otra sesión: confirmar con una cuenta real de Google que el autorelleno de perfil funciona en un segundo pedido.
3. No hay UI para *ver* las notas de crédito generadas — evaluar cuando se aborde facturación electrónica real.
4. Considerar si el inventario necesita alguna forma de "reponer stock" en bloque (hoy solo se edita a mano el campo stock_actual desde el tab Ingredientes) si el negocio lo pide.

No hay ningún bug conocido pendiente en este momento.

## Notas de seguridad
- `FERNET_KEY` NUNCA debe tener un valor por defecto hardcodeado en `backend/app/config.py`. Debe venir solo de `.env` (gitignored).
- `GOOGLE_CLIENT_ID` no es secreto pero vive solo en `.env`/`frontend/.env`, nunca hardcodeado.
- El PIN de cancelación de cocina se guarda hasheado (argon2, mismo esquema que las contraseñas de usuario) — nunca en texto plano ni reversible.
- Recordatorio: `docker-compose restart` NO relee `.env` — hace falta `docker-compose up -d --force-recreate <servicio>` cuando cambian variables de entorno.
