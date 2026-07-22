# Estado del proyecto — 2026-07-22

Este archivo existe para poder retomar el trabajo desde cualquier máquina (basta con `git pull`). No es documentación permanente del proyecto, solo una foto del punto en que quedamos. Se reescribe cada vez que se actualiza — no es un changelog acumulado (para eso está `git log`).

## Último commit en `main`
```
9dd20f9 Add multi-branch support with an admin sucursal switcher
de66e44 Add mesero and cajero staff roles with dedicated screens
```
`9dd20f9` está en GitHub. **Lo de esta sesión (cierre de caja) todavía NO está commiteado** — cambios locales pendientes.

## Qué se hizo en esta sesión
Se agregó **cierre de caja**, a pedido del usuario (fuera de las 4 fases originales, pero directamente relacionado con el rol cajero de la fase 2).

**Cierre de caja.**
- Nueva tabla `cierre_caja`: snapshot inmutable de lo cobrado desde el cierre anterior (o desde el primer pedido, si es el primero) hasta el momento de cerrar. Desglosado por método de pago (efectivo/tarjeta/sinpe/apple_pay), con total y cantidad de cada uno, más el total general.
- `Pedido.cierre_caja_id` (nuevo, nullable): al cerrar, todos los pedidos elegibles (pagado=true, no cancelados, sin cierre previo) quedan marcados con el cierre que los incluyó. **Un pedido ya incluido en un cierre no se puede cancelar** (400 si se intenta) — protege el historial contable de cambios después de cuadrar la caja.
- `resumen-caja` cambió de "cobrado hoy" (por fecha calendario) a **"cobrado en el período actual"** (desde el último cierre) — más correcto para turnos que cruzan medianoche o cierres varias veces al día. Los nombres de campo cambiaron: `cobrado_periodo_actual` / `pedidos_periodo_actual` (antes `cobrado_hoy` / `pedidos_cobrados_hoy`).
- Nuevos endpoints: `POST /api/staff/pedidos/cierres-caja` (cierra y devuelve el desglose), `GET /api/staff/pedidos/cierres-caja` (historial). Permisos: admin y cajero (igual que marcar pagado).
- Pantalla `/caja`: botón "Cerrar caja" (deshabilitado si no hay nada pendiente) que muestra el desglose recién cerrado, y un historial colapsable de cierres anteriores.

**Verificación:** 85 tests de backend pasan (79 anteriores + 6 nuevos en `test_cierre_caja.py`), `tsc --noEmit` sin errores. Probado en Docker de punta a punta: pedidos en efectivo + tarjeta + SINPE → cerrar caja → desglose correcto por método → "por cerrar" vuelve a ₡0 → el historial muestra el cierre con fecha y montos.

Nota técnica: durante la verificación manual, el clic simulado del navegador controlado no disparaba el botón "Cerrar caja" (aunque no estaba deshabilitado) — se confirmó con un `.click()` directo por JS que el botón y el endpoint funcionan bien; parece una particularidad puntual de esa herramienta de automatización, no un bug del código.

## Qué funciona ya verificado (de sesiones anteriores, sigue vigente)
- `docker-compose up` levanta db + backend + frontend. Migraciones + seed corren solos al levantar el backend.
- Flujo completo cliente: menú público (con modificadores) → carrito → checkout (invitado o Google) → confirmar pedido → cocina en tiempo real (WebSocket, con cronómetro) → recibido → en_cocina → listo → entregado (o cancelado).
- Cancelar pedido desde cocina (solo recibido/en_cocina, y solo si no quedó ya en un cierre de caja): admin sin restricción, cocina con PIN configurable. Genera nota de crédito interna si el pedido tenía factura, y devuelve el stock de ingredientes.
- Panel admin: login, categorías/items (precio inline, receta de ingredientes, modificadores), mesas + QR, ingredientes (inventario), personal (usuarios de staff), sucursales (multisucursal), seguridad (PIN).
- Pantallas de staff por rol: `/cocina` (admin/cocina), `/mesero` (admin/mesero), `/caja` (admin/cajero, ahora con cierre de caja), `/admin` (admin). Redirección post-login automática según rol.
- Multisucursal: una cuenta admin puede crear y cambiar entre sucursales, cada una con menú/mesas/pedidos/**cierres de caja** totalmente independientes.
- Snapshot de precio inmutable en pedidos ya creados (incluye el precio de los modificadores elegidos).
- Consentimiento de datos (Ley 8968) + marketing. Captura de datos de factura en checkout (solo captura, no emite comprobante real).
- Sign-In con Google en checkout, aislado por tenant, con autorelleno de perfil en pedidos repetidos — confirmado funcionando con cuenta real.

## Pendiente para la próxima sesión
1. **Revisar y hacer commit + push** de los cambios de esta sesión (cierre de caja) — están en el working tree, no en git todavía.
2. **Fase 4 (última de la iniciativa original): modo offline híbrido para eventos/ferias temporales.** Idea validada con el usuario: un mini-servidor local que actúa de proxy a la nube cuando hay internet, y sirve el menú/pedidos localmente (solo invitado + efectivo) cuando no lo hay. Aún sin diseñar en detalle.
3. No hay UI para cambiar/resetear la contraseña de un usuario de staff una vez creado — solo se puede borrar y recrear la cuenta. Ofrecido implementarlo, no confirmado todavía.
4. No hay UI para *ver* las notas de crédito generadas — evaluar cuando se aborde facturación electrónica real.
5. El usuario está evaluando **patentar el software** en su país — todavía no es una tarea de código.
6. Considerar si el mesero debería poder cobrar con otros métodos además de efectivo (hoy el pedido asistido siempre fuerza `efectivo_en_restaurante`).
7. Considerar si hace falta un reporte/export (PDF o similar) de un cierre de caja para entregarlo físicamente o archivarlo — hoy solo se ve en pantalla.

No hay ningún bug conocido pendiente en este momento.

## Notas de seguridad
- `FERNET_KEY` NUNCA debe tener un valor por defecto hardcodeado en `backend/app/config.py`. Debe venir solo de `.env` (gitignored).
- `GOOGLE_CLIENT_ID` no es secreto pero vive solo en `.env`/`frontend/.env`, nunca hardcodeado.
- El PIN de cancelación de cocina y las contraseñas de usuario se guardan hasheadas (argon2) — nunca en texto plano ni reversibles.
- Recordatorio: `docker-compose restart` NO relee `.env` — hace falta `docker-compose up -d --force-recreate <servicio>` cuando cambian variables de entorno.
