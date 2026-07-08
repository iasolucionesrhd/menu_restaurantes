from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_restaurante_id, get_owned_or_404, require_role
from app.enums import RolUsuario
from app.models.categoria import Categoria
from app.schemas.categoria import CategoriaCreate, CategoriaOut, CategoriaUpdate

router = APIRouter(
    prefix="/api/admin/categorias",
    tags=["admin:categorias"],
    dependencies=[Depends(require_role(RolUsuario.ADMIN))],
)


@router.get("", response_model=list[CategoriaOut])
async def list_categorias(
    db: AsyncSession = Depends(get_db),
    restaurante_id: int = Depends(get_current_restaurante_id),
) -> list[Categoria]:
    result = await db.execute(
        select(Categoria).where(Categoria.restaurante_id == restaurante_id).order_by(Categoria.orden)
    )
    return list(result.scalars().all())


@router.post("", response_model=CategoriaOut, status_code=status.HTTP_201_CREATED)
async def create_categoria(
    payload: CategoriaCreate,
    db: AsyncSession = Depends(get_db),
    restaurante_id: int = Depends(get_current_restaurante_id),
) -> Categoria:
    categoria = Categoria(restaurante_id=restaurante_id, nombre=payload.nombre, orden=payload.orden)
    db.add(categoria)
    await db.commit()
    await db.refresh(categoria)
    return categoria


@router.patch("/{categoria_id}", response_model=CategoriaOut)
async def update_categoria(
    categoria_id: int,
    payload: CategoriaUpdate,
    db: AsyncSession = Depends(get_db),
    restaurante_id: int = Depends(get_current_restaurante_id),
) -> Categoria:
    categoria = await get_owned_or_404(db, Categoria, categoria_id, restaurante_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(categoria, field, value)
    await db.commit()
    await db.refresh(categoria)
    return categoria


@router.delete("/{categoria_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_categoria(
    categoria_id: int,
    db: AsyncSession = Depends(get_db),
    restaurante_id: int = Depends(get_current_restaurante_id),
) -> None:
    categoria = await get_owned_or_404(db, Categoria, categoria_id, restaurante_id)
    await db.delete(categoria)
    await db.commit()
