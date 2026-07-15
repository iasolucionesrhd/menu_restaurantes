import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cliente import Cliente
from app.models.pedido import Pedido
from app.services.google_auth import GoogleUserInfo


def _mock_verify(monkeypatch: pytest.MonkeyPatch, subs_por_token: dict[str, str]):
    """Mockea verify_google_id_token para que cada token en subs_por_token
    devuelva un GoogleUserInfo determinístico. El patch va sobre el módulo
    que CONSUME la función (pedido_service), no sobre google_auth donde se
    define, porque el import ya vinculó el nombre en ese namespace."""

    async def fake_verify(token: str) -> GoogleUserInfo:
        if token not in subs_por_token:
            from fastapi import HTTPException, status

            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token de Google inválido")
        sub = subs_por_token[token]
        return GoogleUserInfo(sub=sub, email=f"{sub}@gmail.test", nombre=f"Usuario {sub}")

    monkeypatch.setattr("app.services.pedido_service.verify_google_id_token", fake_verify)


def _pedido_payload(mesa_codigo_qr, item_id, google_id_token=None, consentimiento_datos=True):
    return {
        "mesa_codigo_qr": mesa_codigo_qr,
        "cliente": {
            "nombre": "Cliente Google",
            "consentimiento_datos": consentimiento_datos,
            **({"google_id_token": google_id_token} if google_id_token else {}),
        },
        "metodo_pago": "efectivo_en_restaurante",
        "items": [{"item_id": item_id, "cantidad": 1}],
    }


async def test_primer_pedido_con_google_crea_cliente_con_google_sub(
    client: AsyncClient, db: AsyncSession, make_restaurante, make_categoria, make_item, make_mesa, monkeypatch
):
    _mock_verify(monkeypatch, {"tok-1": "sub-1"})
    restaurante = await make_restaurante(db)
    categoria = await make_categoria(db, restaurante=restaurante)
    item = await make_item(db, restaurante=restaurante, categoria=categoria)
    mesa = await make_mesa(db, restaurante=restaurante)

    response = await client.post(
        f"/api/public/{restaurante.slug}/pedidos",
        json=_pedido_payload(mesa.codigo_qr, item.id, google_id_token="tok-1"),
    )
    assert response.status_code == 201

    result = await db.execute(select(Cliente).where(Cliente.restaurante_id == restaurante.id))
    clientes = result.scalars().all()
    assert len(clientes) == 1
    assert clientes[0].google_sub == "sub-1"
    assert clientes[0].correo == "sub-1@gmail.test"


async def test_segundo_pedido_mismo_sub_reusa_cliente(
    client: AsyncClient, db: AsyncSession, make_restaurante, make_categoria, make_item, make_mesa, monkeypatch
):
    _mock_verify(monkeypatch, {"tok-1": "sub-1"})
    restaurante = await make_restaurante(db)
    categoria = await make_categoria(db, restaurante=restaurante)
    item = await make_item(db, restaurante=restaurante, categoria=categoria)
    mesa = await make_mesa(db, restaurante=restaurante)

    r1 = await client.post(
        f"/api/public/{restaurante.slug}/pedidos",
        json=_pedido_payload(mesa.codigo_qr, item.id, google_id_token="tok-1"),
    )
    r2 = await client.post(
        f"/api/public/{restaurante.slug}/pedidos",
        json=_pedido_payload(mesa.codigo_qr, item.id, google_id_token="tok-1"),
    )
    assert r1.status_code == 201
    assert r2.status_code == 201

    pedido1 = await db.get(Pedido, r1.json()["id"])
    pedido2 = await db.get(Pedido, r2.json()["id"])
    assert pedido1.cliente_id == pedido2.cliente_id

    result = await db.execute(select(Cliente).where(Cliente.restaurante_id == restaurante.id))
    assert len(result.scalars().all()) == 1


async def test_mismo_sub_en_restaurantes_distintos_no_se_mezcla(
    client: AsyncClient, db: AsyncSession, make_restaurante, make_categoria, make_item, make_mesa, monkeypatch
):
    _mock_verify(monkeypatch, {"tok-1": "sub-1"})
    restaurante_a = await make_restaurante(db, nombre="Restaurante A", slug="restaurante-a")
    restaurante_b = await make_restaurante(db, nombre="Restaurante B", slug="restaurante-b")
    categoria_a = await make_categoria(db, restaurante=restaurante_a)
    categoria_b = await make_categoria(db, restaurante=restaurante_b)
    item_a = await make_item(db, restaurante=restaurante_a, categoria=categoria_a)
    item_b = await make_item(db, restaurante=restaurante_b, categoria=categoria_b)
    mesa_a = await make_mesa(db, restaurante=restaurante_a, codigo_qr="qr-a")
    mesa_b = await make_mesa(db, restaurante=restaurante_b, codigo_qr="qr-b")

    r1 = await client.post(
        f"/api/public/{restaurante_a.slug}/pedidos",
        json=_pedido_payload(mesa_a.codigo_qr, item_a.id, google_id_token="tok-1"),
    )
    r2 = await client.post(
        f"/api/public/{restaurante_b.slug}/pedidos",
        json=_pedido_payload(mesa_b.codigo_qr, item_b.id, google_id_token="tok-1"),
    )
    assert r1.status_code == 201
    assert r2.status_code == 201

    pedido1 = await db.get(Pedido, r1.json()["id"])
    pedido2 = await db.get(Pedido, r2.json()["id"])
    assert pedido1.cliente_id != pedido2.cliente_id

    cliente1 = await db.get(Cliente, pedido1.cliente_id)
    cliente2 = await db.get(Cliente, pedido2.cliente_id)
    assert cliente1.restaurante_id == restaurante_a.id
    assert cliente2.restaurante_id == restaurante_b.id
    assert cliente1.google_sub == cliente2.google_sub == "sub-1"


