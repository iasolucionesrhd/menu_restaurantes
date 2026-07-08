# Menú Digital QR

SaaS multi-tenant de menú digital por QR para restaurantes. Ver [SPEC.md](SPEC.md) para el detalle funcional completo.

## Stack

- **Backend**: FastAPI (async) + SQLAlchemy 2.0 (async) + PostgreSQL + Alembic
- **Frontend**: React + Vite + TypeScript + React Query
- **Tiempo real**: WebSockets nativos de FastAPI (pantalla de cocina)
- **Pagos**: adaptador propio (`PaymentAdapter`) con implementación stub (simulada) y una implementación real de Tilopay lista para activarse con credenciales sandbox
- **Infra local**: Docker Compose (Postgres + backend + frontend)

## Requisitos

- Docker Desktop (con WSL2 en Windows — requiere virtualización habilitada en el BIOS/UEFI)
- Node.js y Python solo son necesarios si quieres correr algo fuera de Docker

## Arranque rápido

```bash
cp .env.example .env
# Genera una FERNET_KEY real y pégala en .env:
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

cp frontend/.env.example frontend/.env

docker-compose up --build
```

Esto levanta:
- Postgres en `localhost:5432` (bases `menu_digital` y `menu_test`)
- Backend en `http://localhost:8000` (aplica migraciones y siembra datos demo automáticamente al arrancar)
- Frontend en `http://localhost:5173`

Al arrancar, el backend imprime en su log las URLs de mesa del restaurante demo y las credenciales de staff:

```
docker-compose logs backend | grep -A 10 "Restaurante demo creado"
```

Credenciales demo (contraseña definida por `SEED_ADMIN_PASSWORD` en `.env`, por defecto `devpassword123`):
- Admin: `admin@pizzeria-luna.demo`
- Cocina: `cocina@pizzeria-luna.demo`

## Estructura

```
backend/    API FastAPI, modelos, migraciones Alembic, tests
frontend/   React + Vite (menú público, checkout, cocina, panel admin)
db/init/    Script SQL para crear la base de datos de test al iniciar Postgres
```

## Pagos: modo stub vs Tilopay

Por defecto `PAYMENT_MODE=stub`: el checkout muestra un botón "Simular pago aprobado" en vez del SDK real de Tilopay, permitiendo probar el flujo completo (menú → carrito → checkout → cocina) sin credenciales reales.

Cuando haya credenciales sandbox de Tilopay:
1. Guardarlas (vía el panel admin o directamente en la tabla `restaurante`, se cifran automáticamente).
2. Cambiar `PAYMENT_MODE=tilopay` en `.env`.
3. Completar los `TODO` marcados en `backend/app/services/payments/tilopay_adapter.py` con los endpoints reales de la API de Tilopay.

## Tests del backend

Con los servicios levantados:

```bash
docker-compose exec backend pytest
```

Cubren aislamiento multi-tenant, autenticación, transiciones de estado de pedidos, snapshot de precios, y los adaptadores de pago.

## Verificación manual del flujo completo

1. Abrir una de las URLs de mesa demo impresas por el seed.
2. Agregar items al carrito (con notas) y pasar a checkout.
3. Completar el pedido con "Efectivo" o simulando un pago con tarjeta/SINPE.
4. Iniciar sesión en `/login` como `cocina@pizzeria-luna.demo` y abrir `/cocina`: el pedido debe aparecer en tiempo real.
5. Avanzar el pedido por sus estados desde la pantalla de cocina.
6. Iniciar sesión como `admin@pizzeria-luna.demo` en `/admin` para gestionar categorías, items y mesas (incluye código QR de cada mesa).
