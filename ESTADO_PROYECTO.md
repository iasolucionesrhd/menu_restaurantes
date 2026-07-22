# Estado del proyecto — 2026-07-21

Este archivo existe para poder retomar el trabajo desde cualquier máquina (basta con `git pull`). No es documentación permanente del proyecto, solo una foto del punto en que quedamos. Se reescribe cada vez que se actualiza — no es un changelog acumulado (para eso está `git log`).

## Último commit en `main`
```
c9bf2ef Rewrite ESTADO_PROYECTO.md as a clean current-state snapshot
5fa9e56 Add Google Sign-In, marketing consent, and digital invoice capture to checkout
```
Todo lo anterior ya está en GitHub. **Lo de esta sesión (cancelación de pedidos + nota de crédito) todavía NO está commiteado** — son cambios locales pendientes de revisar/commitear.

## Qué se hizo en esta sesión
- Se sincronizó la carpeta local (estaba 4 commits detrás de `origin/main`).
- Se levantó `docker-compose` y se verificó el flujo completo en el navegador (menú → carrito → checkout → cocina), incluyendo el botón de Google Sign-In (ya con `GOOGLE_CLIENT_ID` configurado en `.env`/`frontend/.env`).
- **Nueva feature: cancelar pedido desde cocina.**
  - Cancelable solo en estados `recibido` y `en_cocina` (no en `listo`, ya se asume preparado). `TRANSICIONES_ESTADO_PEDIDO` en `backend/app/enums.py` ajustado para reflejar esto.
  - Admin cancela sin restricciones. Cocina necesita un **código de cancelación (PIN)** configurable por el admin desde el nuevo tab "Seguridad" del panel admin (`PATCH /api/admin/restaurante` con `pin_cancelacion`, se guarda hasheado con argon2 igual que las contraseñas — nunca en texto plano).
  - Si cocina intenta cancelar sin que el admin haya configurado un PIN → 400. PIN incorrecto → 401.
  - Al cancelar un pedido con `requiere_factura=true` se genera un registro interno en la tabla nueva `nota_credito` (pedido_id, monto, motivo, fecha). Es un **stub**: no genera XML ni se envía a Hacienda, mismo alcance que la captura de datos de factura hoy.
  - Migración: `7d6468a2718c_add_cancelacion_pin_y_nota_credito.py` (agrega `restaurante.pin_cancelacion_hash` y la tabla `nota_credito`). Ya aplicada en la base de datos local.
  - 7 tests nuevos en `backend/tests/test_cancelacion_pedido.py`. Los 48 tests de backend pasan (41 anteriores + 7 nuevos).
  - Verificado manualmente en Docker real: admin configuró PIN "4321" para pizzeria-luna, cocina no pudo cancelar con PIN incorrecto, sí pudo con el correcto, el pedido desapareció del tablero en tiempo real (WebSocket), y al cancelar un pedido facturado se creó la nota de crédito con el monto correcto.

## Qué funciona ya verificado (de sesiones anteriores, sigue vigente)
- `docker-compose up` levanta db + backend + frontend. Migraciones + seed corren solos al levantar el backend.
- Flujo completo cliente: menú público → carrito → checkout (invitado o Google) → confirmar pedido → pantalla de cocina en tiempo real (WebSocket) → transición de estados recibido → en_cocina → listo → entregado (o cancelado, ver arriba).
- Panel admin: login, gestionar categorías/items (incluye editar precio inline), mesas + generación de QR, y ahora seguridad (PIN de cancelación).
- `/cocina` y `/admin` redirigen a `/login` sin sesión; un rol sin permiso ve una página 403 propia.
- Snapshot de precio inmutable en pedidos ya creados.
- Consentimiento de datos (Ley 8968) + marketing.
- Captura de datos de factura en checkout (solo captura, no emite comprobante real).
- Sign-In con Google en checkout, aislado por tenant, con autorelleno de perfil en pedidos repetidos.

## Pendiente para la próxima sesión
1. **Revisar y hacer commit** de los cambios de esta sesión (cancelación + nota de crédito) — están en el working tree, no en git todavía.
2. Sigue pendiente de otra sesión: confirmar con una cuenta real de Google que el autorelleno de perfil (nombre/correo/teléfono + datos de factura) funciona en un segundo pedido — nunca se probó de punta a punta con una cuenta real dentro de una sesión de Claude Code.
3. No hay UI para *ver* las notas de crédito generadas (solo quedan en la tabla `nota_credito`) — evaluar si hace falta una pantalla de reportes cuando se decida abordar facturación electrónica real.

No hay ningún bug conocido pendiente en este momento.

## Notas de seguridad
- `FERNET_KEY` NUNCA debe tener un valor por defecto hardcodeado en `backend/app/config.py`. Debe venir solo de `.env` (gitignored).
- `GOOGLE_CLIENT_ID` no es secreto pero vive solo en `.env`/`frontend/.env`, nunca hardcodeado.
- El PIN de cancelación de cocina se guarda hasheado (argon2, mismo esquema que las contraseñas de usuario) — nunca en texto plano ni reversible.
- Recordatorio: `docker-compose restart` NO relee `.env` — hace falta `docker-compose up -d --force-recreate <servicio>` cuando cambian variables de entorno.
