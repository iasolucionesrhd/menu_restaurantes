# Estado del proyecto — 2026-07-22

Este archivo existe para poder retomar el trabajo desde cualquier máquina (basta con `git pull`). No es documentación permanente del proyecto, solo una foto del punto en que quedamos. Se reescribe cada vez que se actualiza — no es un changelog acumulado (para eso está `git log`).

## Último commit en `main`
```
50ce9ce Add cash register closing (cierre de caja) with per-method breakdown
```
Ese es el último commiteado y pusheado a GitHub. **Lo de esta sesión (fase 4.1: base del modo híbrido para eventos) todavía NO está commiteado** — cambios locales pendientes.

## Qué se hizo en esta sesión

Arrancó la **fase 4 (última del roadmap original): modo híbrido para eventos/ferias temporales**. El diseño se definió con el usuario a lo largo de varias rondas de preguntas, y quedó documentado en `C:\Users\roger\.claude\plans\misty-swimming-bee.md` (plan completo con las 6 sub-fases, actualizado varias veces conforme se refinó el diseño). Idea central, ya validada:

- Un **nodo local** (equipo portátil con su propia base de datos) es la única fuente de verdad durante el evento — cada evento es una **sucursal de tipo "evento"**, distinta de una sucursal física normal.
- La diferencia entre pedir con o sin internet no es "puede pedir o no" (ambos piden contra el mismo nodo) sino **qué métodos de pago están disponibles**: con conectividad real en el nodo, cualquier método; sin ella, solo efectivo. Además, cualquier sucursal (física o evento) podrá **desactivar el pago en línea por completo** desde el panel admin (para eventos que cobran con pulseras recargables u otro medio propio del organizador) — sub-fase 4.2, siguiente a implementar.
- Para llegar al menú **sin internet**: portal cautivo (misma tecnología del WiFi de aeropuertos/hoteles) — un QR de "unirse a esta red WiFi" hace que el celular, al conectarse, abra automáticamente el menú sin escanear nada más. Para llegar **con internet propio**, sin conectarse a esa red: un QR normal con una URL alcanzable vía un túnel (Cloudflare Tunnel) desde el nodo — ya no hace falta DNS dividido, esa idea se descartó a favor del portal cautivo (sub-fase 4.4).
- La sincronización con la nube **no es continua**: ocurre solo al cerrar caja en el nodo, subiendo ese cierre + sus pedidos en un solo envío (sub-fase 4.3, pendiente).

Esta sesión completó **solo la sub-fase 4.1 (la base)** — el resto del plan (4.2 a 4.6) quedó diseñado y documentado, pero sin implementar todavía:

**Modelo y migraciones.**
- Nuevo enum `OrigenPedido` (`nube` / `evento_local`) en `backend/app/enums.py`.
- `Pedido.origen` (nuevo, default `nube`) — distingue pedidos normales de los que llegarán importados desde un nodo de evento.
- `CierreCaja.origen` (nuevo, default `nube`) y `CierreCaja.sincronizado` (nuevo, default `true`) — en un nodo de evento, un cierre nace con `sincronizado=false` hasta que la sub-fase 4.2 lo suba con éxito a la nube.
- Migración `a2f9c7e1b3d4_add_origen_a_pedido_y_cierre_caja.py`, aplicada sobre la BD de desarrollo.

**Config dual-mode.**
- `MODO_NODO_EVENTO: bool = False` en `backend/app/config.py` — identifica que esta instancia del backend es un nodo de evento (usado por el script de importación; en la sub-fase 4.2 también decidirá a dónde y con qué token sincronizar).

**Manejo de conectividad en pagos y Google Sign-In (aplica igual en la nube que en un nodo evento).**
- `PaymentAdapterUnavailable` (nueva excepción en `services/payments/base.py`): `TilopayAdapter` la lanza cuando no puede contactar a Tilopay (antes cualquier falla de red producía un 500 genérico). `pedido_service.crear_pedido` ahora la traduce en un 503 con mensaje claro ("intenta pagar en efectivo") en vez de reventar.
- `GoogleAuthUnavailable` (nueva excepción en `services/google_auth.py`): se lanza específicamente cuando falla el contacto de red con Google (JWKS), separado de un token genuinamente inválido (que sigue rechazándose con 401 como antes). `crear_pedido` degrada a invitado en ese caso, en vez de fallar el pedido completo.

**Exportar/importar una sucursal para armar un nodo de evento.**
- `GET /api/admin/sucursales/exportar-datos-evento` (ADMIN, sobre la sucursal activa del token): devuelve una foto completa — menú (categorías/items/modificadores), mesas, staff (email + hash de contraseña, nunca se genera una nueva), y las credenciales Tilopay **ya descifradas por el ORM** (viajan en texto plano en esta respuesta admin-only sobre HTTPS).
- `backend/scripts/importar_evento.py` (nuevo, mismo patrón que `scripts/seed.py`): carga ese JSON en la BD vacía de un nodo nuevo, vía `docker compose exec backend python -m scripts.importar_evento datos.json`. Se niega a correr si `MODO_NODO_EVENTO` no está activo. Las credenciales Tilopay se vuelven a cifrar solas al asignarlas (gracias a `EncryptedString`, que usa el `FERNET_KEY` de la instancia que las procesa) — **no hace falta compartir la llave Fernet entre la nube y el nodo**.

**Verificación:** 90 tests de backend pasan (85 anteriores + 5 nuevos en `test_evento_export.py`, cubriendo export con credenciales/menú/mesas/staff, permisos de admin, import completo con verificación de contraseña y reconstrucción de menú, rechazo del import fuera de modo evento, y 503 claro cuando el proveedor de pago es inalcanzable). `tsc --noEmit` sin errores (se agregó `origen`/`sincronizado` a los tipos de `Pedido`/`CierreCaja` en el frontend). Probado a mano contra la BD de desarrollo real: login + export del restaurante demo devuelve el menú completo correctamente. Sin verificación de navegador esta sesión — no hay UI nueva todavía (llega en 4.3).