async def test_subs_distintos_mismo_restaurante_crean_clientes_separados(
    client: AsyncClient, db: AsyncSession, make_restaurante, make_categoria, make_item, make_mesa, monkeypatch
):
    _mock_verify(monkeypatch, {"tok-1": "sub-1", "tok-2": "sub-2"})
    restaurante = await make_restaurante(db)
    categoria = await make_categoria(db, restaurante=restaurante)
    item = await make_item(db, restaurante=restaurante, categoria=categoria)
    mesa = await make_mesa(db, restaurante=restaurante)

    r1 = await client.post(
        f"/api/public/{restaurante.slug}/pedidos",
        json=_pedido_payload(mesa.codigo_qr, item.id, google_id_token="tok-1"),
    )
    r2 = await client.post(
        f"/api/public/{restaurante.slug}/pedidos",
        json=_pedido_payload(mesa.codigo_qr, item.id, google_id_token="tok-2"),
    )
    assert r1.status_code == 201
    assert r2.status_code == 201

    result = await db.execute(select(Cliente).where(Cliente.restaurante_id == restaurante.id))
    assert len(result.scalars().all()) == 2


async def test_token_invalido_devuelve_401_y_no_crea_nada(
    client: AsyncClient, db: AsyncSession, make_restaurante, make_categoria, make_item, make_mesa, monkeypatch
):
    _mock_verify(monkeypatch, {})  # ningún token es válido
    restaurante = await make_restaurante(db)
    categoria = await make_categoria(db, restaurante=restaurante)
    item = await make_item(db, restaurante=restaurante, categoria=categoria)
    mesa = await make_mesa(db, restaurante=restaurante)

    response = await client.post(
        f"/api/public/{restaurante.slug}/pedidos",
        json=_pedido_payload(mesa.codigo_qr, item.id, google_id_token="tok-invalido"),
    )
    assert response.status_code == 401

    clientes = await db.execute(select(Cliente).where(Cliente.restaurante_id == restaurante.id))
    pedidos = await db.execute(select(Pedido).where(Pedido.restaurante_id == restaurante.id))
    assert clientes.scalars().all() == []
    assert pedidos.scalars().all() == []


async def test_google_id_token_sin_google_client_id_configurado_devuelve_400(
    client: AsyncClient, db: AsyncSession, make_restaurante, make_categoria, make_item, make_mesa, monkeypatch
):
    # No se mockea verify_google_id_token: se ejercita la función real. Se
    # fuerza GOOGLE_CLIENT_ID a None explícitamente (en vez de asumir que el
    # entorno de test no lo trae configurado) para no depender de si hay o
    # no credenciales reales cargadas en el .env de esta máquina.
    from app.services.google_auth import settings as google_auth_settings

    monkeypatch.setattr(google_auth_settings, "GOOGLE_CLIENT_ID", None)

    restaurante = await make_restaurante(db)
    categoria = await make_categoria(db, restaurante=restaurante)
    item = await make_item(db, restaurante=restaurante, categoria=categoria)
    mesa = await make_mesa(db, restaurante=restaurante)

    response = await client.post(
        f"/api/public/{restaurante.slug}/pedidos",
        json=_pedido_payload(mesa.codigo_qr, item.id, google_id_token="cualquier-token"),
    )
    assert response.status_code == 400


async def test_checkout_invitado_sigue_creando_cliente_nuevo_cada_vez(
    client: AsyncClient, db: AsyncSession, make_restaurante, make_categoria, make_item, make_mesa
):
    restaurante = await make_restaurante(db)
    categoria = await make_categoria(db, restaurante=restaurante)
    item = await make_item(db, restaurante=restaurante, categoria=categoria)
    mesa = await make_mesa(db, restaurante=restaurante)

    payload = {
        "mesa_codigo_qr": mesa.codigo_qr,
        "cliente": {"nombre": "Invitado", "correo": "mismo@correo.test", "consentimiento_datos": True},
        "metodo_pago": "efectivo_en_restaurante",
        "items": [{"item_id": item.id, "cantidad": 1}],
    }
    r1 = await client.post(f"/api/public/{restaurante.slug}/pedidos", json=payload)
    r2 = await client.post(f"/api/public/{restaurante.slug}/pedidos", json=payload)
    assert r1.status_code == 201
    assert r2.status_code == 201

    result = await db.execute(select(Cliente).where(Cliente.restaurante_id == restaurante.id))
    assert len(result.scalars().all()) == 2


async def test_consentimiento_se_actualiza_al_reusar_cliente_google(
    client: AsyncClient, db: AsyncSession, make_restaurante, make_categoria, make_item, make_mesa, monkeypatch
):
    _mock_verify(monkeypatch, {"tok-1": "sub-1"})
    restaurante = await make_restaurante(db)
    categoria = await make_categoria(db, restaurante=restaurante)
    item = await make_item(db, restaurante=restaurante, categoria=categoria)
    mesa = await make_mesa(db, restaurante=restaurante)

    r1 = await client.post(
        f"/api/public/{restaurante.slug}/pedidos",
        json=_pedido_payload(mesa.codigo_qr, item.id, google_id_token="tok-1", consentimiento_datos=True),
    )
    assert r1.status_code == 201

    r2 = await client.post(
        f"/api/public/{restaurante.slug}/pedidos",
        json=_pedido_payload(mesa.codigo_qr, item.id, google_id_token="tok-1", consentimiento_datos=False),
    )
    assert r2.status_code == 201

    result = await db.execute(select(Cliente).where(Cliente.restaurante_id == restaurante.id))
    cliente = result.scalar_one()
    assert cliente.consentimiento_datos is False
