from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


async def _login(client: AsyncClient, email: str, password: str) -> str:
    response = await client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def _crear_pedido(client: AsyncClient, restaurante, item, mesa) -> int:
    response = await client.post(
        f"/api/public/{restaurante.slug}/pedidos",
        json={
            "mesa_codigo_qr": mesa.codigo_qr,
            "cliente": {"nombre": "Cliente Test", "consentimiento_datos": True},
            "metodo_pago": "efectivo_en_restaurante",
            "items": [{"item_id": item.id, "cantidad": 1}],
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["en_cocina_en"] is None
    assert body["listo_en"] is None
    assert body["creado_en"] is not None
    return body["id"]


async def test_transicion_a_en_cocina_marca_timestamp(
    client: AsyncClient, db: AsyncSession, make_restaurante, make_usuario, make_categoria, make_item, make_mesa
):
    restaurante = await make_restaurante(db)
    await make_usuario(db, restaurante=restaurante, email="admin@demo.test", password="clave123")
    categoria = await make_categoria(db, restaurante=restaurante)
    item = await make_item(db, restaurante=restaurante, categoria=categoria)
    mesa = await make_mesa(db, restaurante=restaurante)
    pedido_id = await _crear_pedido(client, restaurante, item, mesa)

    token = await _login(client, "admin@demo.test", "clave123")
    response = await client.patch(
        f"/api/staff/pedidos/{pedido_id}/estado", json={"estado": "en_cocina"}, headers=_auth_headers(token)
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["en_cocina_en"] is not None
    assert body["listo_en"] is None


async def test_transicion_a_listo_marca_timestamp(
    client: AsyncClient, db: AsyncSession, make_restaurante, make_usuario, make_categoria, make_item, make_mesa
):
    restaurante = await make_restaurante(db)
    await make_usuario(db, restaurante=restaurante, email="admin@demo.test", password="clave123")
    categoria = await make_categoria(db, restaurante=restaurante)
    item = await make_item(db, restaurante=restaurante, categoria=categoria)
    mesa = await make_mesa(db, restaurante=restaurante)
    pedido_id = await _crear_pedido(client, restaurante, item, mesa)

    token = await _login(client, "admin@demo.test", "clave123")
    headers = _auth_headers(token)
    await client.patch(f"/api/staff/pedidos/{pedido_id}/estado", json={"estado": "en_cocina"}, headers=headers)
    response = await client.patch(f"/api/staff/pedidos/{pedido_id}/estado", json={"estado": "listo"}, headers=headers)

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["en_cocina_en"] is not None
    assert body["listo_en"] is not None
