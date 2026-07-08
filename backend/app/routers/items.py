from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_restaurante_id, get_owned_or_404, require_role
from app.enums import RolUsuario
from app.models.categoria import Categoria
from app.models.item import Item
from app.schemas.item import ItemCreate, ItemOut, ItemUpdate

router = APIRouter(
    prefix="/api/admin/items",
    tags=["admin:items"],
    dependencies=[Depends(require_role(RolUsuario.ADMIN))],
)


async def _validar_categoria(db: AsyncSession, categoria_id: int, restaurante_id: int) -> None:
    await get_owned_or_404(db, Categoria, categoria_id, restaurante_id)


@router.get("", response_model=list[ItemOut])
async def list_items(
    db: AsyncSession = Depends(get_db),
    restaurante_id: int = Depends(get_current_restaurante_id),
) -> list[Item]:
    result = await db.execute(select(Item).where(Item.restaurante_id == restaurante_id))
    return list(result.scalars().all())


@router.post("", response_model=ItemOut, status_code=status.HTTP_201_CREATED)
async def create_item(
    payload: ItemCreate,
    db: AsyncSession = Depends(get_db),
    restaurante_id: int = Depends(get_current_restaurante_id),
) -> Item:
    await _validar_categoria(db, payload.categoria_id, restaurante_id)
    item = Item(restaurante_id=restaurante_id, **payload.model_dump())
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


@router.patch("/{item_id}", response_model=ItemOut)
async def update_item(
    item_id: int,
    payload: ItemUpdate,
    db: AsyncSession = Depends(get_db),
    restaurante_id: int = Depends(get_current_restaurante_id),
) -> Item:
    item = await get_owned_or_404(db, Item, item_id, restaurante_id)
    updates = payload.model_dump(exclude_unset=True)
    if "categoria_id" in updates:
        await _validar_categoria(db, updates["categoria_id"], restaurante_id)
    for field, value in updates.items():
        setattr(item, field, value)
    await db.commit()
    await db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    restaurante_id: int = Depends(get_current_restaurante_id),
) -> None:
    item = await get_owned_or_404(db, Item, item_id, restaurante_id)
    await db.delete(item)
    await db.commit()
