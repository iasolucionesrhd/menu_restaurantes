from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_restaurante_id, require_role
from app.enums import RolUsuario
from app.models.restaurante import Restaurante
from app.schemas.restaurante import RestauranteOut, RestauranteUpdate
from app.security import hash_password

router = APIRouter(
    prefix="/api/admin/restaurante",
    tags=["admin:restaurante"],
    dependencies=[Depends(require_role(RolUsuario.ADMIN))],
)


def _to_out(restaurante: Restaurante) -> RestauranteOut:
    return RestauranteOut(
        id=restaurante.id,
        nombre=restaurante.nombre,
        slug=restaurante.slug,
        tilopay_configurado=bool(restaurante.tilopay_llave_api),
        pin_cancelacion_configurado=bool(restaurante.pin_cancelacion_hash),
    )


@router.get("", response_model=RestauranteOut)
async def get_restaurante(
    db: AsyncSession = Depends(get_db),
    restaurante_id: int = Depends(get_current_restaurante_id),
) -> RestauranteOut:
    restaurante = await db.get(Restaurante, restaurante_id)
    return _to_out(restaurante)


@router.patch("", response_model=RestauranteOut)
async def update_restaurante(
    payload: RestauranteUpdate,
    db: AsyncSession = Depends(get_db),
    restaurante_id: int = Depends(get_current_restaurante_id),
) -> RestauranteOut:
    restaurante = await db.get(Restaurante, restaurante_id)
    datos = payload.model_dump(exclude_unset=True)
    pin_cancelacion = datos.pop("pin_cancelacion", None)
    for field, value in datos.items():
        setattr(restaurante, field, value)
    if pin_cancelacion:
        restaurante.pin_cancelacion_hash = hash_password(pin_cancelacion)
    await db.commit()
    await db.refresh(restaurante)
    return _to_out(restaurante)
