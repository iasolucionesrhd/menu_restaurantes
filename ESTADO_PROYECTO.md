# Estado del proyecto — 2026-07-08

Este archivo existe para poder retomar el trabajo desde cualquier máquina (basta con `git pull`). No es documentación permanente del proyecto, solo una foto del punto en que quedamos.

## Último commit en `main`
```
6fe5fd4 Show payment method badge on kitchen tickets
377ce60 Fix infinite render loop in CartContext blocking navigation to checkout
53f340f Drop unnecessary refresh after estado transition, fixes MissingGreenlet
d6bad05 Use NullPool for the test engine to avoid cross-event-loop connections
2838ead Fix pytest-asyncio ScopeMismatch on session-scoped schema fixture
```
Todo lo anterior ya está en GitHub (`https://github.com/iasolucionesrhd/menu_restaurantes.git`). Los 26 tests de backend pasan.

## Qué funciona ya verificado
- `docker-compose up` levanta db + backend + frontend en el portátil.
- Migraciones + seed corren solos al levantar el backend.
- Login, menú público, carrito, pantalla de cocina (con hidratación REST + WebSocket) funcionan.
- Ticket de cocina ahora muestra badge de método de pago: 💵 amarillo "Cobrar en mesa" para efectivo, 💳 verde "Pagado (tarjeta/SINPE/Apple Pay)" para pagos ya cobrados online.

## Resuelto
**Bug de checkout** (clic en "Ir a checkout" no navegaba sin refrescar): verificado el 2026-07-14 levantando el entorno completo con `docker-compose up` en el portátil — se agregó un item al carrito y se hizo clic en "Ir a checkout", navegó correctamente sin necesidad de refresco. Se confirma que el fix del commit `377ce60` (memoización en `CartContext`) resolvió el problema; el síntoma anterior era efectivamente HMR de Vite con estado viejo, no un bug de código.

## Hito 12 — verificación manual completa (2026-07-14)
Se levantó el entorno con `docker-compose up` y se verificó todo lo pendiente:
- ✅ Ticket llega en tiempo real por WebSocket a `/cocina` sin refrescar, al crear un pedido nuevo desde el menú público.
- ✅ Transición de estados recibido → en_cocina → listo → entregado funciona en la UI de cocina.
- ✅ `/cocina` y `/admin` redirigen a `/login` sin sesión.
- ⚠️→✅ **Rol `cocina` en rutas solo-admin**: la API ya devolvía `403` correctamente, pero el frontend redirigía a `/login` igual que sin sesión. Arreglado, ver sección "Arreglos aplicados" abajo.
- ✅ Snapshot de precio: se cambió el precio de "Pizza Margarita" de 8.50 a 12.00 vía API (`PATCH /api/admin/items/1`) y el pedido ya creado conservó `precio_unitario: 8.50`. Precio restaurado a 8.50 después de la prueba.
- ✅ Generación de QR de mesa desde el admin funciona (botón "Ver QR" renderiza la imagen).
- ⚠️→✅ Nota menor: el panel admin no tenía UI para editar el precio de un item. Arreglado, ver sección "Arreglos aplicados" abajo.

Con esto el hito 12 queda verificado.

## Arreglos aplicados (2026-07-14, sesión de tarde)
- **Edición de precio en admin**: `frontend/src/pages/staff/AdminPanel.tsx` — la celda de precio en la tabla de items ahora es un `<input type="number">` que hace `PATCH /api/admin/items/{id}` al perder el foco (`onBlur`), solo si el valor cambió.
- **403 diferenciado de "sin sesión"**: nuevo `frontend/src/pages/ForbiddenPage.tsx`; `RequireAuth.tsx` ahora renderiza esa página cuando hay sesión pero el rol no coincide, en vez de redirigir a `/login` (que queda solo para el caso sin sesión).
- **Bug de React encontrado de paso**: `LoginPage.tsx` llamaba `navigate()` directamente en el cuerpo del componente (durante el render) para redirigir si ya había sesión — antipatrón que React marca con el warning "Cannot update a component while rendering a different component". Se cambió al patrón declarativo `return <Navigate .../>` (igual que `RequireAuth`).
- **Causa raíz de por qué no se veía el fix al principio**: Vite dentro del contenedor Docker en Windows no detectaba los cambios de archivo hechos desde el host (problema conocido de bind mounts + inotify en Windows). Se agregó `server.watch.usePolling: true` en `frontend/vite.config.ts` — sin esto, cualquier edición de código durante desarrollo con Docker en este portátil requeriría reiniciar el contenedor manualmente para verse reflejada.

