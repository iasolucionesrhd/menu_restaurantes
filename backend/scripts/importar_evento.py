import argparse
import asyncio
import json
import sys

from sqlalchemy import select

from app.config import settings
from app.database import AsyncSessionLocal
from app.enums import RolUsuario
from app.models.categoria import Categoria
from app.models.item import Item
from app.models.mesa import Mesa
from app.models.modificador import Modificador
from app.models.modificador_grupo import ModificadorGrupo
from app.models.restaurante import Restaurante
from app.models.usuario import Usuario


async def importar_evento(ruta_json: str) -> None:
    if not settings.MODO_NODO_EVENTO:
        print("MODO_NODO_EVENTO no está activo en este backend — este script solo debe correrse en un nodo de evento.")
        sys.exit(1)

    with open(ruta_json, encoding="utf-8") as f:
        datos = json.load(f)

    async with AsyncSessionLocal() as db:
        slug = datos["restaurante"]["slug"]
        result = await db.execute(select(Restaurante).where(Restaurante.slug == slug))
        if result.scalar_one_or_none() is not None:
            print(f"Ya existe una sucursal '{slug}' en este nodo, no se vuelve a importar.")
            return

        r = datos["restaurante"]
        restaurante = Restaurante(
            nombre=r["nombre"],
            slug=r["slug"],
            pin_cancelacion_hash=r["pin_cancelacion_hash"],
            # Se re-cifran solas al asignarlas (EncryptedString usa el
            # FERNET_KEY de esta instancia, no el de donde se exportaron).
            tilopay_llave_api=r["tilopay_llave_api"],
            tilopay_usuario_api=r["tilopay_usuario_api"],
            tilopay_password_api=r["tilopay_password_api"],
        )
        db.add(restaurante)
        await db.flush()

        for u in datos["usuarios"]:
            db.add(
                Usuario(
                    restaurante_id=restaurante.id,
                    email=u["email"],
                    password_hash=u["password_hash"],
                    rol=RolUsuario(u["rol"]),
                )
            )

        for m in datos["mesas"]:
            db.add(Mesa(restaurante_id=restaurante.id, numero=m["numero"], codigo_qr=m["codigo_qr"]))

        for c in datos["categorias"]:
            categoria = Categoria(restaurante_id=restaurante.id, nombre=c["nombre"], orden=c["orden"])
            db.add(categoria)
            await db.flush()
            for i in c["items"]:
                item = Item(
                    restaurante_id=restaurante.id,
                    categoria_id=categoria.id,
                    nombre=i["nombre"],
                    descripcion=i["descripcion"],
                    precio=i["precio"],
                    disponible=i["disponible"],
                    imagen_url=i["imagen_url"],
                )
                db.add(item)
                await db.flush()
                for g in i["modificador_grupos"]:
                    grupo = ModificadorGrupo(
                        restaurante_id=restaurante.id,
                        item_id=item.id,
                        nombre=g["nombre"],
                        obligatorio=g["obligatorio"],
                        seleccion_multiple=g["seleccion_multiple"],
                    )
                    db.add(grupo)
                    await db.flush()
                    for mod in g["modificadores"]:
                        db.add(
                            Modificador(
                                restaurante_id=restaurante.id,
                                grupo_id=grupo.id,
                                nombre=mod["nombre"],
                                precio_extra=mod["precio_extra"],
                            )
                        )

        await db.commit()

        print(f"Sucursal '{slug}' importada en este nodo de evento:")
        print(f"  {len(datos['categorias'])} categorías, {len(datos['usuarios'])} usuarios de staff, {len(datos['mesas'])} mesas.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Importa una foto de sucursal (exportada con GET /api/admin/sucursales/exportar-datos-evento) "
        "para armar un nodo de evento nuevo."
    )
    parser.add_argument("archivo", help="Ruta al archivo JSON exportado")
    args = parser.parse_args()
    asyncio.run(importar_evento(args.archivo))
