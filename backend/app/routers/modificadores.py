from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_restaurante_id, get_owned_or_404, require_role
from app.enums import RolUsuario
from app.models.item import Item
from app.models.modificador import Modificador
from app.models.modificador_grupo import ModificadorGrupo
from app.schemas.modificador import (
    ModificadorCreate,
    ModificadorGrupoCreate,
    ModificadorGrupoOut,
    ModificadorGrupoUpdate,
    ModificadorOut,
    ModificadorUpdate,
)

router = APIRouter(
    prefix="/api/admin",
    tags=["admin:modificadores"],
    dependencies=[Depends(require_role(RolUsuario.ADMIN))],
)


@router.post(
    "/items/{item_id}/modificador-grupos", response_model=ModificadorGrupoOut, status_code=status.HTTP_201_CREATED
)
async def create_modificador_grupo(
    item_id: int,
    payload: ModificadorGrupoCreate,
    db: AsyncSession = Depends(get_db),
    restaurante_id: int = Depends(get_current_restaurante_id),
) -> ModificadorGrupoOut:
    await get_owned_or_404(db, Item, item_id, restaurante_id)
    grupo = ModificadorGrupo(item_id=item_id, restaurante_id=restaurante_id, **payload.model_dump())
    db.add(grupo)
    await db.commit()
    await db.refresh(grupo)
    # Recién creado: nunca tiene modificadores todavía, evita el lazy-load async.
    return ModificadorGrupoOut(
        id=grupo.id, nombre=grupo.nombre, obligatorio=grupo.obligatorio, seleccion_multiple=grupo.seleccion_multiple
    )


@router.patch("/modificador-grupos/{grupo_id}", response_model=ModificadorGrupoOut)
async def update_modificador_grupo(
    grupo_id: int,
    payload: ModificadorGrupoUpdate,
    db: AsyncSession = Depends(get_db),
    restaurante_id: int = Depends(get_current_restaurante_id),
) -> ModificadorGrupo:
    grupo = await get_owned_or_404(db, ModificadorGrupo, grupo_id, restaurante_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(grupo, field, value)
    await db.commit()
    await db.refresh(grupo, attribute_names=["modificadores"])
    return grupo


@router.delete("/modificador-grupos/{grupo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_modificador_grupo(
    grupo_id: int,
    db: AsyncSession = Depends(get_db),
    restaurante_id: int = Depends(get_current_restaurante_id),
) -> None:
    grupo = await get_owned_or_404(db, ModificadorGrupo, grupo_id, restaurante_id)
    await db.delete(grupo)
    await db.commit()


@router.post(
    "/modificador-grupos/{grupo_id}/modificadores", response_model=ModificadorOut, status_code=status.HTTP_201_CREATED
)
async def create_modificador(
    grupo_id: int,
    payload: ModificadorCreate,
    db: AsyncSession = Depends(get_db),
    restaurante_id: int = Depends(get_current_restaurante_id),
) -> Modificador:
    await get_owned_or_404(db, ModificadorGrupo, grupo_id, restaurante_id)
    modificador = Modificador(grupo_id=grupo_id, restaurante_id=restaurante_id, **payload.model_dump())
    db.add(modificador)
    await db.commit()
    await db.refresh(modificador)
    return modificador


@router.patch("/modificadores/{modificador_id}", response_model=ModificadorOut)
async def update_modificador(
    modificador_id: int,
    payload: ModificadorUpdate,
    db: AsyncSession = Depends(get_db),
    restaurante_id: int = Depends(get_current_restaurante_id),
) -> Modificador:
    modificador = await get_owned_or_404(db, Modificador, modificador_id, restaurante_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(modificador, field, value)
    await db.commit()
    await db.refresh(modificador)
    return modificador


@router.delete("/modificadores/{modificador_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_modificador(
    modificador_id: int,
    db: AsyncSession = Depends(get_db),
    restaurante_id: int = Depends(get_current_restaurante_id),
) -> None:
    modificador = await get_owned_or_404(db, Modificador, modificador_id, restaurante_id)
    await db.delete(modificador)
    await db.commit()
