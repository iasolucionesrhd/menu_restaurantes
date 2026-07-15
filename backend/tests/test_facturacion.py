import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cliente import Cliente
from app.models.pedido import Pedido
from app.services.google_auth import GoogleUserInfo


def _mock_verify(monkeypatch: pytest.MonkeyPatch, subs_por_token: dict[str, str]):
    async def fake_verify(token: str) -> GoogleUserInfo:
        if token not in subs_por_token:
            from fastapi import HTTPException, status

            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token de Google inválido")
        sub = subs_por_token[token]
        return GoogleUserInfo(sub=sub, email=f"{sub}@gmail.test", nombre=f"Usuario {sub}")

    # Cada módulo que hace "from app.services.google_auth import
    # verify_google_id_token" se lleva su propia referencia vinculada al
    # namespace local — hay que parchear cada consumidor por separado, no
    # el módulo donde se define.
    monkeypatch.setattr("app.services.pedido_service.verify_google_id_token", fake_verify)
    monkeypatch.setattr("app.routers.clientes_publico.verify_google_id_token", fake_verify)


DATOS_FACTURACION = {
    "nombre": "Empresa Prueba SA",
    "cedula": "3-101-123456",
    "correo": "facturas@empresa.test",
    "telefono": "22334455",
    "direccion": "San José, Costa Rica",
    "actividad_economica": "620100",
}


def _pedido_payload(mesa_codigo_qr, item_id, google_id_token=None, datos_facturacion=None):
    cliente = {"nombre": "Cliente Prueba", "consentimiento_datos": True}
    if google_id_token:
        cliente["google_id_token"] = google_id_token
    if datos_facturacion is not None:
        cliente["datos_facturacion"] = datos_facturacion
    return {
        "mesa_codigo_qr": mesa_codigo_qr,
        "cliente": cliente,
        "metodo_pago": "efectivo_en_restaurante",
        "items": [{"item_id": item_id, "cantidad": 1}],
    }


async def test_pedido_con_factura_guarda_snapshot_y_perfil(
    client: AsyncClient, db: AsyncSession, make_restaurante, make_categoria, make_item, make_mesa
):
    restaurante = await make_restaurante(db)
    categoria = await make_categoria(db, restaurante=restaurante)
    item = await make_item(db, restaurante=restaurante, categoria=categoria)
    mesa = await make_mesa(db, restaurante=restaurante)

    response = await client.post(
        f"/api/public/{restaurante.slug}/pedidos",
        json=_pedido_payload(mesa.codigo_qr, item.id, datos_facturacion=DATOS_FACTURACION),
    )
    assert response.status_code == 201
    body = response.json()
    assert body["requiere_factura"] is True
    assert body["factura_nombre"] == DATOS_FACTURACION["nombre"]
    assert body["factura_cedula"] == DATOS_FACTURACION["cedula"]
    assert body["factura_actividad_economica"] == DATOS_FACTURACION["actividad_economica"]

    pedido_db = await db.get(Pedido, body["id"])
    assert pedido_db.requiere_factura is True
    assert pedido_db.factura_direccion == DATOS_FACTURACION["direccion"]

    cliente_db = await db.get(Cliente, pedido_db.cliente_id)
    assert cliente_db.factura_cedula == DATOS_FACTURACION["cedula"]
    assert cliente_db.factura_correo == DATOS_FACTURACION["correo"]


async def test_pedido_sin_factura_no_cambia_nada(
    client: AsyncClient, db: AsyncSession, make_restaurante, make_categoria, make_item, make_mesa
):
    restaurante = await make_restaurante(db)
    categoria = await make_categoria(db, restaurante=restaurante)
    item = await make_item(db, restaurante=restaurante, categoria=categoria)
    mesa = await make_mesa(db, restaurante=restaurante)

    response = await client.post(
        f"/api/public/{restaurante.slug}/pedidos",
        json=_pedido_payload(mesa.codigo_qr, item.id),
    )
    assert response.status_code == 201
    body = response.json()
    assert body["requiere_factura"] is False
    assert body["factura_nombre"] is None
    assert body["factura_cedula"] is None

    pedido_db = await db.get(Pedido, body["id"])
    cliente_db = await db.get(Cliente, pedido_db.cliente_id)
    assert cliente_db.factura_cedula is None


