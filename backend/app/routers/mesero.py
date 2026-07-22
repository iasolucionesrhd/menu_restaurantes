from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_restaurante_id, get_owned_or_404, require_role
from app.enums import MetodoPago, RolUsuario
from app.models.mesa import Mesa
from app.models.restaurante import Restaurante
from app.schemas.mesa import MesaOut
from app.schemas.pedido import ClienteCreate, PedidoAsistidoCreateRequest, PedidoOut
from app.schemas.ws_messages import NuevoPedidoMessage
from app.services.pedido_service import crear_pedido, pedido_a_out
from app.services.payments.base import PaymentAdapter
from app.services.payments.factory import get_payment_adapter
from app.services.ws_manager import manager

router = APIRouter(
    prefix="/api/staff",
    tags=["staff:mesero"],
    dependencies=[Depends(require_role(RolUsuario.ADMIN, RolUsuario.MESERO))],
)


@router.get("/mesas", response_model=list[MesaOut])
async def list_mesas_staff(
    db: AsyncSession = Depends(get_db),
    restaurante_id: int = Depends(get_current_restaurante_id),
) -> list[Mesa]:
    result = await db.execute(select(Mesa).where(Mesa.restaurante_id == restaurante_id))
    return list(result.scalars().all())


@router.post("/pedidos/asistido", response_model=PedidoOut, status_code=status.HTTP_201_CREATED)
async def crear_pedido_asistido(
    payload: PedidoAsistidoCreateRequest,
    db: AsyncSession = Depends(get_db),
    restaurante_id: int = Depends(get_current_restaurante_id),
    adapter: PaymentAdapter = Depends(get_payment_adapter),
) -> PedidoOut:
    restaurante = await db.get(Restaurante, restaurante_id)
    mesa = await get_owned_or_404(db, Mesa, payload.mesa_id, restaurante_id)

    pedido = await crear_pedido(
        db,
        restaurante=restaurante,
        mesa_codigo_qr=mesa.codigo_qr,
        cliente_data=ClienteCreate(nombre=payload.cliente_nombre, consentimiento_datos=True),
        metodo_pago=MetodoPago.EFECTIVO_EN_RESTAURANTE,
        items_data=payload.items,
        payment_intent_id=None,
        adapter=adapter,
    )
    pedido_out = pedido_a_out(pedido)
    await manager.broadcast(restaurante_id, NuevoPedidoMessage(pedido=pedido_out).model_dump(mode="json"))
    return pedido_out