## Feature nueva: Sign-In con Google en checkout (2026-07-14)
Implementado según el plan en `C:\Users\roger\.claude\plans\elegant-frolicking-reddy.md` (uno de los planes locales de Claude Code, no versionado en el repo). Resumen:
- `Cliente` tiene ahora `google_sub` (nullable) + unique compuesto `(restaurante_id, google_sub)` — nunca unique de `google_sub` solo, para que la misma cuenta de Google en dos restaurantes distintos genere dos `Cliente` completamente separados (requisito explícito: nada se mezcla entre tenants). Migración `579a2ecd1052_add_google_sub_to_cliente.py`, probada con upgrade/downgrade/upgrade contra Postgres.
- Verificación del ID token de Google en `backend/app/services/google_auth.py`, usando `pyjwt` (ya era dependencia del proyecto para el JWT de staff, verificación completamente separada) — **no se agregaron dependencias nuevas** al `requirements.txt`.
- `crear_pedido` en `pedido_service.py`: si viene `google_id_token`, busca o crea el `Cliente` por `(restaurante_id, sub)`; si no viene, comportamiento de invitado sin cambios. El correo se toma del token verificado, nunca del JSON del cliente (evita que alguien mande un token válido con un correo ajeno).
- Un solo `GOOGLE_CLIENT_ID` para toda la plataforma (decisión del usuario, no uno por restaurante como Tilopay) — variable opcional, sin configurar el feature simplemente no aparece (botón oculto en frontend, 400 explícito en backend si igual llega un token).
- 8 tests nuevos en `backend/tests/test_google_signin.py`, incluyendo el caso central de aislamiento entre tenants (mismo `sub` en dos restaurantes → dos `Cliente` distintos). Los 34 tests del backend pasan.
- **Sin verificar todavía**: el flujo real del botón de Google en el navegador — no se configuró un Client ID real de Google Cloud en esta sesión, así que solo se probó que (a) el checkout de invitado sigue funcionando exactamente igual sin el env var configurado, y (b) la lógica de backend vía tests con la verificación mockeada. Falta el paso 3 de "Sign-In con Google" en el `README.md` (crear el Client ID real) para probar el flujo end-to-end con una cuenta de Google real.

## Feature nueva: checkbox de marketing + factura digital en checkout (2026-07-15)
- **Consentimiento de marketing separado** del consentimiento de datos de contacto (Ley 8968 exige consentimientos distintos para finalidades distintas) — `Cliente.consentimiento_marketing`, sin premarcar, checkbox propio en `CustomerForm.tsx`.
- **Checkbox "Necesito factura"** despliega un formulario con nombre/razón social, cédula, correo, teléfono, ubicación y código de actividad económica (alcance confirmado: solo se guarda el dato, no se genera ni envía ningún comprobante electrónico real a Hacienda todavía — eso queda para cuando se decida si va directo a Hacienda o vía el ERP que use cada restaurante).
- Los datos de facturación se guardan en dos lugares con propósitos distintos: `Cliente.factura_*` es el "perfil actual" (se sobrescribe cada vez, sirve para autorellenar), `Pedido.factura_*` + `requiere_factura` es un snapshot inmutable por pedido (mismo patrón que el snapshot de precio) — así una corrección posterior de cédula no cambia retroactivamente pedidos ya hechos.
- **Autorelleno solo para clientes con Google Sign-In**: nuevo endpoint `POST /api/public/{slug}/cliente/perfil` (`backend/app/routers/clientes_publico.py`) que, dado un ID token de Google verificado, devuelve el perfil guardado (contacto + factura) de ese cliente en ese restaurante específico — aislado por tenant igual que el resto. El frontend lo llama automáticamente justo después de que el botón de Google resuelve.
- 7 tests nuevos en `backend/tests/test_facturacion.py`. Los 41 tests del backend pasan. Migración `51d3dccca84a` probada con upgrade/downgrade/upgrade.
- De paso se corrigió un bug preexistente en `frontend/src/api/client.ts`: los errores 422 de FastAPI traen `detail` como una lista de objetos, no un string — se mostraba como `[object Object]`. Ahora se arma un mensaje legible.
- **Sin verificar todavía**: el flujo real de autorelleno con una cuenta de Google real (requiere el Client ID configurado y hacer un segundo pedido con la misma cuenta) — no se pudo simular el popup real de Google desde el navegador de esta sesión. Sí se verificó por tests automatizados (backend) y manualmente el checkout de invitado con factura completo end-to-end.

## Notas de seguridad
- `FERNET_KEY` NUNCA debe tener un valor por defecto hardcodeado en `backend/app/config.py` (ya pasó una vez y bloqueó el push). Debe venir solo de `.env` (gitignored).
