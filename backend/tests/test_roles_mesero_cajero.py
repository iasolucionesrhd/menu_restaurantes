from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.enums import RolUsuario


async def _login(client: AsyncClient, email: str, password: str) -> str:
    response = await client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def _crear_pedido_publico(client: AsyncClient, restaurante, item, mesa) -> int:
    response = await client.post(
        f"/api/public/{restaurante.slug}/pedidos",
        json={
            "mesa_codigo_qr": mesa.codigo_qr,
            "cliente": {"nombre": "Cliente Test", "consentimiento_datos": True},
            "metodo_pago": "efectivo_en_restaurante",
            "items": [{"item_id": item.id, "cantidad": 1}],
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


async def test_admin_puede_crear_usuario_mesero(
    client: AsyncClient, db: AsyncSession, make_restaurante, make_usuario
):
    restaurante = await make_restaurante(db)
    await make_usuario(db, restaurante=restaurante, email="admin@demo.test", password="clave123", rol=RolUsuario.ADMIN)
    token = await _login(client, "admin@demo.test", "clave123")

    response = await client.post(
        "/api/admin/usuarios",
        json={"email": "mesero@demo.test", "password": "clave123", "rol": "mesero"},
        headers=_auth_headers(token),
    )
    assert response.status_code == 201, response.text
    assert response.json()["rol"] == "mesero"

    login_mesero = await client.post("/api/auth/login", json={"email": "mesero@demo.test", "password": "clave123"})
    assert login_mesero.status_code == 200


async def test_admin_no_puede_eliminar_su_propia_cuenta(
    client: AsyncClient, db: AsyncSession, make_restaurante, make_usuario
):
    restaurante = await make_restaurante(db)
    admin = await make_usuario(db, restaurante=restaurante, email="admin@demo.test", password="clave123", rol=RolUsuario.ADMIN)
    token = await _login(client, "admin@demo.test", "clave123")

    response = await client.delete(f"/api/admin/usuarios/{admin.id}", headers=_auth_headers(token))
    assert response.status_code == 400


async def test_mesero_puede_crear_pedido_asistido(
    client: AsyncClient, db: AsyncSession, make_restaurante, make_usuario, make_categoria, make_item, make_mesa
):
    restaurante = await make_restaurante(db)
    await make_usuario(db, restaurante=restaurante, email="mesero@demo.test", password="clave123", rol=RolUsuario.MESERO)
    categoria = await make_categoria(db, restaurante=restaurante)
    item = await make_item(db, restaurante=restaurante, categoria=categoria, precio="5.00")
    mesa = await make_mesa(db, restaurante=restaurante)
    token = await _login(client, "mesero@demo.test", "clave123")

    response = await client.post(
        "/api/staff/pedidos/asistido",
        json={"mesa_id": mesa.id, "cliente_nombre": "Mesa 1 - Juan", "items": [{"item_id": item.id, "cantidad": 2}]},
        headers=_auth_headers(token),
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["metodo_pago"] == "efectivo_en_restaurante"
    assert body["pagado"] is False
    assert float(body["monto_total"]) == 10.00


async def test_cajero_no_puede_crear_pedido_asistido(
    client: AsyncClient, db: AsyncSession, make_restaurante, make_usuario, make_categoria, make_item, make_mesa
):
    restaurante = await make_restaurante(db)
    await make_usuario(db, restaurante=restaurante, email="cajero@demo.test", password="clave123", rol=RolUsuario.CAJERO)
    categoria = await make_categoria(db, restaurante=restaurante)
    item = await make_item(db, restaurante=restaurante, categoria=categoria)
    mesa = await make_mesa(db, restaurante=restaurante)
    token = await _login(client, "cajero@demo.test", "clave123")

    response = await client.post(
        "/api/staff/pedidos/asistido",
        json={"mesa_id": mesa.id, "cliente_nombre": "Test", "items": [{"item_id": item.id, "cantidad": 1}]},
        headers=_auth_headers(token),
    )
    assert response.status_code == 403


async def test_mesero_puede_marcar_entregado_pero_no_avanzar_a_en_cocina(
    client: AsyncClient, db: AsyncSession, make_restaurante, make_usuario, make_categoria, make_item, make_mesa
):
    restaurante = await make_restaurante(db)
    await make_usuario(db, restaurante=restaurante, email="admin@demo.test", password="clave123", rol=RolUsuario.ADMIN)
    await make_usuario(db, restaurante=restaurante, email="mesero@demo.test", password="clave123", rol=RolUsuario.MESERO)
    categoria = await make_categoria(db, restaurante=restaurante)
    item = await make_item(db, restaurante=restaurante, categoria=categoria)
    mesa = await make_mesa(db, restaurante=restaurante)
    pedido_id = await _crear_pedido_publico(client, restaurante, item, mesa)

    mesero_token = await _login(client, "mesero@demo.test", "clave123")

    intento_temprano = await client.patch(
        f"/api/staff/pedidos/{pedido_id}/estado", json={"estado": "en_cocina"}, headers=_auth_headers(mesero_token)
    )
    assert intento_temprano.status_code == 403

    admin_token = await _login(client, "admin@demo.test", "clave123")
    admin_headers = _auth_headers(admin_token)
    await client.patch(f"/api/staff/pedidos/{pedido_id}/estado", json={"estado": "en_cocina"}, headers=admin_headers)
    await client.patch(f"/api/staff/pedidos/{pedido_id}/estado", json={"estado": "listo"}, headers=admin_headers)

    entrega = await client.patch(
        f"/api/staff/pedidos/{pedido_id}/estado", json={"estado": "entregado"}, headers=_auth_headers(mesero_token)
    )
    assert entrega.status_code == 200, entrega.text
    assert entrega.json()["estado"] == "entregado"


async def test_mesero_no_puede_cancelar(
    client: AsyncClient, db: AsyncSession, make_restaurante, make_usuario, make_categoria, make_item, make_mesa
):
    restaurante = await make_restaurante(db)
    await make_usuario(db, restaurante=restaurante, email="mesero@demo.test", password="clave123", rol=RolUsuario.MESERO)
    categoria = await make_categoria(db, restaurante=restaurante)
    item = await make_item(db, restaurante=restaurante, categoria=categoria)
    mesa = await make_mesa(db, restaurante=restaurante)
    pedido_id = await _crear_pedido_publico(client, restaurante, item, mesa)

    token = await _login(client, "mesero@demo.test", "clave123")
    response = await client.patch(
        f"/api/staff/pedidos/{pedido_id}/estado", json={"estado": "cancelado"}, headers=_auth_headers(token)
    )
    assert response.status_code == 403


async def test_cajero_puede_marcar_pagado_y_no_puede_cambiar_estado(
    client: AsyncClient, db: AsyncSession, make_restaurante, make_usuario, make_categoria, make_item, make_mesa
):
    restaurante = await make_restaurante(db)
    await make_usuario(db, restaurante=restaurante, email="cajero@demo.test", password="clave123", rol=RolUsuario.CAJERO)
    categoria = await make_categoria(db, restaurante=restaurante)
    item = await make_item(db, restaurante=restaurante, categoria=categoria, precio="7.50")
    mesa = await make_mesa(db, restaurante=restaurante)
    pedido_id = await _crear_pedido_publico(client, restaurante, item, mesa)

    token = await _login(client, "cajero@demo.test", "clave123")
    headers = _auth_headers(token)

    estado_bloqueado = await client.patch(
        f"/api/staff/pedidos/{pedido_id}/estado", json={"estado": "en_cocina"}, headers=headers
    )
    assert estado_bloqueado.status_code == 403

    pagado_resp = await client.patch(f"/api/staff/pedidos/{pedido_id}/pagado", headers=headers)
    assert pagado_resp.status_code == 200, pagado_resp.text
    assert pagado_resp.json()["pagado"] is True


async def test_mesero_no_puede_marcar_pagado(
    client: AsyncClient, db: AsyncSession, make_restaurante, make_usuario, make_categoria, make_item, make_mesa
):
    restaurante = await make_restaurante(db)
    await make_usuario(db, restaurante=restaurante, email="mesero@demo.test", password="clave123", rol=RolUsuario.MESERO)
    categoria = await make_categoria(db, restaurante=restaurante)
    item = await make_item(db, restaurante=restaurante, categoria=categoria)
    mesa = await make_mesa(db, restaurante=restaurante)
    pedido_id = await _crear_pedido_publico(client, restaurante, item, mesa)

    token = await _login(client, "mesero@demo.test", "clave123")
    response = await client.patch(f"/api/staff/pedidos/{pedido_id}/pagado", headers=_auth_headers(token))
    assert response.status_code == 403


async def test_pedido_con_tarjeta_queda_pagado_automaticamente(
    client: AsyncClient, db: AsyncSession, make_restaurante, make_categoria, make_item, make_mesa
):
    restaurante = await make_restaurante(db)
    categoria = await make_categoria(db, restaurante=restaurante)
    item = await make_item(db, restaurante=restaurante, categoria=categoria)
    mesa = await make_mesa(db, restaurante=restaurante)

    response = await client.post(
        f"/api/public/{restaurante.slug}/pedidos",
        json={
            "mesa_codigo_qr": mesa.codigo_qr,
            "cliente": {"nombre": "Cliente Test", "consentimiento_datos": True},
            "metodo_pago": "tarjeta",
            "items": [{"item_id": item.id, "cantidad": 1}],
            "payment_intent_id": "pi_stub_test",
        },
    )
    assert response.status_code == 201, response.text
    assert response.json()["pagado"] is True


async def test_resumen_caja_suma_pedidos_pagados_del_dia(
    client: AsyncClient, db: AsyncSession, make_restaurante, make_usuario, make_categoria, make_item, make_mesa
):
    restaurante = await make_restaurante(db)
    await make_usuario(db, restaurante=restaurante, email="cajero@demo.test", password="clave123", rol=RolUsuario.CAJERO)
    categoria = await make_categoria(db, restaurante=restaurante)
    item = await make_item(db, restaurante=restaurante, categoria=categoria, precio="4.00")
    mesa = await make_mesa(db, restaurante=restaurante)
    pedido_id = await _crear_pedido_publico(client, restaurante, item, mesa)

    token = await _login(client, "cajero@demo.test", "clave123")
    headers = _auth_headers(token)
    await client.patch(f"/api/staff/pedidos/{pedido_id}/pagado", headers=headers)

    response = await client.get("/api/staff/pedidos/resumen-caja", headers=headers)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["pedidos_cobrados_hoy"] == 1
    assert float(body["cobrado_hoy"]) == 4.00
