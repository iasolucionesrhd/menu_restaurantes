from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.enums import RolUsuario


async def _login(client: AsyncClient, email: str, password: str) -> str:
    response = await client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def _crear_pedido(client: AsyncClient, restaurante, item, mesa, metodo_pago: str, payment_intent_id=None) -> int:
    payload = {
        "mesa_codigo_qr": mesa.codigo_qr,
        "cliente": {"nombre": "Cliente Test", "consentimiento_datos": True},
        "metodo_pago": metodo_pago,
        "items": [{"item_id": item.id, "cantidad": 1}],
    }
    if payment_intent_id:
        payload["payment_intent_id"] = payment_intent_id
    response = await client.post(f"/api/public/{restaurante.slug}/pedidos", json=payload)
    assert response.status_code == 201, response.text
    return response.json()["id"]


async def test_cierre_desglosa_por_metodo_de_pago(
    client: AsyncClient, db: AsyncSession, make_restaurante, make_usuario, make_categoria, make_item, make_mesa
):
    restaurante = await make_restaurante(db)
    await make_usuario(db, restaurante=restaurante, email="cajero@demo.test", password="clave123", rol=RolUsuario.CAJERO)
    categoria = await make_categoria(db, restaurante=restaurante)
    item = await make_item(db, restaurante=restaurante, categoria=categoria, precio="5.00")
    mesa = await make_mesa(db, restaurante=restaurante)

    pedido_efectivo = await _crear_pedido(client, restaurante, item, mesa, "efectivo_en_restaurante")
    await _crear_pedido(client, restaurante, item, mesa, "tarjeta", payment_intent_id="pi_1")
    await _crear_pedido(client, restaurante, item, mesa, "sinpe", payment_intent_id="pi_2")

    token = await _login(client, "cajero@demo.test", "clave123")
    headers = _auth_headers(token)
    await client.patch(f"/api/staff/pedidos/{pedido_efectivo}/pagado", headers=headers)

    response = await client.post("/api/staff/pedidos/cierres-caja", headers=headers)
    assert response.status_code == 201, response.text
    body = response.json()
    assert float(body["total_efectivo"]) == 5.00
    assert body["cantidad_efectivo"] == 1
    assert float(body["total_tarjeta"]) == 5.00
    assert body["cantidad_tarjeta"] == 1
    assert float(body["total_sinpe"]) == 5.00
    assert body["cantidad_sinpe"] == 1
    assert float(body["total_apple_pay"]) == 0
    assert float(body["total_general"]) == 15.00
    assert body["cantidad_general"] == 3


async def test_resumen_caja_se_resetea_tras_el_cierre(
    client: AsyncClient, db: AsyncSession, make_restaurante, make_usuario, make_categoria, make_item, make_mesa
):
    restaurante = await make_restaurante(db)
    await make_usuario(db, restaurante=restaurante, email="cajero@demo.test", password="clave123", rol=RolUsuario.CAJERO)
    categoria = await make_categoria(db, restaurante=restaurante)
    item = await make_item(db, restaurante=restaurante, categoria=categoria, precio="3.00")
    mesa = await make_mesa(db, restaurante=restaurante)
    pedido_id = await _crear_pedido(client, restaurante, item, mesa, "efectivo_en_restaurante")

    token = await _login(client, "cajero@demo.test", "clave123")
    headers = _auth_headers(token)
    await client.patch(f"/api/staff/pedidos/{pedido_id}/pagado", headers=headers)

    antes = await client.get("/api/staff/pedidos/resumen-caja", headers=headers)
    assert antes.json()["pedidos_periodo_actual"] == 1

    await client.post("/api/staff/pedidos/cierres-caja", headers=headers)

    despues = await client.get("/api/staff/pedidos/resumen-caja", headers=headers)
    assert despues.json()["pedidos_periodo_actual"] == 0
    assert float(despues.json()["cobrado_periodo_actual"]) == 0


