# Estado del proyecto — 2026-07-22

Este archivo existe para poder retomar el trabajo desde cualquier máquina (basta con `git pull`). No es documentación permanente del proyecto, solo una foto del punto en que quedamos. Se reescribe cada vez que se actualiza — no es un changelog acumulado (para eso está `git log`).

## Último commit en `main`
```
de66e44 Add mesero and cajero staff roles with dedicated screens
b255ec0 Add ingredient inventory, kitchen prep-time tracking, and product modifiers
```
`de66e44` está en GitHub. **Lo de esta sesión (multisucursal) todavía NO está commiteado** — cambios locales pendientes.

## Qué se hizo en esta sesión
Se completó la **fase 3 de la iniciativa de 4 partes**: modificadores → roles mesero/cajero → **multisucursal (esta sesión)** → modo offline para eventos (pendiente).

**Multisucursal.**
- Decisiones ya acordadas con el usuario: menú 100% independiente por sucursal, una sola cuenta admin con selector para cambiar entre sucursales.
- `Restaurante` ya era una sucursal independiente (menú/mesas/pedidos aislados) — no se tocó ese modelo. Se agregó tabla puente `usuario_restaurante` (qué sucursales adicionales puede ver un admin, más allá de su sucursal de origen).
- **Cambio de arquitectura clave:** `get_current_restaurante_id` (backend/app/deps.py) ahora lee la sucursal activa del **claim del JWT**, no de la fila fija `usuario.restaurante_id` en BD (antes sí lo hacía). Esto es 100% retrocompatible — para una cuenta de una sola sucursal el JWT siempre trae ese mismo id, así que nada cambia en la práctica. "Cambiar de sucursal" = pedir un token nuevo con otro `restaurante_id` (validado contra `usuario_restaurante` + la sucursal de origen), sin mutar ninguna fila.
- Nuevos endpoints: `GET /api/auth/mis-restaurantes` (lista sucursales accesibles), `POST /api/auth/cambiar-restaurante` (emite un token nuevo), `POST /api/admin/sucursales` (admin crea una sucursal nueva — nombre + slug — y queda vinculada automáticamente a su cuenta).
- Nuevo tab "Sucursales" en el panel admin: crea sucursales nuevas, lista las accesibles, marca cuál está "Activa", botón "Cambiar a esta" que pide el token nuevo y refresca todo el panel (todas las pestañas ya leen del token activo, no necesitaron cambios).
- El staff de cocina/mesero/cajero **no** tiene este selector — están fijos a la sucursal donde se creó su cuenta (`usuario.restaurante_id` en BD), tal como se acordó (el switcher es solo para admin).

**Verificación:** 79 tests de backend pasan (72 anteriores + 7 nuevos en `test_multisucursal.py`), `tsc --noEmit` sin errores. Probado en Docker de punta a punta: admin creó la sucursal "Pizzería Luna Cartago" desde el tab nuevo, cambió a ella, confirmó que el menú estaba vacío (aislado), creó una categoría de prueba ahí, volvió a "Pizzería Luna" y confirmó que sus categorías originales (Pizzas/Bebidas/Postres) seguían intactas sin ningún rastro de la prueba.

## Qué funciona ya verificado (de sesiones anteriores, sigue vigente)
- `docker-compose up` levanta db + backend + frontend. Migraciones + seed corren solos al levantar el backend.
- Flujo completo cliente: menú público (con modificadores) → carrito → checkout (invitado o Google) → confirmar pedido → cocina en tiempo real (WebSocket, con cronómetro) → recibido → en_cocina → listo → entregado (o cancelado).
- Cancelar pedido desde cocina (solo recibido/en_cocina): admin sin restricción, cocina con PIN configurable. Genera nota de crédito interna si el pedido tenía factura, y devuelve el stock de ingredientes.
- Panel admin: login, categorías/items (precio inline, receta de ingredientes, modificadores), mesas + QR, ingredientes (inventario), personal (usuarios de staff), **sucursales (multisucursal)**, seguridad (PIN).
- Pantallas de staff por rol: `/cocina` (admin/cocina), `/mesero` (admin/mesero), `/caja` (admin/cajero), `/admin` (admin). Redirección post-login automática según rol.
- Snapshot de precio inmutable en pedidos ya creados (incluye el precio de los modificadores elegidos).
- Consentimiento de datos (Ley 8968) + marketing. Captura de datos de factura en checkout (solo captura, no emite comprobante real).
- Sign-In con Google en checkout, aislado por tenant, con autorelleno de perfil en pedidos repetidos — confirmado funcionando con cuenta real.

## Pendiente para la próxima sesión
1. **Revisar y hacer commit + push** de los cambios de esta sesión (multisucursal) — están en el working tree, no en git todavía.
2. **Fase 4 (última de la iniciativa): modo offline híbrido para eventos/ferias temporales.** Idea validada con el usuario: un mini-servidor local que actúa de proxy a la nube cuando hay internet, y sirve el menú/pedidos localmente (solo invitado + efectivo) cuando no lo hay. Aún sin diseñar en detalle — falta decidir qué hardware/software se recomienda para el mini-servidor y cómo se implementa el "modo evento" (feature flag que oculta Google Sign-In/pago online cuando no hay salida a internet).
3. No hay UI para cambiar/resetear la contraseña de un usuario de staff una vez creado (el usuario preguntó por esto) — solo se puede borrar y recrear la cuenta. Ofrecido implementarlo, no confirmado todavía.
4. No hay UI para *ver* las notas de crédito generadas — evaluar cuando se aborde facturación electrónica real.
5. El usuario está evaluando **patentar el software** en su país — todavía no es una tarea de código.
6. Considerar si el mesero debería poder cobrar con otros métodos además de efectivo (hoy el pedido asistido siempre fuerza `efectivo_en_restaurante`).

No hay ningún bug conocido pendiente en este momento.

## Notas de seguridad
- `FERNET_KEY` NUNCA debe tener un valor por defecto hardcodeado en `backend/app/config.py`. Debe venir solo de `.env` (gitignored).
- `GOOGLE_CLIENT_ID` no es secreto pero vive solo en `.env`/`frontend/.env`, nunca hardcodeado.
- El PIN de cancelación de cocina y las contraseñas de usuario se guardan hasheadas (argon2) — nunca en texto plano ni reversibles.
- Recordatorio: `docker-compose restart` NO relee `.env` — hace falta `docker-compose up -d --force-recreate <servicio>` cuando cambian variables de entorno.
