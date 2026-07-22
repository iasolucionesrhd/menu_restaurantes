# Estado del proyecto — 2026-07-22

Este archivo existe para poder retomar el trabajo desde cualquier máquina (basta con `git pull`). No es documentación permanente del proyecto, solo una foto del punto en que quedamos. Se reescribe cada vez que se actualiza — no es un changelog acumulado (para eso está `git log`).

## Último commit en `main`
```
b255ec0 Add ingredient inventory, kitchen prep-time tracking, and product modifiers
f2ecdd2 Add order cancellation from kitchen with PIN gate and credit-note stub
```
`b255ec0` está en GitHub. **Lo de esta sesión (roles mesero/cajero) todavía NO está commiteado** — cambios locales pendientes.

## Qué se hizo en esta sesión
Se completó la **fase 2 de la iniciativa de 4 partes**: modificadores (fase 1, ya en main) → **roles mesero/cajero (esta sesión)** → multisucursal → modo offline para eventos.

**Roles: mesero y cajero.**
- `RolUsuario` ahora incluye `mesero` y `cajero` (además de `admin`/`cocina`). Migración `938888aab4f2` agrega los valores al enum nativo de Postgres (`ALTER TYPE ... ADD VALUE`) y la columna `pedido.pagado`.
- **Prerrequisito que no existía y había que resolver primero:** no había ninguna forma de crear usuarios de staff desde la app (solo el script de seed). Se agregó tab "Personal" en el panel admin + `POST/GET/DELETE /api/admin/usuarios` para que el admin pueda dar de alta mesero/cajero/cocina/otro admin con email+contraseña.
- **Mesero** (pantalla nueva `/mesero`): toma pedidos asistidos (elige mesa + nombre del cliente + items con modificadores, vía `POST /api/staff/pedidos/asistido`, siempre `efectivo_en_restaurante`) y marca "entregado" cuando el pedido está listo. No puede cancelar ni avanzar a en_cocina/listo (403 si lo intenta — verificado con test).
- **Cajero** (pantalla nueva `/caja`): ve pedidos pendientes de cobro (`pagado=false`) y los marca cobrados (`PATCH /api/staff/pedidos/{id}/pagado`), más un resumen "Cobrado hoy" (`GET /api/staff/pedidos/resumen-caja`). No ve cocina ni puede cambiar el estado del pedido.
- **Campo `pedido.pagado`** nuevo: tarjeta/sinpe/apple_pay quedan `pagado=true` automáticamente al crearse (ya se verificó el pago online); efectivo_en_restaurante empieza en `false` hasta que cajero lo cobra. El ticket de cocina ahora muestra "✅ Pagado" en vez de "💵 Cobrar en mesa" una vez cobrado.
- El WebSocket de cocina (`/api/ws/cocina/{slug}`) ahora acepta también conexiones de mesero y cajero, para que sus pantallas se actualicen en vivo igual que cocina.
- Permisos por transición de estado (tabla `ROLES_POR_TRANSICION` en `backend/app/routers/pedidos.py`): en_cocina/listo → admin/cocina; entregado → admin/cocina/mesero; cancelado → admin/cocina (con PIN si es cocina, igual que antes). Cajero no aparece en ninguna transición de estado, solo en `pagado`.

**Verificación:** 72 tests de backend pasan (62 anteriores + 10 nuevos en `test_roles_mesero_cajero.py`), `tsc --noEmit` sin errores. Probado en Docker de punta a punta: admin creó usuarios mesero/cajero desde el tab Personal → mesero tomó un pedido asistido con modificadores → admin lo pasó a en_cocina/listo → mesero lo marcó entregado (y no pudo hacer la transición a en_cocina, 403 confirmado también por test) → cajero lo vio en pendientes de cobro, lo marcó cobrado, y "Cobrado hoy" se actualizó correctamente.

## Qué funciona ya verificado (de sesiones anteriores, sigue vigente)
- `docker-compose up` levanta db + backend + frontend. Migraciones + seed corren solos al levantar el backend.
- Flujo completo cliente: menú público (con modificadores) → carrito → checkout (invitado o Google) → confirmar pedido → cocina en tiempo real (WebSocket, con cronómetro) → recibido → en_cocina → listo → entregado (o cancelado).
- Cancelar pedido desde cocina (solo recibido/en_cocina): admin sin restricción, cocina con PIN configurable en tab "Seguridad". Genera nota de crédito interna si el pedido tenía factura, y devuelve el stock de ingredientes.
- Panel admin: login, categorías/items (precio inline, receta de ingredientes, modificadores), mesas + QR, ingredientes (inventario), **personal (usuarios de staff)**, seguridad (PIN).
- Pantallas de staff por rol: `/cocina` (admin/cocina), `/mesero` (admin/mesero), `/caja` (admin/cajero), `/admin` (admin). Redirección post-login automática según rol (`LoginPage.tsx`).
- Snapshot de precio inmutable en pedidos ya creados (incluye el precio de los modificadores elegidos).
- Consentimiento de datos (Ley 8968) + marketing. Captura de datos de factura en checkout (solo captura, no emite comprobante real).
- Sign-In con Google en checkout, aislado por tenant, con autorelleno de perfil en pedidos repetidos — confirmado funcionando con cuenta real.

## Pendiente para la próxima sesión
1. **Revisar y hacer commit + push** de los cambios de esta sesión (roles mesero/cajero) — están en el working tree, no en git todavía.
2. Seguir con la iniciativa de 4 partes:
   - **Fase 3 (siguiente): multisucursal.** Decisiones ya tomadas con el usuario: menú 100% independiente por sucursal, pero **una sola cuenta admin con selector de sucursal** (implica un nivel de tenant nuevo por encima de `Restaurante`, o un modelo "Usuario puede pertenecer a N restaurantes"). Aún sin diseñar el esquema de datos exacto.
   - Fase 4: modo offline híbrido — para **eventos/ferias temporales** (no la sede fija). Idea validada: un mini-servidor local que actúa de proxy a la nube cuando hay internet, y sirve el menú/pedidos localmente (solo invitado + efectivo) cuando no lo hay.
3. Sigue pendiente: no hay UI para *ver* las notas de crédito generadas — evaluar cuando se aborde facturación electrónica real.
4. El usuario está evaluando **patentar el software** en su país — todavía no es una tarea de código.
5. Considerar si el mesero debería poder ver/cobrar pagos con otros métodos además de efectivo (hoy el pedido asistido siempre fuerza `efectivo_en_restaurante`).

No hay ningún bug conocido pendiente en este momento.

## Notas de seguridad
- `FERNET_KEY` NUNCA debe tener un valor por defecto hardcodeado en `backend/app/config.py`. Debe venir solo de `.env` (gitignored).
- `GOOGLE_CLIENT_ID` no es secreto pero vive solo en `.env`/`frontend/.env`, nunca hardcodeado.
- El PIN de cancelación de cocina se guarda hasheado (argon2, mismo esquema que las contraseñas de usuario) — nunca en texto plano ni reversible.
- Recordatorio: `docker-compose restart` NO relee `.env` — hace falta `docker-compose up -d --force-recreate <servicio>` cuando cambian variables de entorno.
