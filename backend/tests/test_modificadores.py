from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.enums import RolUsuario


async def _login(client: AsyncClient, email: str, password: str) -> str:
    response = await client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def _crear_grupo_y_modificadores(
    client: AsyncClient, headers: dict, item_id: int
) -> tuple[int, int, int]:
    """Crea un grupo 'Tamaño' (única, obligatorio) con dos opciones. Retorna (grupo_id, id_chico, id_grande)."""
    grupo_resp = await client.post(
        f"/api/admin/items/{item_id}/modificador-grupos",
        json={"nombre": "Tamaño", "obligatorio": True, "seleccion_multiple": False},
        headers=headers,
    )
    assert grupo_resp.status_code == 201, grupo_resp.text
    grupo_id = grupo_resp.json()["id"]

    chico_resp = await client.post(
        f"/api/admin/modificador-grupos/{grupo_id}/modificadores",
        json={"nombre": "Chico", "precio_extra": "0"},
        headers=headers,
    )
    grande_resp = await client.post(
        f"/api/admin/modificador-grupos/{grupo_id}/modificadores",
        json={"nombre": "Grande", "precio_extra": "2.00"},
        headers=headers,
    )
    assert chico_resp.status_code == 201
    assert grande_resp.status_code == 201
    return grupo_id, chico_resp.json()["id"], grande_resp.json()["id"]


async def _crear_pedido(client: AsyncClient, restaurante, item, mesa, modificador_ids: list[int]) -> dict:
    response = await client.post(
        f"/api/public/{restaurante.slug}/pedidos",
        json={
            "mesa_codigo_qr": mesa.codigo_qr,
            "cliente": {"nombre": "Cliente Test", "consentimiento_datos": True},
            "metodo_pago": "efectivo_en_restaurante",
            "items": [{"item_id": item.id, "cantidad": 1, "modificador_ids": modificador_ids}],
        },
    )
    return response


async def test_admin_puede_crear_grupo_y_modificadores(
    client: AsyncClient, db: AsyncSession, make_restaurante, make_usuario, make_categoria, make_item
):
    restaurante = await make_restaurante(db)
    await make_usuario(db, restaurante=restaurante, email="admin@demo.test", password="clave123", rol=RolUsuario.ADMIN)
    categoria = await make_categoria(db, restaurante=restaurante)
    item = await make_item(db, restaurante=restaurante, categoria=categoria)
    token = await _login(client, "admin@demo.test", "clave123")

    grupo_id, chico_id, grande_id = await _crear_grupo_y_modificadores(client, _auth_headers(token), item.id)

    response = await client.get("/api/admin/items", headers=_auth_headers(token))
    assert response.status_code == 200
    item_out = next(i for i in response.json() if i["id"] == item.id)
    assert len(item_out["modificador_grupos"]) == 1
    grupo = item_out["modificador_grupos"][0]
    assert grupo["nombre"] == "Tamaño"
    assert grupo["obligatorio"] is True
    assert {m["nombre"] for m in grupo["modificadores"]} == {"Chico", "Grande"}


async def test_pedido_con_modificador_suma_precio_extra(
    client: AsyncClient,
    db: AsyncSession,
    make_restaurante,
    make_usuario,
    make_categoria,
    make_item,
    make_mesa,
):
    restaurante = await make_restaurante(db)
    await make_usuario(db, restaurante=restaurante, email="admin@demo.test", password="clave123", rol=RolUsuario.ADMIN)
    categoria = await make_categoria(db, restaurante=restaurante)
    item = await make_item(db, restaurante=restaurante, categoria=categoria, precio="10.00")
    mesa = await make_mesa(db, restaurante=restaurante)
    token = await _login(client, "admin@demo.test", "clave123")

    _, chico_id, grande_id = await _crear_grupo_y_modificadores(client, _auth_headers(token), item.id)

    response = await _crear_pedido(client, restaurante, item, mesa, [grande_id])
    assert response.status_code == 201, response.text
    body = response.json()
    assert float(body["monto_total"]) == 12.00
    assert body["items"][0]["modificadores"] == [{"nombre": "Grande", "precio_extra": "2.00"}]


