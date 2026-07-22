from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.enums import RolUsuario
from app.models.usuario_restaurante import UsuarioRestaurante


async def _login(client: AsyncClient, email: str, password: str) -> str:
    response = await client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def test_admin_puede_crear_sucursal_y_queda_vinculada(
    client: AsyncClient, db: AsyncSession, make_restaurante, make_usuario
):
    restaurante = await make_restaurante(db)
    admin = await make_usuario(db, restaurante=restaurante, email="admin@demo.test", password="clave123", rol=RolUsuario.ADMIN)
    token = await _login(client, "admin@demo.test", "clave123")

    response = await client.post(
        "/api/admin/sucursales", json={"nombre": "Sucursal Cartago", "slug": "sucursal-cartago"}, headers=_auth_headers(token)
    )
    assert response.status_code == 201, response.text
    nueva_id = response.json()["id"]

    result = await db.execute(
        select(UsuarioRestaurante).where(
            UsuarioRestaurante.usuario_id == admin.id, UsuarioRestaurante.restaurante_id == nueva_id
        )
    )
    assert result.scalar_one_or_none() is not None


async def test_slug_duplicado_falla(client: AsyncClient, db: AsyncSession, make_restaurante, make_usuario):
    restaurante = await make_restaurante(db, slug="pizzeria-luna")
    await make_usuario(db, restaurante=restaurante, email="admin@demo.test", password="clave123", rol=RolUsuario.ADMIN)
    token = await _login(client, "admin@demo.test", "clave123")

    response = await client.post(
        "/api/admin/sucursales", json={"nombre": "Otra", "slug": "pizzeria-luna"}, headers=_auth_headers(token)
    )
    assert response.status_code == 400


async def test_cocina_no_puede_crear_sucursal(client: AsyncClient, db: AsyncSession, make_restaurante, make_usuario):
    restaurante = await make_restaurante(db)
    await make_usuario(db, restaurante=restaurante, email="cocina@demo.test", password="clave123", rol=RolUsuario.COCINA)
    token = await _login(client, "cocina@demo.test", "clave123")

    response = await client.post(
        "/api/admin/sucursales", json={"nombre": "Otra", "slug": "otra-sucursal"}, headers=_auth_headers(token)
    )
    assert response.status_code == 403


async def test_mis_restaurantes_incluye_origen_y_creadas(
    client: AsyncClient, db: AsyncSession, make_restaurante, make_usuario
):
    restaurante = await make_restaurante(db, slug="pizzeria-luna")
    await make_usuario(db, restaurante=restaurante, email="admin@demo.test", password="clave123", rol=RolUsuario.ADMIN)
    token = await _login(client, "admin@demo.test", "clave123")
    headers = _auth_headers(token)

    await client.post("/api/admin/sucursales", json={"nombre": "Sucursal 2", "slug": "sucursal-2"}, headers=headers)

    response = await client.get("/api/auth/mis-restaurantes", headers=headers)
    assert response.status_code == 200
    slugs = {r["slug"] for r in response.json()}
    assert slugs == {"pizzeria-luna", "sucursal-2"}


async def test_cocina_solo_ve_su_propia_sucursal(
    client: AsyncClient, db: AsyncSession, make_restaurante, make_usuario
):
    restaurante = await make_restaurante(db)
    await make_usuario(db, restaurante=restaurante, email="cocina@demo.test", password="clave123", rol=RolUsuario.COCINA)
    token = await _login(client, "cocina@demo.test", "clave123")

    response = await client.get("/api/auth/mis-restaurantes", headers=_auth_headers(token))
    assert response.status_code == 200
    assert len(response.json()) == 1


async def test_cambiar_restaurante_aisla_datos_entre_sucursales(
    client: AsyncClient, db: AsyncSession, make_restaurante, make_usuario
):
    restaurante = await make_restaurante(db, slug="pizzeria-luna")
    await make_usuario(db, restaurante=restaurante, email="admin@demo.test", password="clave123", rol=RolUsuario.ADMIN)
    token = await _login(client, "admin@demo.test", "clave123")
    headers = _auth_headers(token)

    await client.post("/api/admin/categorias", json={"nombre": "Pizzas", "orden": 0}, headers=headers)

    crear_sucursal = await client.post(
        "/api/admin/sucursales", json={"nombre": "Sucursal 2", "slug": "sucursal-2"}, headers=headers
    )
    nueva_id = crear_sucursal.json()["id"]

    cambio = await client.post("/api/auth/cambiar-restaurante", json={"restaurante_id": nueva_id}, headers=headers)
    assert cambio.status_code == 200, cambio.text
    nuevo_token = cambio.json()["access_token"]
    assert cambio.json()["usuario"]["restaurante_slug"] == "sucursal-2"
    nuevos_headers = _auth_headers(nuevo_token)

    categorias_nueva_sucursal = await client.get("/api/admin/categorias", headers=nuevos_headers)
    assert categorias_nueva_sucursal.json() == []

    categorias_original = await client.get("/api/admin/categorias", headers=headers)
    assert len(categorias_original.json()) == 1

    await client.post("/api/admin/categorias", json={"nombre": "Bebidas", "orden": 0}, headers=nuevos_headers)
    categorias_nueva_sucursal2 = await client.get("/api/admin/categorias", headers=nuevos_headers)
    assert len(categorias_nueva_sucursal2.json()) == 1
    assert categorias_nueva_sucursal2.json()[0]["nombre"] == "Bebidas"


async def test_no_puede_cambiar_a_sucursal_ajena(
    client: AsyncClient, db: AsyncSession, make_restaurante, make_usuario
):
    restaurante_a = await make_restaurante(db, nombre="A", slug="restaurante-a")
    restaurante_b = await make_restaurante(db, nombre="B", slug="restaurante-b")
    await make_usuario(db, restaurante=restaurante_a, email="admin@demo.test", password="clave123", rol=RolUsuario.ADMIN)
    token = await _login(client, "admin@demo.test", "clave123")

    response = await client.post(
        "/api/auth/cambiar-restaurante", json={"restaurante_id": restaurante_b.id}, headers=_auth_headers(token)
    )
    assert response.status_code == 403
