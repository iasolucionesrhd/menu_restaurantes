import json

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.enums import RolUsuario
from app.models.categoria import Categoria
from app.models.item import Item
from app.models.mesa import Mesa
from app.models.modificador import Modificador
from app.models.modificador_grupo import ModificadorGrupo
from app.models.restaurante import Restaurante
from app.models.usuario import Usuario
from app.security import verify_password
from app.services.payments.base import PaymentAdapterUnavailable
from app.services.payments.stub_adapter import StubPaymentAdapter
from scripts import importar_evento as importar_evento_mod
from tests.conftest import TestSessionLocal


async def _login(client: AsyncClient, email: str, password: str) -> str:
    response = await client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def _armar_menu_completo(db: AsyncSession, make_categoria, make_item, restaurante: Restaurante):
    categoria = await make_categoria(db, restaurante=restaurante, nombre="Pizzas", orden=0)
    item = await make_item(db, restaurante=restaurante, categoria=categoria, nombre="Pizza Margarita", precio="8.50")
    grupo = ModificadorGrupo(
        restaurante_id=restaurante.id, item_id=item.id, nombre="Tamaño", obligatorio=True, seleccion_multiple=False
    )
    db.add(grupo)
    await db.flush()
    db.add(Modificador(restaurante_id=restaurante.id, grupo_id=grupo.id, nombre="Grande", precio_extra="2.00"))
    await db.commit()
    return categoria, item


async def test_exportar_datos_evento_incluye_menu_mesas_usuarios_y_credenciales(
    client: AsyncClient, db: AsyncSession, make_restaurante, make_usuario, make_categoria, make_item, make_mesa
):
    restaurante = await make_restaurante(db)
    await _armar_menu_completo(db, make_categoria, make_item, restaurante)
    await make_mesa(db, restaurante=restaurante, numero=1, codigo_qr="mesa-1")
    admin = await make_usuario(db, restaurante=restaurante, email="admin@demo.test", password="clave123", rol=RolUsuario.ADMIN)
    await make_usuario(db, restaurante=restaurante, email="cocina@demo.test", password="clave456", rol=RolUsuario.COCINA)

    restaurante_db = await db.get(Restaurante, restaurante.id)
    restaurante_db.tilopay_llave_api = "llave-secreta"
    restaurante_db.tilopay_usuario_api = "usuario-tilopay"
    restaurante_db.tilopay_password_api = "clave-tilopay"
    await db.commit()

    token = await _login(client, "admin@demo.test", "clave123")
    response = await client.get("/api/admin/sucursales/exportar-datos-evento", headers=_auth_headers(token))
    assert response.status_code == 200, response.text
    body = response.json()

    assert body["restaurante"]["slug"] == restaurante.slug
    # Las credenciales viajan en texto plano (el ORM ya las descifró al leerlas).
    assert body["restaurante"]["tilopay_llave_api"] == "llave-secreta"
    assert body["restaurante"]["tilopay_usuario_api"] == "usuario-tilopay"

    assert len(body["categorias"]) == 1
    categoria_out = body["categorias"][0]
    assert categoria_out["nombre"] == "Pizzas"
    assert len(categoria_out["items"]) == 1
    item_out = categoria_out["items"][0]
    assert item_out["nombre"] == "Pizza Margarita"
    assert len(item_out["modificador_grupos"]) == 1
    assert item_out["modificador_grupos"][0]["modificadores"][0]["nombre"] == "Grande"

    assert len(body["mesas"]) == 1
    assert body["mesas"][0]["codigo_qr"] == "mesa-1"

    emails = {u["email"] for u in body["usuarios"]}
    assert emails == {"admin@demo.test", "cocina@demo.test"}
    # La contraseña original (hash) se copia tal cual, nunca se genera una nueva.
    admin_out = next(u for u in body["usuarios"] if u["email"] == "admin@demo.test")
    assert verify_password("clave123", admin_out["password_hash"])


async def test_cocina_no_puede_exportar_datos_evento(
    client: AsyncClient, db: AsyncSession, make_restaurante, make_usuario
):
    restaurante = await make_restaurante(db)
    await make_usuario(db, restaurante=restaurante, email="cocina@demo.test", password="clave123", rol=RolUsuario.COCINA)
    token = await _login(client, "cocina@demo.test", "clave123")

    response = await client.get("/api/admin/sucursales/exportar-datos-evento", headers=_auth_headers(token))
    assert response.status_code == 403