## Qué funciona ya verificado (de sesiones anteriores, sigue vigente)
- `docker-compose up` levanta db + backend + frontend. Migraciones + seed corren solos al levantar el backend.
- Flujo completo cliente: menú público (con modificadores) → carrito → checkout (invitado o Google) → confirmar pedido → cocina en tiempo real (WebSocket, con cronómetro) → recibido → en_cocina → listo → entregado (o cancelado).
- Cancelar pedido desde cocina (solo recibido/en_cocina, y solo si no quedó ya en un cierre de caja): admin sin restricción, cocina con PIN configurable. Genera nota de crédito interna si el pedido tenía factura, y devuelve el stock de ingredientes.
- Panel admin: login, categorías/items (precio inline, receta de ingredientes, modificadores), mesas + QR, ingredientes (inventario), personal (usuarios de staff), sucursales (multisucursal + ahora exportar datos de evento), seguridad (PIN).
- Pantallas de staff por rol: `/cocina` (admin/cocina), `/mesero` (admin/mesero), `/caja` (admin/cajero, con cierre de caja), `/admin` (admin). Redirección post-login automática según rol.
- Multisucursal: una cuenta admin puede crear y cambiar entre sucursales, cada una con menú/mesas/pedidos/cierres de caja totalmente independientes.
- Snapshot de precio inmutable en pedidos ya creados (incluye el precio de los modificadores elegidos).
- Consentimiento de datos (Ley 8968) + marketing. Captura de datos de factura en checkout (solo captura, no emite comprobante real).
- Sign-In con Google en checkout, aislado por tenant, con autorelleno de perfil en pedidos repetidos.

## Pendiente para la próxima sesión
1. **Sub-fase 4.2 — Tipo de sucursal + control de pago en línea** (siguiente a implementar, ya diseñada en el plan): `Restaurante.tipo_sucursal` (física/evento) y `Restaurante.acepta_pago_en_linea` (interruptor explícito del admin, independiente de la conectividad — pensado para pulseras recargables u otros medios de pago del organizador). Se valida en `crear_pedido` antes de intentar contactar al adaptador de pago; se expone en `GET /menu` para que el checkout oculte de entrada las opciones en línea si está apagado. Detalle completo en `C:\Users\roger\.claude\plans\misty-swimming-bee.md`.
2. **Sub-fase 4.3 — Sync al cerrar caja**: al ejecutar `cerrar_caja` en un nodo en modo evento, armar un paquete {cierre + pedidos incluidos} y subirlo a un endpoint nuevo en la nube (`importar-resultado-evento`), autenticado con un token de sincronización de larga duración generado una vez por un admin. Si no hay internet en ese momento, el cierre queda pendiente y se puede reintentar manualmente.
3. **Sub-fase 4.4 — Portal cautivo (sin internet) + QR con URL vía túnel (con internet propio)**: QR de unión a WiFi + configuración de portal cautivo en el nodo (ej. `nodogsplash`/`OpenNDS`), documentada como guía de despliegue; ajuste del checkout para intentar pago en línea y caer a efectivo con mensaje claro si el nodo no tiene conectividad en ese momento (el backend ya devuelve el 503 correcto, falta el manejo en el frontend).
4. **Sub-fase 4.5 — `docker-compose` del nodo local + guía de despliegue** (Postgres + backend + frontend en modo evento, notas de hostapd/dnsmasq/cloudflared/portal cautivo).
5. **Sub-fase 4.6 — Verificación end-to-end** simulando un evento completo.
6. No hay UI para cambiar/resetear la contraseña de un usuario de staff una vez creado — solo se puede borrar y recrear la cuenta. Ofrecido implementarlo, no confirmado todavía.
7. No hay UI para *ver* las notas de crédito generadas — evaluar cuando se aborde facturación electrónica real.
8. El usuario está evaluando **patentar el software** en su país — todavía no es una tarea de código.
9. Considerar si el mesero debería poder cobrar con otros métodos además de efectivo (hoy el pedido asistido siempre fuerza `efectivo_en_restaurante`).
10. Considerar un reporte/export (PDF o similar) de un cierre de caja — hoy solo se ve en pantalla.

No hay ningún bug conocido pendiente en este momento.

## Notas de seguridad
- `FERNET_KEY` NUNCA debe tener un valor por defecto hardcodeado en `backend/app/config.py`. Debe venir solo de `.env` (gitignored). **Un nodo de evento puede (y debe) tener su propio `FERNET_KEY` distinto al de la nube** — las credenciales exportadas se vuelven a cifrar solas con la llave del nodo al importarlas.
- `GOOGLE_CLIENT_ID` no es secreto pero vive solo en `.env`/`frontend/.env`, nunca hardcodeado.
- El PIN de cancelación de cocina y las contraseñas de usuario se guardan hasheadas (argon2) — nunca en texto plano ni reversibles. El export de datos de evento copia el hash tal cual, nunca genera una contraseña nueva.
- El endpoint de exportar datos de evento devuelve las credenciales Tilopay **en texto plano** en la respuesta (el ORM ya las descifró) — es admin-only y debe viajar siempre sobre HTTPS; el archivo JSON resultante debe tratarse como sensible (borrarlo del equipo usado para preparar el nodo una vez importado).
- Recordatorio: `docker-compose restart` NO relee `.env` — hace falta `docker-compose up -d --force-recreate <servicio>` cuando cambian variables de entorno.
