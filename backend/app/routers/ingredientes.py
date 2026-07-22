from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_restaurante_id, get_owned_or_404, require_role
from app.enums import RolUsuario
from app.models.ingrediente import Ingrediente
from app.schemas.ingrediente import IngredienteCreate, IngredienteOut, IngredienteUpdate

router = APIRouter(
    prefix="/api/admin/ingredientes",
    tags=["admin:ingredientes"],
    dependencies=[Depends(require_role(RolUsuario.ADMIN))],
)


@router.get("", response_model=list[IngredienteOut])
async def list_ingredientes(
    db: AsyncSession = Depends(get_db),
    restaurante_id: int = Depends(get_current_restaurante_id),
) -> list[Ingrediente]:
    result = await db.execute(select(Ingrediente).where(Ingrediente.restaurante_id == restaurante_id))
    return list(result.scalars().all())


@router.post("", response_model=IngredienteOut, status_code=status.HTTP_201_CREATED)
async def create_ingrediente(
    payload: IngredienteCreate,
    db: AsyncSession = Depends(get_db),
    restaurante_id: int = Depends(get_current_restaurante_id),
) -> Ingrediente:
    ingrediente = Ingrediente(restaurante_id=restaurante_id, **payload.model_dump())
    db.add(ingrediente)
    await db.commit()
    await db.refresh(ingrediente)
    return ingrediente


@router.patch("/{ingrediente_id}", response_model=IngredienteOut)
async def update_ingrediente(
    ingrediente_id: int,
    payload: IngredienteUpdate,
    db: AsyncSession = Depends(get_db),
    restaurante_id: int = Depends(get_current_restaurante_id),
) -> Ingrediente:
    ingrediente = await get_owned_or_404(db, Ingrediente, ingrediente_id, restaurante_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(ingrediente, field, value)
    await db.commit()
    await db.refresh(ingrediente)
    return ingrediente


@router.delete("/{ingrediente_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ingrediente(
    ingrediente_id: int,
    db: AsyncSession = Depends(get_db),
    restaurante_id: int = Depends(get_current_restaurante_id),
) -> None:
    ingrediente = await get_owned_or_404(db, Ingrediente, ingrediente_id, restaurante_id)
    await db.delete(ingrediente)
    await db.commit()
