from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


async def _login(client: AsyncClient, email: str, password: str) -> str:
    response = await client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def test_admin_a_cannot_read_categoria_from_restaurante_b(
    client: AsyncClient, db: AsyncSession, make_restaurante, make_usuario, make_categoria
):
    restaurante_a = await make_restaurante(db, nombre="Restaurante A", slug="restaurante-a")
    restaurante_b = await make_restaurante(db, nombre="Restaurante B", slug="restaurante-b")
    await make_usuario(db, restaurante=restaurante_a, email="admin.a@demo.test", password="clave123")
    await make_usuario(db, restaurante=restaurante_b, email="admin.b@demo.test", password="clave123")
    categoria_b = await make_categoria(db, restaurante=restaurante_b, nombre="Bebidas B")

    token_a = await _login(client, "admin.a@demo.test", "clave123")

    response = await client.patch(
        f"/api/admin/categorias/{categoria_b.id}",
        json={"nombre": "hackeado"},
        headers=_auth_headers(token_a),
    )

    assert response.status_code == 404


async def test_admin_a_cannot_delete_item_from_restaurante_b(
    client: AsyncClient, db: AsyncSession, make_restaurante, make_usuario, make_categoria, make_item
):
    restaurante_a = await make_restaurante(db, nombre="Restaurante A", slug="restaurante-a")
    restaurante_b = await make_restaurante(db, nombre="Restaurante B", slug="restaurante-b")
    await make_usuario(db, restaurante=restaurante_a, email="admin.a@demo.test", password="clave123")
    categoria_b = await make_categoria(db, restaurante=restaurante_b, nombre="Postres B")
    item_b = await make_item(db, restaurante=restaurante_b, categoria=categoria_b, nombre="Tiramisú")

    token_a = await _login(client, "admin.a@demo.test", "clave123")

    response = await client.delete(f"/api/admin/items/{item_b.id}", headers=_auth_headers(token_a))

    assert response.status_code == 404


async def test_admin_a_cannot_delete_mesa_from_restaurante_b(
    client: AsyncClient, db: AsyncSession, make_restaurante, make_usuario, make_mesa
):
    restaurante_a = await make_restaurante(db, nombre="Restaurante A", slug="restaurante-a")
    restaurante_b = await make_restaurante(db, nombre="Restaurante B", slug="restaurante-b")
    await make_usuario(db, restaurante=restaurante_a, email="admin.a@demo.test", password="clave123")
    mesa_b = await make_mesa(db, restaurante=restaurante_b, numero=5, codigo_qr="qr-b-5")

    token_a = await _login(client, "admin.a@demo.test", "clave123")

    response = await client.delete(f"/api/admin/mesas/{mesa_b.id}", headers=_auth_headers(token_a))

    assert response.status_code == 404


async def test_categorias_list_only_returns_own_restaurante(
    client: AsyncClient, db: AsyncSession, make_restaurante, make_usuario, make_categoria
):
    restaurante_a = await make_restaurante(db, nombre="Restaurante A", slug="restaurante-a")
    restaurante_b = await make_restaurante(db, nombre="Restaurante B", slug="restaurante-b")
    await make_usuario(db, restaurante=restaurante_a, email="admin.a@demo.test", password="clave123")
    await make_categoria(db, restaurante=restaurante_a, nombre="Categoria A")
    await make_categoria(db, restaurante=restaurante_b, nombre="Categoria B")

    token_a = await _login(client, "admin.a@demo.test", "clave123")

    response = await client.get("/api/admin/categorias", headers=_auth_headers(token_a))

    assert response.status_code == 200
    nombres = {c["nombre"] for c in response.json()}
    assert nombres == {"Categoria A"}


async def test_cocina_role_cannot_access_admin_only_route(
    client: AsyncClient, db: AsyncSession, make_restaurante, make_usuario
):
    from app.enums import RolUsuario

    restaurante = await make_restaurante(db)
    await make_usuario(
        db, restaurante=restaurante, email="cocina@demo.test", password="clave123", rol=RolUsuario.COCINA
    )

    token = await _login(client, "cocina@demo.test", "clave123")

    response = await client.get("/api/admin/categorias", headers=_auth_headers(token))

    assert response.status_code == 403