async def test_pedido_sin_seleccionar_grupo_obligatorio_falla(
    client: AsyncClient,
    db: AsyncSession,
    make_restaurante,
    make_usuario,
    make_categoria,
    make_item,
    make_mesa,
):
    restaurante = await make_restaurante(db)
    await make_usuario(db, restaurante=restaurante, email="admin@demo.test", password="clave123", rol=RolUsuario.ADMIN)
    categoria = await make_categoria(db, restaurante=restaurante)
    item = await make_item(db, restaurante=restaurante, categoria=categoria, precio="10.00")
    mesa = await make_mesa(db, restaurante=restaurante)
    token = await _login(client, "admin@demo.test", "clave123")

    await _crear_grupo_y_modificadores(client, _auth_headers(token), item.id)

    response = await _crear_pedido(client, restaurante, item, mesa, [])
    assert response.status_code == 400


async def test_pedido_con_dos_opciones_de_grupo_unico_falla(
    client: AsyncClient,
    db: AsyncSession,
    make_restaurante,
    make_usuario,
    make_categoria,
    make_item,
    make_mesa,
):
    restaurante = await make_restaurante(db)
    await make_usuario(db, restaurante=restaurante, email="admin@demo.test", password="clave123", rol=RolUsuario.ADMIN)
    categoria = await make_categoria(db, restaurante=restaurante)
    item = await make_item(db, restaurante=restaurante, categoria=categoria, precio="10.00")
    mesa = await make_mesa(db, restaurante=restaurante)
    token = await _login(client, "admin@demo.test", "clave123")

    _, chico_id, grande_id = await _crear_grupo_y_modificadores(client, _auth_headers(token), item.id)

    response = await _crear_pedido(client, restaurante, item, mesa, [chico_id, grande_id])
    assert response.status_code == 400


async def test_pedido_con_modificador_de_otro_item_falla(
    client: AsyncClient,
    db: AsyncSession,
    make_restaurante,
    make_usuario,
    make_categoria,
    make_item,
    make_mesa,
):
    restaurante = await make_restaurante(db)
    await make_usuario(db, restaurante=restaurante, email="admin@demo.test", password="clave123", rol=RolUsuario.ADMIN)
    categoria = await make_categoria(db, restaurante=restaurante)
    item_a = await make_item(db, restaurante=restaurante, categoria=categoria, nombre="Item A", precio="10.00")
    item_b = await make_item(db, restaurante=restaurante, categoria=categoria, nombre="Item B", precio="5.00")
    mesa = await make_mesa(db, restaurante=restaurante)
    token = await _login(client, "admin@demo.test", "clave123")

    _, chico_id_a, grande_id_a = await _crear_grupo_y_modificadores(client, _auth_headers(token), item_a.id)

    response = await _crear_pedido(client, restaurante, item_b, mesa, [grande_id_a])
    assert response.status_code == 400


async def test_grupo_opcional_permite_no_seleccionar(
    client: AsyncClient,
    db: AsyncSession,
    make_restaurante,
    make_usuario,
    make_categoria,
    make_item,
    make_mesa,
):
    restaurante = await make_restaurante(db)
    await make_usuario(db, restaurante=restaurante, email="admin@demo.test", password="clave123", rol=RolUsuario.ADMIN)
    categoria = await make_categoria(db, restaurante=restaurante)
    item = await make_item(db, restaurante=restaurante, categoria=categoria, precio="10.00")
    mesa = await make_mesa(db, restaurante=restaurante)
    token = await _login(client, "admin@demo.test", "clave123")

    grupo_resp = await client.post(
        f"/api/admin/items/{item.id}/modificador-grupos",
        json={"nombre": "Extras", "obligatorio": False, "seleccion_multiple": True},
        headers=_auth_headers(token),
    )
    grupo_id = grupo_resp.json()["id"]
    queso_resp = await client.post(
        f"/api/admin/modificador-grupos/{grupo_id}/modificadores",
        json={"nombre": "Queso extra", "precio_extra": "1.50"},
        headers=_auth_headers(token),
    )
    tocino_resp = await client.post(
        f"/api/admin/modificador-grupos/{grupo_id}/modificadores",
        json={"nombre": "Tocino", "precio_extra": "2.50"},
        headers=_auth_headers(token),
    )
    queso_id = queso_resp.json()["id"]
    tocino_id = tocino_resp.json()["id"]

    sin_seleccion = await _crear_pedido(client, restaurante, item, mesa, [])
    assert sin_seleccion.status_code == 201
    assert float(sin_seleccion.json()["monto_total"]) == 10.00

    con_ambos = await _crear_pedido(client, restaurante, item, mesa, [queso_id, tocino_id])
    assert con_ambos.status_code == 201, con_ambos.text
    assert float(con_ambos.json()["monto_total"]) == 14.00
    nombres = {m["nombre"] for m in con_ambos.json()["items"][0]["modificadores"]}
    assert nombres == {"Queso extra", "Tocino"}