async def test_importar_evento_reconstruye_menu_mesas_y_usuarios(
    client: AsyncClient,
    db: AsyncSession,
    make_restaurante,
    make_usuario,
    make_categoria,
    make_item,
    make_mesa,
    monkeypatch,
    tmp_path,
):
    restaurante = await make_restaurante(db, nombre="Pizzería Luna", slug="pizzeria-luna")
    await _armar_menu_completo(db, make_categoria, make_item, restaurante)
    await make_mesa(db, restaurante=restaurante, numero=1, codigo_qr="mesa-1")
    await make_usuario(db, restaurante=restaurante, email="admin@demo.test", password="clave123", rol=RolUsuario.ADMIN)

    restaurante_db = await db.get(Restaurante, restaurante.id)
    restaurante_db.tilopay_llave_api = "llave-secreta"
    await db.commit()

    token = await _login(client, "admin@demo.test", "clave123")
    export_response = await client.get("/api/admin/sucursales/exportar-datos-evento", headers=_auth_headers(token))
    assert export_response.status_code == 200
    datos = export_response.json()
    # El "nodo" de la prueba es la misma BD de test (no una Postgres aparte),
    # así que se importa bajo un slug distinto para no chocar con la sucursal
    # de origen — lo que se está probando es que el import reconstruye todo
    # a partir del JSON, no que las dos bases sean físicamente independientes.
    datos["restaurante"]["slug"] = "pizzeria-luna-nodo-evento"
    # codigo_qr es único en toda la tabla (no por sucursal); en un nodo real
    # sería una BD aparte y no habría colisión, pero aquí se reutiliza la
    # misma BD de test, así que hay que evitar chocar con la mesa de origen.
    datos["mesas"][0]["codigo_qr"] = "mesa-1-nodo-evento"
    # email también es único en toda la tabla (no por sucursal); mismo motivo.
    datos["usuarios"][0]["email"] = "admin-nodo-evento@demo.test"

    archivo = tmp_path / "evento.json"
    archivo.write_text(json.dumps(datos), encoding="utf-8")

    monkeypatch.setattr(settings, "MODO_NODO_EVENTO", True)
    # El script usa su propia AsyncSessionLocal (pensada para apuntar a la BD
    # del nodo); en la prueba se redirige a la BD de test que ya usan el resto
    # de los fixtures, para poder verificar el resultado con `db`.
    monkeypatch.setattr(importar_evento_mod, "AsyncSessionLocal", TestSessionLocal)

    await importar_evento_mod.importar_evento(str(archivo))

    result = await db.execute(select(Restaurante).where(Restaurante.slug == "pizzeria-luna-nodo-evento"))
    nodo = result.scalar_one()
    assert nodo.nombre == "Pizzería Luna"
    assert nodo.tilopay_llave_api == "llave-secreta"  # se re-cifró y descifró con el FERNET_KEY de este proceso

    categorias_result = await db.execute(select(Categoria).where(Categoria.restaurante_id == nodo.id))
    categorias = categorias_result.scalars().all()
    assert len(categorias) == 1 and categorias[0].nombre == "Pizzas"

    items_result = await db.execute(select(Item).where(Item.restaurante_id == nodo.id))
    items = items_result.scalars().all()
    assert len(items) == 1 and items[0].nombre == "Pizza Margarita"

    mesas_result = await db.execute(select(Mesa).where(Mesa.restaurante_id == nodo.id))
    mesas = mesas_result.scalars().all()
    assert len(mesas) == 1 and mesas[0].codigo_qr == "mesa-1-nodo-evento"

    usuarios_result = await db.execute(select(Usuario).where(Usuario.restaurante_id == nodo.id))
    usuario_nodo = usuarios_result.scalar_one()
    assert usuario_nodo.email == "admin-nodo-evento@demo.test"
    assert verify_password("clave123", usuario_nodo.password_hash)


async def test_importar_evento_falla_si_modo_nodo_evento_no_esta_activo(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "MODO_NODO_EVENTO", False)
    archivo = tmp_path / "evento.json"
    archivo.write_text("{}", encoding="utf-8")

    with pytest.raises(SystemExit):
        await importar_evento_mod.importar_evento(str(archivo))


async def test_pago_sin_conectividad_devuelve_503_no_500(
    client: AsyncClient, db: AsyncSession, make_restaurante, make_categoria, make_item, make_mesa, monkeypatch
):
    restaurante = await make_restaurante(db)
    categoria = await make_categoria(db, restaurante=restaurante)
    item = await make_item(db, restaurante=restaurante, categoria=categoria, precio="5.00")
    mesa = await make_mesa(db, restaurante=restaurante)

    async def _verificar_no_disponible(self, *, restaurante, payment_intent_id, transaction_reference=None):
        raise PaymentAdapterUnavailable("sin red")

    monkeypatch.setattr(StubPaymentAdapter, "verificar_transaccion", _verificar_no_disponible)

    response = await client.post(
        f"/api/public/{restaurante.slug}/pedidos",
        json={
            "mesa_codigo_qr": mesa.codigo_qr,
            "cliente": {"nombre": "Cliente Test", "consentimiento_datos": True},
            "metodo_pago": "tarjeta",
            "payment_intent_id": "pi_1",
            "items": [{"item_id": item.id, "cantidad": 1}],
        },
    )
    assert response.status_code == 503
    assert "efectivo" in response.json()["detail"].lower()