async def test_perfil_devuelve_datos_facturacion_guardados(
    client: AsyncClient, db: AsyncSession, make_restaurante, make_categoria, make_item, make_mesa, monkeypatch
):
    _mock_verify(monkeypatch, {"tok-1": "sub-1"})
    restaurante = await make_restaurante(db)
    categoria = await make_categoria(db, restaurante=restaurante)
    item = await make_item(db, restaurante=restaurante, categoria=categoria)
    mesa = await make_mesa(db, restaurante=restaurante)

    await client.post(
        f"/api/public/{restaurante.slug}/pedidos",
        json=_pedido_payload(mesa.codigo_qr, item.id, google_id_token="tok-1", datos_facturacion=DATOS_FACTURACION),
    )

    response = await client.post(
        f"/api/public/{restaurante.slug}/cliente/perfil",
        json={"google_id_token": "tok-1"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["factura_cedula"] == DATOS_FACTURACION["cedula"]
    assert body["factura_nombre"] == DATOS_FACTURACION["nombre"]


async def test_perfil_cliente_existente_sin_factura_da_200_con_campos_null(
    client: AsyncClient, db: AsyncSession, make_restaurante, make_categoria, make_item, make_mesa, monkeypatch
):
    _mock_verify(monkeypatch, {"tok-1": "sub-1"})
    restaurante = await make_restaurante(db)
    categoria = await make_categoria(db, restaurante=restaurante)
    item = await make_item(db, restaurante=restaurante, categoria=categoria)
    mesa = await make_mesa(db, restaurante=restaurante)

    await client.post(
        f"/api/public/{restaurante.slug}/pedidos",
        json=_pedido_payload(mesa.codigo_qr, item.id, google_id_token="tok-1"),
    )

    response = await client.post(
        f"/api/public/{restaurante.slug}/cliente/perfil",
        json={"google_id_token": "tok-1"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["nombre"] == "Cliente Prueba"
    assert body["factura_cedula"] is None
    assert body["factura_nombre"] is None


async def test_perfil_sin_cliente_previo_da_404(
    client: AsyncClient, db: AsyncSession, make_restaurante, monkeypatch
):
    _mock_verify(monkeypatch, {"tok-1": "sub-nunca-pidio"})
    restaurante = await make_restaurante(db)

    response = await client.post(
        f"/api/public/{restaurante.slug}/cliente/perfil",
        json={"google_id_token": "tok-1"},
    )
    assert response.status_code == 404


async def test_perfil_no_se_mezcla_entre_restaurantes(
    client: AsyncClient, db: AsyncSession, make_restaurante, make_categoria, make_item, make_mesa, monkeypatch
):
    _mock_verify(monkeypatch, {"tok-1": "sub-1"})
    restaurante_a = await make_restaurante(db, nombre="Restaurante A", slug="restaurante-a")
    restaurante_b = await make_restaurante(db, nombre="Restaurante B", slug="restaurante-b")
    categoria_a = await make_categoria(db, restaurante=restaurante_a)
    item_a = await make_item(db, restaurante=restaurante_a, categoria=categoria_a)
    mesa_a = await make_mesa(db, restaurante=restaurante_a, codigo_qr="qr-a")

    await client.post(
        f"/api/public/{restaurante_a.slug}/pedidos",
        json=_pedido_payload(mesa_a.codigo_qr, item_a.id, google_id_token="tok-1", datos_facturacion=DATOS_FACTURACION),
    )

    respuesta_a = await client.post(
        f"/api/public/{restaurante_a.slug}/cliente/perfil", json={"google_id_token": "tok-1"}
    )
    respuesta_b = await client.post(
        f"/api/public/{restaurante_b.slug}/cliente/perfil", json={"google_id_token": "tok-1"}
    )
    assert respuesta_a.status_code == 200
    assert respuesta_a.json()["factura_cedula"] == DATOS_FACTURACION["cedula"]
    assert respuesta_b.status_code == 404


async def test_datos_facturacion_con_campos_en_blanco_falla_validacion(
    client: AsyncClient, db: AsyncSession, make_restaurante, make_categoria, make_item, make_mesa
):
    restaurante = await make_restaurante(db)
    categoria = await make_categoria(db, restaurante=restaurante)
    item = await make_item(db, restaurante=restaurante, categoria=categoria)
    mesa = await make_mesa(db, restaurante=restaurante)

    datos_invalidos = {**DATOS_FACTURACION, "nombre": "   "}
    response = await client.post(
        f"/api/public/{restaurante.slug}/pedidos",
        json=_pedido_payload(mesa.codigo_qr, item.id, datos_facturacion=datos_invalidos),
    )
    assert response.status_code == 422

    result = await db.execute(select(Pedido).where(Pedido.restaurante_id == restaurante.id))
    assert result.scalars().all() == []
