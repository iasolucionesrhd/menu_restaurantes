from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.database import get_db
from app.deps import get_restaurante_by_slug
from app.models.categoria import Categoria
from app.models.item import Item
from app.models.mesa import Mesa
from app.models.modificador_grupo import ModificadorGrupo
from app.models.restaurante import Restaurante
from app.schemas.menu import CategoriaMenuOut, MenuPublicoOut, MesaPublicaOut

router = APIRouter(prefix="/api/public/{slug}", tags=["public:menu"])


@router.get("/menu", response_model=MenuPublicoOut)
async def get_menu_publico(
    restaurante: Restaurante = Depends(get_restaurante_by_slug),
    db: AsyncSession = Depends(get_db),
) -> MenuPublicoOut:
    result = await db.execute(
        select(Categoria)
        .where(Categoria.restaurante_id == restaurante.id)
        .options(
            selectinload(Categoria.items)
            .selectinload(Item.modificador_grupos)
            .selectinload(ModificadorGrupo.modificadores)
        )
        .order_by(Categoria.orden)
    )
    categorias = result.scalars().all()

    categorias_out = [
        CategoriaMenuOut(
            id=categoria.id,
            nombre=categoria.nombre,
            items=[item for item in categoria.items if item.disponible],
        )
        for categoria in categorias
    ]

    return MenuPublicoOut(
        restaurante_nombre=restaurante.nombre,
        restaurante_slug=restaurante.slug,
        payment_mode=settings.PAYMENT_MODE,
        categorias=categorias_out,
    )


@router.get("/mesa/{codigo_qr}", response_model=MesaPublicaOut)
async def get_mesa_publica(
    codigo_qr: str,
    restaurante: Restaurante = Depends(get_restaurante_by_slug),
    db: AsyncSession = Depends(get_db),
) -> MesaPublicaOut:
    result = await db.execute(
        select(Mesa).where(Mesa.codigo_qr == codigo_qr, Mesa.restaurante_id == restaurante.id)
    )
    mesa = result.scalar_one_or_none()
    if mesa is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mesa no encontrada")

    tipo_entrega = "mesa" if mesa.numero is not None else "retiro"
    return MesaPublicaOut(numero=mesa.numero, tipo_entrega=tipo_entrega)
