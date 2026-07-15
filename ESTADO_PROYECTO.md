# Estado del proyecto — 2026-07-15

Este archivo existe para poder retomar el trabajo desde cualquier máquina (basta con `git pull`). No es documentación permanente del proyecto, solo una foto del punto en que quedamos. Se reescribe cada vez que se actualiza — no es un changelog acumulado (para eso está `git log`).

## Último commit en `main`
```
5fa9e56 Add Google Sign-In, marketing consent, and digital invoice capture to checkout
70fa77d Add project status doc for cross-machine continuity
6fe5fd4 Show payment method badge on kitchen tickets
```
Todo lo anterior ya está en GitHub (`https://github.com/iasolucionesrhd/menu_restaurantes.git`). Los 41 tests de backend pasan.

## Qué funciona ya verificado
- `docker-compose up` levanta db + backend + frontend. Migraciones + seed corren solos al levantar el backend.
- Flujo completo cliente: menú público → carrito → checkout (invitado) → confirmar pedido → pantalla de cocina en tiempo real (WebSocket) → transición de estados recibido → en_cocina → listo → entregado.
- Panel admin: login, gestionar categorías/items (incluye editar precio inline), mesas + generación de QR.
- `/cocina` y `/admin` redirigen a `/login` sin sesión; un rol sin permiso (ej. cocina en `/admin`) ve una página 403 propia, no lo manda a `/login`.
- Snapshot de precio: si se cambia el precio de un item después, los pedidos ya creados conservan el precio original.
- Checkbox de consentimiento de datos (Ley 8968) + checkbox separado de marketing (sin premarcar).
- Checkbox "Necesito factura" en checkout: guarda nombre/cédula/correo/teléfono/dirección/actividad económica por pedido (snapshot inmutable) y en el perfil del `Cliente` (para autorelleno). Alcance: solo captura el dato, no genera ni envía comprobante electrónico real a Hacienda todavía.
- Sign-In con Google en checkout: token verificado en el backend (`pyjwt`, sin dependencias nuevas), un solo Client ID para toda la plataforma, aislado por tenant (mismo Google account en dos restaurantes = dos `Cliente` completamente separados, nunca se mezclan). Verificado con `docker-compose` real: el botón aparece, el login funciona, y el pedido se crea sin el error de configuración que hubo al principio (recordatorio: `docker-compose restart` NO relee `.env` — hace falta `docker-compose up -d --force-recreate <servicio>` cuando cambian variables de entorno).

## Pendiente para la próxima sesión
**El usuario va a probar mañana** el flujo completo con su propia cuenta de Google:
1. Pedir una vez marcando "Necesito factura" y llenando los datos.
2. Hacer un segundo pedido con la misma cuenta de Google (mismo restaurante) y confirmar que:
   - El formulario de contacto (nombre/correo/teléfono) aparece pre-llenado.
   - El checkbox de factura aparece marcado solo, con los datos de la vez anterior ya cargados.
3. Si algo no autorellena bien, revisar `frontend/src/components/checkout/CustomerForm.tsx` (función `handleGoogleSignIn`) y el endpoint `POST /api/public/{slug}/cliente/perfil` (`backend/app/routers/clientes_publico.py`) — la lógica está cubierta por tests automatizados (backend) pero el flujo real del popup de Google nunca se ejecutó de punta a punta en una sesión de Claude Code (no se puede simular el consentimiento real de Google desde el navegador controlado).

No hay ningún bug conocido pendiente en este momento — todo lo demás de la sesión de hoy quedó verificado (tests + pruebas manuales en Docker).

## Notas de seguridad
- `FERNET_KEY` NUNCA debe tener un valor por defecto hardcodeado en `backend/app/config.py` (ya pasó una vez y bloqueó el push). Debe venir solo de `.env` (gitignored).
- `GOOGLE_CLIENT_ID` no es secreto (es un identificador público), pero igual vive solo en `.env`/`frontend/.env`, nunca hardcodeado.
