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
            "cliente": {"nombre": "Cliente Test"},
            "metodo_pago": "efectivo_en_restaurante",
            "items": [{"item_id": item.id, "cantidad": 1}],
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


async def test_cadena_valida_de_estados(
    client: AsyncClient,
    db: AsyncSession,
    make_restaurante,
    make_usuario,
    make_categoria,
    make_item,
    make_mesa,
):
    restaurante = await make_restaurante(db)
    await make_usuario(db, restaurante=restaurante, email="cocina@demo.test", password="clave123")
    categoria = await make_categoria(db, restaurante=restaurante)
    item = await make_item(db, restaurante=restaurante, categoria=categoria, precio="4.00")
    mesa = await make_mesa(db, restaurante=restaurante)
    pedido_id = await _crear_pedido(client, restaurante, item, mesa)

    token = await _login(client, "cocina@demo.test", "clave123")
    headers = _auth_headers(token)

    for estado in ["en_cocina", "listo", "entregado"]:
        response = await client.patch(
            f"/api/staff/pedidos/{pedido_id}/estado", json={"estado": estado}, headers=headers
        )
        assert response.status_code == 200, response.text
        assert response.json()["estado"] == estado


async def test_salto_ilegal_de_estado_es_rechazado(
    client: AsyncClient,
    db: AsyncSession,
    make_restaurante,
    make_usuario,
    make_categoria,
    make_item,
    make_mesa,
):
    restaurante = await make_restaurante(db)
    await make_usuario(db, restaurante=restaurante, email="cocina@demo.test", password="clave123")
    categoria = await make_categoria(db, restaurante=restaurante)
    item = await make_item(db, restaurante=restaurante, categoria=categoria, precio="4.00")
    mesa = await make_mesa(db, restaurante=restaurante)
    pedido_id = await _crear_pedido(client, restaurante, item, mesa)

    token = await _login(client, "cocina@demo.test", "clave123")

    response = await client.patch(
        f"/api/staff/pedidos/{pedido_id}/estado",
        json={"estado": "entregado"},
        headers=_auth_headers(token),
    )

    assert response.status_code == 400


async def test_no_se_puede_transicionar_pedido_ya_entregado(
    client: AsyncClient,
    db: AsyncSession,
    make_restaurante,
    make_usuario,
    make_categoria,
    make_item,
    make_mesa,
):
    restaurante = await make_restaurante(db)
    await make_usuario(db, restaurante=restaurante, email="cocina@demo.test", password="clave123")
    categoria = await make_categoria(db, restaurante=restaurante)
    item = await make_item(db, restaurante=restaurante, categoria=categoria, precio="4.00")
    mesa = await make_mesa(db, restaurante=restaurante)
    pedido_id = await _crear_pedido(client, restaurante, item, mesa)

    token = await _login(client, "cocina@demo.test", "clave123")
    headers = _auth_headers(token)

    for estado in ["en_cocina", "listo", "entregado"]:
        await client.patch(f"/api/staff/pedidos/{pedido_id}/estado", json={"estado": estado}, headers=headers)

    response = await client.patch(
        f"/api/staff/pedidos/{pedido_id}/estado", json={"estado": "en_cocina"}, headers=headers
    )
    assert response.status_code == 400


async def test_staff_de_otro_restaurante_no_puede_transicionar(
    client: AsyncClient,
    db: AsyncSession,
    make_restaurante,
    make_usuario,
    make_categoria,
    make_item,
    make_mesa,
):
    restaurante_a = await make_restaurante(db, nombre="A", slug="restaurante-a")
    restaurante_b = await make_restaurante(db, nombre="B", slug="restaurante-b")
    await make_usuario(db, restaurante=restaurante_b, email="cocina.b@demo.test", password="clave123")
    categoria = await make_categoria(db, restaurante=restaurante_a)
    item = await make_item(db, restaurante=restaurante_a, categoria=categoria, precio="4.00")
    mesa = await make_mesa(db, restaurante=restaurante_a)
    pedido_id = await _crear_pedido(client, restaurante_a, item, mesa)

    token_b = await _login(client, "cocina.b@demo.test", "clave123")

    response = await client.patch(
        f"/api/staff/pedidos/{pedido_id}/estado",
        json={"estado": "en_cocina"},
        headers=_auth_headers(token_b),
    )

    assert response.status_code == 404
