from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.enums import RolUsuario
from app.models.ingrediente import Ingrediente


async def _login(client: AsyncClient, email: str, password: str) -> str:
    response = await client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def _crear_pedido(client: AsyncClient, restaurante, item, mesa, cantidad: int = 1) -> int:
    response = await client.post(
        f"/api/public/{restaurante.slug}/pedidos",
        json={
            "mesa_codigo_qr": mesa.codigo_qr,
            "cliente": {"nombre": "Cliente Test", "consentimiento_datos": True},
            "metodo_pago": "efectivo_en_restaurante",
            "items": [{"item_id": item.id, "cantidad": cantidad}],
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


async def test_admin_puede_crear_ingrediente(
    client: AsyncClient, db: AsyncSession, make_restaurante, make_usuario
):
    restaurante = await make_restaurante(db)
    await make_usuario(db, restaurante=restaurante, email="admin@demo.test", password="clave123", rol=RolUsuario.ADMIN)
    token = await _login(client, "admin@demo.test", "clave123")

    response = await client.post(
        "/api/admin/ingredientes",
        json={"nombre": "Mozzarella", "unidad": "g", "stock_actual": "1000", "stock_minimo": "200"},
        headers=_auth_headers(token),
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["nombre"] == "Mozzarella"
    assert body["stock_bajo"] is False


async def test_ingrediente_marca_stock_bajo(
    client: AsyncClient, db: AsyncSession, make_restaurante, make_usuario, make_ingrediente
):
    restaurante = await make_restaurante(db)
    await make_usuario(db, restaurante=restaurante, email="admin@demo.test", password="clave123", rol=RolUsuario.ADMIN)
    await make_ingrediente(db, restaurante=restaurante, nombre="Piña", stock_actual="50", stock_minimo="100")
    token = await _login(client, "admin@demo.test", "clave123")

    response = await client.get("/api/admin/ingredientes", headers=_auth_headers(token))
    assert response.status_code == 200
    assert response.json()[0]["stock_bajo"] is True


async def test_set_receta_item_y_lectura(
    client: AsyncClient,
    db: AsyncSession,
    make_restaurante,
    make_usuario,
    make_categoria,
    make_item,
    make_ingrediente,
):
    restaurante = await make_restaurante(db)
    await make_usuario(db, restaurante=restaurante, email="admin@demo.test", password="clave123", rol=RolUsuario.ADMIN)
    categoria = await make_categoria(db, restaurante=restaurante)
    item = await make_item(db, restaurante=restaurante, categoria=categoria)
    mozzarella = await make_ingrediente(db, restaurante=restaurante, nombre="Mozzarella", unidad="g")
    salsa = await make_ingrediente(db, restaurante=restaurante, nombre="Salsa de tomate", unidad="ml")
    token = await _login(client, "admin@demo.test", "clave123")

    response = await client.put(
        f"/api/admin/items/{item.id}/ingredientes",
        json={
            "ingredientes": [
                {"ingrediente_id": mozzarella.id, "cantidad_requerida": "200"},
                {"ingrediente_id": salsa.id, "cantidad_requerida": "100"},
            ]
        },
        headers=_auth_headers(token),
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert len(body["ingredientes"]) == 2
    nombres = {i["nombre"] for i in body["ingredientes"]}
    assert nombres == {"Mozzarella", "Salsa de tomate"}


async def test_pedido_descuenta_stock_de_ingredientes(
    client: AsyncClient,
    db: AsyncSession,
    make_restaurante,
    make_categoria,
    make_item,
    make_mesa,
    make_ingrediente,
    make_receta,
):
    restaurante = await make_restaurante(db)
    categoria = await make_categoria(db, restaurante=restaurante)
    item = await make_item(db, restaurante=restaurante, categoria=categoria)
    mesa = await make_mesa(db, restaurante=restaurante)
    mozzarella = await make_ingrediente(db, restaurante=restaurante, stock_actual="1000")
    await make_receta(db, item=item, ingrediente=mozzarella, cantidad_requerida="200")

    await _crear_pedido(client, restaurante, item, mesa, cantidad=2)

    await db.refresh(mozzarella)
    result = await db.execute(select(Ingrediente).where(Ingrediente.id == mozzarella.id))
    actualizado = result.scalar_one()
    assert float(actualizado.stock_actual) == 600.0  # 1000 - (200 * 2)


async def test_pedido_permite_stock_negativo_sin_bloquear(
    client: AsyncClient,
    db: AsyncSession,
    make_restaurante,
    make_categoria,
    make_item,
    make_mesa,
    make_ingrediente,
    make_receta,
):
    restaurante = await make_restaurante(db)
    categoria = await make_categoria(db, restaurante=restaurante)
    item = await make_item(db, restaurante=restaurante, categoria=categoria)
    mesa = await make_mesa(db, restaurante=restaurante)
    escasa = await make_ingrediente(db, restaurante=restaurante, stock_actual="50")
    await make_receta(db, item=item, ingrediente=escasa, cantidad_requerida="200")

    pedido_id = await _crear_pedido(client, restaurante, item, mesa, cantidad=1)
    assert pedido_id is not None

    result = await db.execute(select(Ingrediente).where(Ingrediente.id == escasa.id))
    actualizado = result.scalar_one()
    assert float(actualizado.stock_actual) == -150.0


async def test_cancelar_pedido_devuelve_stock(
    client: AsyncClient,
    db: AsyncSession,
    make_restaurante,
    make_usuario,
    make_categoria,
    make_item,
    make_mesa,
    make_ingrediente,
    make_receta,
):
    restaurante = await make_restaurante(db)
    await make_usuario(db, restaurante=restaurante, email="admin@demo.test", password="clave123", rol=RolUsuario.ADMIN)
    categoria = await make_categoria(db, restaurante=restaurante)
    item = await make_item(db, restaurante=restaurante, categoria=categoria)
    mesa = await make_mesa(db, restaurante=restaurante)
    mozzarella = await make_ingrediente(db, restaurante=restaurante, stock_actual="1000")
    await make_receta(db, item=item, ingrediente=mozzarella, cantidad_requerida="200")

    pedido_id = await _crear_pedido(client, restaurante, item, mesa, cantidad=1)

    token = await _login(client, "admin@demo.test", "clave123")
    response = await client.patch(
        f"/api/staff/pedidos/{pedido_id}/estado", json={"estado": "cancelado"}, headers=_auth_headers(token)
    )
    assert response.status_code == 200, response.text

    result = await db.execute(select(Ingrediente).where(Ingrediente.id == mozzarella.id))
    actualizado = result.scalar_one()
    assert float(actualizado.stock_actual) == 1000.0
