import secrets

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_restaurante_id, get_owned_or_404, require_role
from app.enums import RolUsuario
from app.models.mesa import Mesa
from app.models.restaurante import Restaurante
from app.schemas.mesa import MesaCreate, MesaOut
from app.services.qr_service import generate_qr_png, mesa_public_url

router = APIRouter(
    prefix="/api/admin/mesas",
    tags=["admin:mesas"],
    dependencies=[Depends(require_role(RolUsuario.ADMIN))],
)


@router.get("", response_model=list[MesaOut])
async def list_mesas(
    db: AsyncSession = Depends(get_db),
    restaurante_id: int = Depends(get_current_restaurante_id),
) -> list[Mesa]:
    result = await db.execute(select(Mesa).where(Mesa.restaurante_id == restaurante_id))
    return list(result.scalars().all())


@router.post("", response_model=MesaOut, status_code=status.HTTP_201_CREATED)
async def create_mesa(
    payload: MesaCreate,
    db: AsyncSession = Depends(get_db),
    restaurante_id: int = Depends(get_current_restaurante_id),
) -> Mesa:
    mesa = Mesa(restaurante_id=restaurante_id, numero=payload.numero, codigo_qr=secrets.token_urlsafe(8))
    db.add(mesa)
    await db.commit()
    await db.refresh(mesa)
    return mesa


@router.delete("/{mesa_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_mesa(
    mesa_id: int,
    db: AsyncSession = Depends(get_db),
    restaurante_id: int = Depends(get_current_restaurante_id),
) -> None:
    mesa = await get_owned_or_404(db, Mesa, mesa_id, restaurante_id)
    await db.delete(mesa)
    await db.commit()


@router.get("/{mesa_id}/qr")
async def get_mesa_qr(
    mesa_id: int,
    db: AsyncSession = Depends(get_db),
    restaurante_id: int = Depends(get_current_restaurante_id),
) -> Response:
    mesa = await get_owned_or_404(db, Mesa, mesa_id, restaurante_id)
    restaurante = await db.get(Restaurante, restaurante_id)
    png_bytes = generate_qr_png(mesa_public_url(restaurante, mesa))
    return Response(content=png_bytes, media_type="image/png")
