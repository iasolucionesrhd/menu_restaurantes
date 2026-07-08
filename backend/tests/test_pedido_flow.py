from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.item import Item


async def test_crear_pedido_efectivo(
    client: AsyncClient, db: AsyncSession, make_restaurante, make_categoria, make_item, make_mesa
):
    restaurante = await make_restaurante(db)
    categoria = await make_categoria(db, restaurante=restaurante)
    item1 = await make_item(db, restaurante=restaurante, categoria=categoria, nombre="Pizza", precio="10.00")
    item2 = await make_item(db, restaurante=restaurante, categoria=categoria, nombre="Refresco", precio="2.50")
    mesa = await make_mesa(db, restaurante=restaurante, numero=1, codigo_qr="qr-mesa-1")

    response = await client.post(
        f"/api/public/{restaurante.slug}/pedidos",
        json={
            "mesa_codigo_qr": mesa.codigo_qr,
            "cliente": {"nombre": "Juan Pérez", "correo": "juan@test.com", "consentimiento_datos": True},
            "metodo_pago": "efectivo_en_restaurante",
            "items": [
                {"item_id": item1.id, "cantidad": 2, "notas": "sin cebolla"},
                {"item_id": item2.id, "cantidad": 1},
            ],
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["estado"] == "recibido"
    assert body["tilopay_transaction_id"] is None
    assert body["tipo_entrega"] == "mesa"
    assert body["mesa_numero"] == 1
    assert float(body["monto_total"]) == 22.50
    notas = {i["notas"] for i in body["items"]}
    assert "sin cebolla" in notas


async def test_precio_snapshot_no_cambia_si_item_se_actualiza(
    client: AsyncClient, db: AsyncSession, make_restaurante, make_categoria, make_item, make_mesa
):
    restaurante = await make_restaurante(db)
    categoria = await make_categoria(db, restaurante=restaurante)
    item = await make_item(db, restaurante=restaurante, categoria=categoria, nombre="Pizza", precio="10.00")
    mesa = await make_mesa(db, restaurante=restaurante)

    response = await client.post(
        f"/api/public/{restaurante.slug}/pedidos",
        json={
            "mesa_codigo_qr": mesa.codigo_qr,
            "cliente": {"nombre": "Ana"},
            "metodo_pago": "efectivo_en_restaurante",
            "items": [{"item_id": item.id, "cantidad": 1}],
        },
    )
    assert response.status_code == 201
    pedido_id = response.json()["id"]
    assert response.json()["items"][0]["precio_unitario"] == "10.00"

    item_db = await db.get(Item, item.id)
    item_db.precio = "99.00"
    await db.commit()

    consulta = await client.get(f"/api/public/{restaurante.slug}/pedidos/{pedido_id}")
    assert consulta.json()["items"][0]["precio_unitario"] == "10.00"


async def test_crear_pedido_con_pago_stub(
    client: AsyncClient, db: AsyncSession, make_restaurante, make_categoria, make_item, make_mesa
):
    restaurante = await make_restaurante(db)
    categoria = await make_categoria(db, restaurante=restaurante)
    item = await make_item(db, restaurante=restaurante, categoria=categoria, precio="5.00")
    mesa = await make_mesa(db, restaurante=restaurante)

    iniciar = await client.post(
        f"/api/public/{restaurante.slug}/pagos/iniciar",
        json={"monto": "5.00", "metodo_pago": "tarjeta", "referencia_externa": "ref-x"},
    )
    payment_intent_id = iniciar.json()["payment_intent_id"]

    response = await client.post(
        f"/api/public/{restaurante.slug}/pedidos",
        json={
            "mesa_codigo_qr": mesa.codigo_qr,
            "cliente": {"nombre": "Luis"},
            "metodo_pago": "tarjeta",
            "items": [{"item_id": item.id, "cantidad": 1}],
            "payment_intent_id": payment_intent_id,
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["estado"] == "recibido"
    assert body["tilopay_transaction_id"] == payment_intent_id


async def test_pedido_para_retirar_sin_mesa(
    client: AsyncClient, db: AsyncSession, make_restaurante, make_categoria, make_item
):
    restaurante = await make_restaurante(db)
    categoria = await make_categoria(db, restaurante=restaurante)
    item = await make_item(db, restaurante=restaurante, categoria=categoria, precio="3.00")

    response = await client.post(
        f"/api/public/{restaurante.slug}/pedidos",
        json={
            "mesa_codigo_qr": None,
            "cliente": {"nombre": "Marta"},
            "metodo_pago": "efectivo_en_restaurante",
            "items": [{"item_id": item.id, "cantidad": 1}],
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["tipo_entrega"] == "retiro"
    assert body["mesa_numero"] is None


async def test_pago_tarjeta_sin_payment_intent_id_falla(
    client: AsyncClient, db: AsyncSession, make_restaurante, make_categoria, make_item
):
    restaurante = await make_restaurante(db)
    categoria = await make_categoria(db, restaurante=restaurante)
    item = await make_item(db, restaurante=restaurante, categoria=categoria, precio="3.00")

    response = await client.post(
        f"/api/public/{restaurante.slug}/pedidos",
        json={
            "mesa_codigo_qr": None,
            "cliente": {"nombre": "Marta"},
            "metodo_pago": "tarjeta",
            "items": [{"item_id": item.id, "cantidad": 1}],
        },
    )

    assert response.status_code == 400
