from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.deps import get_current_restaurante_id, get_restaurante_by_slug, require_role
from app.enums import EstadoPedido, RolUsuario
from app.models.item_pedido import ItemPedido
from app.models.pedido import Pedido
from app.models.restaurante import Restaurante
from app.schemas.pedido import ActualizarEstadoRequest, PedidoCreateRequest, PedidoOut
from app.schemas.ws_messages import EstadoActualizadoMessage, NuevoPedidoMessage
from app.services.pedido_service import crear_pedido, pedido_a_out, transicionar_estado
from app.services.payments.base import PaymentAdapter
from app.services.payments.factory import get_payment_adapter
from app.services.ws_manager import manager

public_router = APIRouter(prefix="/api/public/{slug}/pedidos", tags=["public:pedidos"])
staff_router = APIRouter(prefix="/api/staff/pedidos", tags=["staff:pedidos"])


def _load_options():
    return (
        selectinload(Pedido.items).selectinload(ItemPedido.item),
        selectinload(Pedido.cliente),
        selectinload(Pedido.mesa),
    )


@public_router.post("", response_model=PedidoOut, status_code=status.HTTP_201_CREATED)
async def crear_pedido_publico(
    payload: PedidoCreateRequest,
    restaurante: Restaurante = Depends(get_restaurante_by_slug),
    db: AsyncSession = Depends(get_db),
    adapter: PaymentAdapter = Depends(get_payment_adapter),
) -> PedidoOut:
    pedido = await crear_pedido(
        db,
        restaurante=restaurante,
        mesa_codigo_qr=payload.mesa_codigo_qr,
        cliente_data=payload.cliente,
        metodo_pago=payload.metodo_pago,
        items_data=payload.items,
        payment_intent_id=payload.payment_intent_id,
        adapter=adapter,
    )
    pedido_out = pedido_a_out(pedido)
    await manager.broadcast(restaurante.id, NuevoPedidoMessage(pedido=pedido_out).model_dump(mode="json"))
    return pedido_out


@public_router.get("/{pedido_id}", response_model=PedidoOut)
async def obtener_pedido_publico(
    pedido_id: int,
    restaurante: Restaurante = Depends(get_restaurante_by_slug),
    db: AsyncSession = Depends(get_db),
) -> PedidoOut:
    result = await db.execute(
        select(Pedido).where(Pedido.id == pedido_id, Pedido.restaurante_id == restaurante.id).options(*_load_options())
    )
    pedido = result.scalar_one_or_none()
    if pedido is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido no encontrado")
    return pedido_a_out(pedido)


@staff_router.get(
    "", response_model=list[PedidoOut], dependencies=[Depends(require_role(RolUsuario.ADMIN, RolUsuario.COCINA))]
)
async def listar_pedidos_staff(
    estado: str | None = Query(default=None, description="Lista separada por comas, ej. recibido,en_cocina"),
    db: AsyncSession = Depends(get_db),
    restaurante_id: int = Depends(get_current_restaurante_id),
) -> list[PedidoOut]:
    query = select(Pedido).where(Pedido.restaurante_id == restaurante_id).options(*_load_options())
    if estado:
        estados = [EstadoPedido(e.strip()) for e in estado.split(",") if e.strip()]
        query = query.where(Pedido.estado.in_(estados))
    query = query.order_by(Pedido.creado_en)

    result = await db.execute(query)
    return [pedido_a_out(p) for p in result.scalars().all()]


@staff_router.patch(
    "/{pedido_id}/estado",
    response_model=PedidoOut,
    dependencies=[Depends(require_role(RolUsuario.ADMIN, RolUsuario.COCINA))],
)
async def actualizar_estado_pedido(
    pedido_id: int,
    payload: ActualizarEstadoRequest,
    db: AsyncSession = Depends(get_db),
    restaurante_id: int = Depends(get_current_restaurante_id),
) -> PedidoOut:
    result = await db.execute(
        select(Pedido)
        .where(Pedido.id == pedido_id, Pedido.restaurante_id == restaurante_id)
        .options(*_load_options())
    )
    pedido = result.scalar_one_or_none()
    if pedido is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido no encontrado")

    pedido = await transicionar_estado(db, pedido, payload.estado)
    await manager.broadcast(
        restaurante_id, EstadoActualizadoMessage(pedido_id=pedido.id, estado=pedido.estado).model_dump(mode="json")
    )
    return pedido_a_out(pedido)
