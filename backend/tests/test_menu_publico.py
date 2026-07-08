from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


async def test_unavailable_items_never_appear(
    client: AsyncClient, db: AsyncSession, make_restaurante, make_categoria, make_item
):
    restaurante = await make_restaurante(db)
    categoria = await make_categoria(db, restaurante=restaurante)
    await make_item(db, restaurante=restaurante, categoria=categoria, nombre="Disponible", disponible=True)
    await make_item(db, restaurante=restaurante, categoria=categoria, nombre="No disponible", disponible=False)

    response = await client.get(f"/api/public/{restaurante.slug}/menu")

    assert response.status_code == 200
    body = response.json()
    nombres = {item["nombre"] for cat in body["categorias"] for item in cat["items"]}
    assert nombres == {"Disponible"}


async def test_invalid_slug_returns_404(client: AsyncClient):
    response = await client.get("/api/public/no-existe/menu")
    assert response.status_code == 404


async def test_mesa_qr_from_other_restaurante_returns_404(
    client: AsyncClient, db: AsyncSession, make_restaurante, make_mesa
):
    restaurante_a = await make_restaurante(db, nombre="A", slug="restaurante-a")
    restaurante_b = await make_restaurante(db, nombre="B", slug="restaurante-b")
    mesa_b = await make_mesa(db, restaurante=restaurante_b, numero=3, codigo_qr="codigo-b-3")

    response = await client.get(f"/api/public/{restaurante_a.slug}/mesa/{mesa_b.codigo_qr}")

    assert response.status_code == 404


async def test_mesa_sin_numero_es_para_retirar(
    client: AsyncClient, db: AsyncSession, make_restaurante, make_mesa
):
    restaurante = await make_restaurante(db)
    mesa = await make_mesa(db, restaurante=restaurante, numero=None, codigo_qr="codigo-retiro")

    response = await client.get(f"/api/public/{restaurante.slug}/mesa/{mesa.codigo_qr}")

    assert response.status_code == 200
    assert response.json() == {"numero": None, "tipo_entrega": "retiro"}
