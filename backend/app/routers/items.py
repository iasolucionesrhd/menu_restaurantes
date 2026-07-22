from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.deps import get_current_restaurante_id, get_owned_or_404, require_role
from app.enums import RolUsuario
from app.models.categoria import Categoria
from app.models.ingrediente import Ingrediente
from app.models.item import Item
from app.models.item_ingrediente import ItemIngrediente
from app.models.modificador_grupo import ModificadorGrupo
from app.schemas.item import ItemCreate, ItemIngredienteOut, ItemOut, ItemUpdate, RecetaUpdate

router = APIRouter(
    prefix="/api/admin/items",
    tags=["admin:items"],
    dependencies=[Depends(require_role(RolUsuario.ADMIN))],
)


def _load_options():
    return (
        selectinload(Item.ingredientes).selectinload(ItemIngrediente.ingrediente),
        selectinload(Item.modificador_grupos).selectinload(ModificadorGrupo.modificadores),
    )


def _to_out(item: Item) -> ItemOut:
    return ItemOut(
        id=item.id,
        categoria_id=item.categoria_id,
        nombre=item.nombre,
        descripcion=item.descripcion,
        precio=item.precio,
        disponible=item.disponible,
        imagen_url=item.imagen_url,
        ingredientes=[
            ItemIngredienteOut(
                ingrediente_id=ii.ingrediente_id,
                nombre=ii.ingrediente.nombre,
                unidad=ii.ingrediente.unidad,
                cantidad_requerida=ii.cantidad_requerida,
            )
            for ii in item.ingredientes
        ],
        modificador_grupos=item.modificador_grupos,
    )


async def _obtener_item_con_receta(db: AsyncSession, item_id: int, restaurante_id: int) -> Item:
    result = await db.execute(
        select(Item).where(Item.id == item_id, Item.restaurante_id == restaurante_id).options(*_load_options())
    )
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No encontrado")
    return item


async def _validar_categoria(db: AsyncSession, categoria_id: int, restaurante_id: int) -> None:
    await get_owned_or_404(db, Categoria, categoria_id, restaurante_id)


@router.get("", response_model=list[ItemOut])
async def list_items(
    db: AsyncSession = Depends(get_db),
    restaurante_id: int = Depends(get_current_restaurante_id),
) -> list[ItemOut]:
    result = await db.execute(
        select(Item).where(Item.restaurante_id == restaurante_id).options(*_load_options())
    )
    return [_to_out(item) for item in result.scalars().all()]


@router.post("", response_model=ItemOut, status_code=status.HTTP_201_CREATED)
async def create_item(
    payload: ItemCreate,
    db: AsyncSession = Depends(get_db),
    restaurante_id: int = Depends(get_current_restaurante_id),
) -> ItemOut:
    await _validar_categoria(db, payload.categoria_id, restaurante_id)
    item = Item(restaurante_id=restaurante_id, **payload.model_dump())
    db.add(item)
    await db.commit()
    return _to_out(await _obtener_item_con_receta(db, item.id, restaurante_id))


@router.patch("/{item_id}", response_model=ItemOut)
async def update_item(
    item_id: int,
    payload: ItemUpdate,
    db: AsyncSession = Depends(get_db),
    restaurante_id: int = Depends(get_current_restaurante_id),
) -> ItemOut:
    item = await get_owned_or_404(db, Item, item_id, restaurante_id)
    updates = payload.model_dump(exclude_unset=True)
    if "categoria_id" in updates:
        await _validar_categoria(db, updates["categoria_id"], restaurante_id)
    for field, value in updates.items():
        setattr(item, field, value)
    await db.commit()
    return _to_out(await _obtener_item_con_receta(db, item_id, restaurante_id))


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    restaurante_id: int = Depends(get_current_restaurante_id),
) -> None:
    item = await get_owned_or_404(db, Item, item_id, restaurante_id)
    await db.delete(item)
    await db.commit()


@router.put("/{item_id}/ingredientes", response_model=ItemOut)
async def set_receta_item(
    item_id: int,
    payload: RecetaUpdate,
    db: AsyncSession = Depends(get_db),
    restaurante_id: int = Depends(get_current_restaurante_id),
) -> ItemOut:
    await get_owned_or_404(db, Item, item_id, restaurante_id)

    ingrediente_ids = [entrada.ingrediente_id for entrada in payload.ingredientes]
    if ingrediente_ids:
        result = await db.execute(
            select(Ingrediente.id).where(
                Ingrediente.id.in_(ingrediente_ids), Ingrediente.restaurante_id == restaurante_id
            )
        )
        ids_validos = set(result.scalars().all())
        if ids_validos != set(ingrediente_ids):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ingrediente no encontrado")

    result = await db.execute(select(ItemIngrediente).where(ItemIngrediente.item_id == item_id))
    for receta_actual in result.scalars().all():
        await db.delete(receta_actual)
    for entrada in payload.ingredientes:
        db.add(
            ItemIngrediente(
                item_id=item_id, ingrediente_id=entrada.ingrediente_id, cantidad_requerida=entrada.cantidad_requerida
            )
        )
    await db.commit()
    return _to_out(await _obtener_item_con_receta(db, item_id, restaurante_id))
