import asyncio
import secrets

from sqlalchemy import select

from app.config import settings
from app.database import AsyncSessionLocal
from app.enums import RolUsuario
from app.models.categoria import Categoria
from app.models.item import Item
from app.models.mesa import Mesa
from app.models.restaurante import Restaurante
from app.models.usuario import Usuario
from app.security import hash_password
from app.services.qr_service import mesa_public_url

DEMO_SLUG = "pizzeria-luna"

CATEGORIAS_DEMO = [
    ("Pizzas", 0, [
        ("Pizza Margarita", "Salsa de tomate, mozzarella y albahaca", "8.50"),
        ("Pizza Pepperoni", "Salsa de tomate, mozzarella y pepperoni", "9.50"),
        ("Pizza Hawaiana", "Jamón, piña y mozzarella", "9.00"),
    ]),
    ("Bebidas", 1, [
        ("Refresco natural", "Fresa, mora o cas", "2.00"),
        ("Gaseosa", "Lata 355ml", "1.50"),
        ("Agua embotellada", "500ml", "1.00"),
    ]),
    ("Postres", 2, [
        ("Tres leches", "Porción individual", "3.50"),
        ("Flan de caramelo", "Porción individual", "3.00"),
    ]),
]


async def seed() -> None:
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Restaurante).where(Restaurante.slug == DEMO_SLUG))
        restaurante = result.scalar_one_or_none()

        if restaurante is not None:
            print(f"El restaurante demo '{DEMO_SLUG}' ya existe, no se vuelve a sembrar.")
            return

        restaurante = Restaurante(nombre="Pizzería Luna", slug=DEMO_SLUG)
        db.add(restaurante)
        await db.flush()

        admin = Usuario(
            restaurante_id=restaurante.id,
            email=f"admin@{DEMO_SLUG}.demo",
            password_hash=hash_password(settings.SEED_ADMIN_PASSWORD),
            rol=RolUsuario.ADMIN,
        )
        cocina = Usuario(
            restaurante_id=restaurante.id,
            email=f"cocina@{DEMO_SLUG}.demo",
            password_hash=hash_password(settings.SEED_ADMIN_PASSWORD),
            rol=RolUsuario.COCINA,
        )
        db.add_all([admin, cocina])

        for nombre_cat, orden, items in CATEGORIAS_DEMO:
            categoria = Categoria(restaurante_id=restaurante.id, nombre=nombre_cat, orden=orden)
            db.add(categoria)
            await db.flush()
            for nombre_item, descripcion, precio in items:
                db.add(
                    Item(
                        restaurante_id=restaurante.id,
                        categoria_id=categoria.id,
                        nombre=nombre_item,
                        descripcion=descripcion,
                        precio=precio,
                    )
                )

        mesas = [
            Mesa(restaurante_id=restaurante.id, numero=1, codigo_qr=secrets.token_urlsafe(8)),
            Mesa(restaurante_id=restaurante.id, numero=2, codigo_qr=secrets.token_urlsafe(8)),
            Mesa(restaurante_id=restaurante.id, numero=None, codigo_qr=secrets.token_urlsafe(8)),
        ]
        db.add_all(mesas)

        await db.commit()

        print("Restaurante demo creado:")
        print(f"  Admin:  admin@{DEMO_SLUG}.demo / {settings.SEED_ADMIN_PASSWORD}")
        print(f"  Cocina: cocina@{DEMO_SLUG}.demo / {settings.SEED_ADMIN_PASSWORD}")
        print("URLs de mesa:")
        for mesa in mesas:
            etiqueta = f"mesa {mesa.numero}" if mesa.numero is not None else "para retirar"
            print(f"  {etiqueta}: {mesa_public_url(restaurante, mesa)}")


if __name__ == "__main__":
    asyncio.run(seed())