async def test_pedido_incluido_en_cierre_no_se_puede_cancelar(
    client: AsyncClient, db: AsyncSession, make_restaurante, make_usuario, make_categoria, make_item, make_mesa
):
    restaurante = await make_restaurante(db)
    await make_usuario(db, restaurante=restaurante, email="admin@demo.test", password="clave123", rol=RolUsuario.ADMIN)
    categoria = await make_categoria(db, restaurante=restaurante)
    item = await make_item(db, restaurante=restaurante, categoria=categoria)
    mesa = await make_mesa(db, restaurante=restaurante)
    pedido_id = await _crear_pedido(client, restaurante, item, mesa, "efectivo_en_restaurante")

    token = await _login(client, "admin@demo.test", "clave123")
    headers = _auth_headers(token)
    await client.patch(f"/api/staff/pedidos/{pedido_id}/pagado", headers=headers)
    await client.post("/api/staff/pedidos/cierres-caja", headers=headers)

    response = await client.patch(
        f"/api/staff/pedidos/{pedido_id}/estado", json={"estado": "cancelado"}, headers=headers
    )
    assert response.status_code == 400


async def test_pedido_cancelado_no_cuenta_en_el_cierre(
    client: AsyncClient, db: AsyncSession, make_restaurante, make_usuario, make_categoria, make_item, make_mesa
):
    restaurante = await make_restaurante(db)
    await make_usuario(db, restaurante=restaurante, email="admin@demo.test", password="clave123", rol=RolUsuario.ADMIN)
    categoria = await make_categoria(db, restaurante=restaurante)
    item = await make_item(db, restaurante=restaurante, categoria=categoria, precio="6.00")
    mesa = await make_mesa(db, restaurante=restaurante)
    pedido_id = await _crear_pedido(client, restaurante, item, mesa, "tarjeta", payment_intent_id="pi_x")

    token = await _login(client, "admin@demo.test", "clave123")
    headers = _auth_headers(token)
    cancel = await client.patch(
        f"/api/staff/pedidos/{pedido_id}/estado", json={"estado": "cancelado"}, headers=headers
    )
    assert cancel.status_code == 200

    response = await client.post("/api/staff/pedidos/cierres-caja", headers=headers)
    assert response.json()["cantidad_general"] == 0


async def test_segundo_cierre_no_duplica_pedidos_del_primero(
    client: AsyncClient, db: AsyncSession, make_restaurante, make_usuario, make_categoria, make_item, make_mesa
):
    restaurante = await make_restaurante(db)
    await make_usuario(db, restaurante=restaurante, email="cajero@demo.test", password="clave123", rol=RolUsuario.CAJERO)
    categoria = await make_categoria(db, restaurante=restaurante)
    item = await make_item(db, restaurante=restaurante, categoria=categoria, precio="2.00")
    mesa = await make_mesa(db, restaurante=restaurante)
    pedido_1 = await _crear_pedido(client, restaurante, item, mesa, "efectivo_en_restaurante")

    token = await _login(client, "cajero@demo.test", "clave123")
    headers = _auth_headers(token)
    await client.patch(f"/api/staff/pedidos/{pedido_1}/pagado", headers=headers)
    primer_cierre = await client.post("/api/staff/pedidos/cierres-caja", headers=headers)
    assert primer_cierre.json()["cantidad_general"] == 1

    pedido_2 = await _crear_pedido(client, restaurante, item, mesa, "efectivo_en_restaurante")
    await client.patch(f"/api/staff/pedidos/{pedido_2}/pagado", headers=headers)
    segundo_cierre = await client.post("/api/staff/pedidos/cierres-caja", headers=headers)
    assert segundo_cierre.json()["cantidad_general"] == 1

    historial = await client.get("/api/staff/pedidos/cierres-caja", headers=headers)
    assert len(historial.json()) == 2


async def test_mesero_no_puede_cerrar_caja(
    client: AsyncClient, db: AsyncSession, make_restaurante, make_usuario
):
    restaurante = await make_restaurante(db)
    await make_usuario(db, restaurante=restaurante, email="mesero@demo.test", password="clave123", rol=RolUsuario.MESERO)
    token = await _login(client, "mesero@demo.test", "clave123")

    response = await client.post("/api/staff/pedidos/cierres-caja", headers=_auth_headers(token))
    assert response.status_code == 403
