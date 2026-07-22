from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.enums import RolUsuario
from app.models.nota_credito import NotaCredito
from app.models.pedido import Pedido


async def _login(client: AsyncClient, email: str, password: str) -> str:
    response = await client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def _crear_pedido(client: AsyncClient, restaurante, item, mesa, *, datos_facturacion=None) -> int:
    cliente = {"nombre": "Cliente Test", "consentimiento_datos": True}
    if datos_facturacion is not None:
        cliente["datos_facturacion"] = datos_facturacion
    response = await client.post(
        f"/api/public/{restaurante.slug}/pedidos",
        json={
            "mesa_codigo_qr": mesa.codigo_qr,
            "cliente": cliente,
            "metodo_pago": "efectivo_en_restaurante",
            "items": [{"item_id": item.id, "cantidad": 1}],
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


DATOS_FACTURACION = {
    "nombre": "Empresa Prueba SA",
    "cedula": "3-101-123456",
    "correo": "facturas@empresa.test",
    "telefono": "22334455",
    "direccion": "San José, Costa Rica",
    "actividad_economica": "620100",
}


async def test_admin_puede_cancelar_pedido_recibido_sin_pin(
    client: AsyncClient, db: AsyncSession, make_restaurante, make_usuario, make_categoria, make_item, make_mesa
):
    restaurante = await make_restaurante(db)
    await make_usuario(db, restaurante=restaurante, email="admin@demo.test", password="clave123", rol=RolUsuario.ADMIN)
    categoria = await make_categoria(db, restaurante=restaurante)
    item = await make_item(db, restaurante=restaurante, categoria=categoria)
    mesa = await make_mesa(db, restaurante=restaurante)
    pedido_id = await _crear_pedido(client, restaurante, item, mesa)

    token = await _login(client, "admin@demo.test", "clave123")
    response = await client.patch(
        f"/api/staff/pedidos/{pedido_id}/estado", json={"estado": "cancelado"}, headers=_auth_headers(token)
    )
    assert response.status_code == 200, response.text
    assert response.json()["estado"] == "cancelado"


async def test_cocina_no_puede_cancelar_sin_pin_configurado(
    client: AsyncClient, db: AsyncSession, make_restaurante, make_usuario, make_categoria, make_item, make_mesa
):
    restaurante = await make_restaurante(db)
    await make_usuario(db, restaurante=restaurante, email="cocina@demo.test", password="clave123", rol=RolUsuario.COCINA)
    categoria = await make_categoria(db, restaurante=restaurante)
    item = await make_item(db, restaurante=restaurante, categoria=categoria)
    mesa = await make_mesa(db, restaurante=restaurante)
    pedido_id = await _crear_pedido(client, restaurante, item, mesa)

    token = await _login(client, "cocina@demo.test", "clave123")
    response = await client.patch(
        f"/api/staff/pedidos/{pedido_id}/estado", json={"estado": "cancelado"}, headers=_auth_headers(token)
    )
    assert response.status_code == 400


async def test_cocina_con_pin_correcto_puede_cancelar(
    client: AsyncClient, db: AsyncSession, make_restaurante, make_usuario, make_categoria, make_item, make_mesa
):
    restaurante = await make_restaurante(db)
    await make_usuario(db, restaurante=restaurante, email="admin@demo.test", password="clave123", rol=RolUsuario.ADMIN)
    await make_usuario(db, restaurante=restaurante, email="cocina@demo.test", password="clave123", rol=RolUsuario.COCINA)
    categoria = await make_categoria(db, restaurante=restaurante)
    item = await make_item(db, restaurante=restaurante, categoria=categoria)
    mesa = await make_mesa(db, restaurante=restaurante)
    pedido_id = await _crear_pedido(client, restaurante, item, mesa)

    admin_token = await _login(client, "admin@demo.test", "clave123")
    config_response = await client.patch(
        "/api/admin/restaurante", json={"pin_cancelacion": "1234"}, headers=_auth_headers(admin_token)
    )
    assert config_response.status_code == 200
    assert config_response.json()["pin_cancelacion_configurado"] is True

    cocina_token = await _login(client, "cocina@demo.test", "clave123")
    response = await client.patch(
        f"/api/staff/pedidos/{pedido_id}/estado",
        json={"estado": "cancelado", "pin": "1234"},
        headers=_auth_headers(cocina_token),
    )
    assert response.status_code == 200, response.text
    assert response.json()["estado"] == "cancelado"


async def test_cocina_con_pin_incorrecto_no_puede_cancelar(
    client: AsyncClient, db: AsyncSession, make_restaurante, make_usuario, make_categoria, make_item, make_mesa
):
    restaurante = await make_restaurante(db)
    await make_usuario(db, restaurante=restaurante, email="admin@demo.test", password="clave123", rol=RolUsuario.ADMIN)
    await make_usuario(db, restaurante=restaurante, email="cocina@demo.test", password="clave123", rol=RolUsuario.COCINA)
    categoria = await make_categoria(db, restaurante=restaurante)
    item = await make_item(db, restaurante=restaurante, categoria=categoria)
    mesa = await make_mesa(db, restaurante=restaurante)
    pedido_id = await _crear_pedido(client, restaurante, item, mesa)

    admin_token = await _login(client, "admin@demo.test", "clave123")
    await client.patch("/api/admin/restaurante", json={"pin_cancelacion": "1234"}, headers=_auth_headers(admin_token))

    cocina_token = await _login(client, "cocina@demo.test", "clave123")
    response = await client.patch(
        f"/api/staff/pedidos/{pedido_id}/estado",
        json={"estado": "cancelado", "pin": "9999"},
        headers=_auth_headers(cocina_token),
    )
    assert response.status_code == 401


async def test_no_se_puede_cancelar_pedido_listo(
    client: AsyncClient, db: AsyncSession, make_restaurante, make_usuario, make_categoria, make_item, make_mesa
):
    restaurante = await make_restaurante(db)
    await make_usuario(db, restaurante=restaurante, email="admin@demo.test", password="clave123", rol=RolUsuario.ADMIN)
    categoria = await make_categoria(db, restaurante=restaurante)
    item = await make_item(db, restaurante=restaurante, categoria=categoria)
    mesa = await make_mesa(db, restaurante=restaurante)
    pedido_id = await _crear_pedido(client, restaurante, item, mesa)

    token = await _login(client, "admin@demo.test", "clave123")
    headers = _auth_headers(token)
    for estado in ["en_cocina", "listo"]:
        await client.patch(f"/api/staff/pedidos/{pedido_id}/estado", json={"estado": estado}, headers=headers)

    response = await client.patch(
        f"/api/staff/pedidos/{pedido_id}/estado", json={"estado": "cancelado"}, headers=headers
    )
    assert response.status_code == 400


async def test_cancelar_pedido_facturado_genera_nota_credito(
    client: AsyncClient, db: AsyncSession, make_restaurante, make_usuario, make_categoria, make_item, make_mesa
):
    restaurante = await make_restaurante(db)
    await make_usuario(db, restaurante=restaurante, email="admin@demo.test", password="clave123", rol=RolUsuario.ADMIN)
    categoria = await make_categoria(db, restaurante=restaurante)
    item = await make_item(db, restaurante=restaurante, categoria=categoria, precio="10.00")
    mesa = await make_mesa(db, restaurante=restaurante)
    pedido_id = await _crear_pedido(client, restaurante, item, mesa, datos_facturacion=DATOS_FACTURACION)

    token = await _login(client, "admin@demo.test", "clave123")
    response = await client.patch(
        f"/api/staff/pedidos/{pedido_id}/estado", json={"estado": "cancelado"}, headers=_auth_headers(token)
    )
    assert response.status_code == 200, response.text

    result = await db.execute(select(NotaCredito).where(NotaCredito.pedido_id == pedido_id))
    nota = result.scalar_one_or_none()
    assert nota is not None
    assert float(nota.monto) == 10.00


async def test_cancelar_pedido_sin_factura_no_genera_nota_credito(
    client: AsyncClient, db: AsyncSession, make_restaurante, make_usuario, make_categoria, make_item, make_mesa
):
    restaurante = await make_restaurante(db)
    await make_usuario(db, restaurante=restaurante, email="admin@demo.test", password="clave123", rol=RolUsuario.ADMIN)
    categoria = await make_categoria(db, restaurante=restaurante)
    item = await make_item(db, restaurante=restaurante, categoria=categoria)
    mesa = await make_mesa(db, restaurante=restaurante)
    pedido_id = await _crear_pedido(client, restaurante, item, mesa)

    token = await _login(client, "admin@demo.test", "clave123")
    await client.patch(
        f"/api/staff/pedidos/{pedido_id}/estado", json={"estado": "cancelado"}, headers=_auth_headers(token)
    )

    result = await db.execute(select(NotaCredito).where(NotaCredito.pedido_id == pedido_id))
    assert result.scalar_one_or_none() is None
