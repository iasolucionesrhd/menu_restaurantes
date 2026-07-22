from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.deps import get_current_restaurante_id, get_current_usuario, get_restaurante_by_slug, require_role
from app.enums import EstadoPedido, RolUsuario
from app.models.cierre_caja import CierreCaja
from app.models.item_pedido import ItemPedido
from app.models.pedido import Pedido
from app.models.restaurante import Restaurante
from app.models.usuario import Usuario
from app.schemas.pedido import (
    ActualizarEstadoRequest,
    CierreCajaOut,
    PedidoCreateRequest,
    PedidoOut,
    ResumenCajaOut,
)
from app.schemas.ws_messages import EstadoActualizadoMessage, NuevoPedidoMessage
from app.security import verify_password
from app.services.pedido_service import (
    cerrar_caja,
    crear_pedido,
    generar_nota_credito,
    marcar_pagado,
    pedido_a_out,
    restaurar_stock,
    transicionar_estado,
)
from app.services.payments.base import PaymentAdapter
from app.services.payments.factory import get_payment_adapter
from app.services.ws_manager import manager

# Quién puede pedir cada transición de estado, más allá de si la transición
# en sí es legal según TRANSICIONES_ESTADO_PEDIDO. Cocina/admin llevan el
# pedido hasta "listo"; mesero solo puede marcarlo "entregado" al llevarlo a
# la mesa; cancelar queda fuera de esta tabla porque además exige PIN si es
# cocina (ver actualizar_estado_pedido).
ROLES_POR_TRANSICION: dict[EstadoPedido, set[RolUsuario]] = {
    EstadoPedido.EN_COCINA: {RolUsuario.ADMIN, RolUsuario.COCINA},
    EstadoPedido.LISTO: {RolUsuario.ADMIN, RolUsuario.COCINA},
    EstadoPedido.ENTREGADO: {RolUsuario.ADMIN, RolUsuario.COCINA, RolUsuario.MESERO},
}

public_router = APIRouter(prefix="/api/public/{slug}/pedidos", tags=["public:pedidos"])
staff_router = APIRouter(prefix="/api/staff/pedidos", tags=["staff:pedidos"])


def _load_options():
    return (
        selectinload(Pedido.items).selectinload(ItemPedido.item),
        selectinload(Pedido.items).selectinload(ItemPedido.modificadores),
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
    "",
    response_model=list[PedidoOut],
    dependencies=[
        Depends(require_role(RolUsuario.ADMIN, RolUsuario.COCINA, RolUsuario.MESERO, RolUsuario.CAJERO))
    ],
)
async def listar_pedidos_staff(
    estado: str | None = Query(default=None, description="Lista separada por comas, ej. recibido,en_cocina"),
    pagado: bool | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    restaurante_id: int = Depends(get_current_restaurante_id),
) -> list[PedidoOut]:
    query = select(Pedido).where(Pedido.restaurante_id == restaurante_id).options(*_load_options())
    if estado:
        estados = [EstadoPedido(e.strip()) for e in estado.split(",") if e.strip()]
        query = query.where(Pedido.estado.in_(estados))
    if pagado is not None:
        query = query.where(Pedido.pagado == pagado)
    query = query.order_by(Pedido.creado_en)

    result = await db.execute(query)
    return [pedido_a_out(p) for p in result.scalars().all()]


@staff_router.get(
    "/resumen-caja",
    response_model=ResumenCajaOut,
    dependencies=[Depends(require_role(RolUsuario.ADMIN, RolUsuario.CAJERO))],
)
async def resumen_caja(
    db: AsyncSession = Depends(get_db),
    restaurante_id: int = Depends(get_current_restaurante_id),
) -> ResumenCajaOut:
    # "Periodo actual" = lo cobrado desde el último cierre de caja (o desde
    # siempre, si nunca se ha cerrado). Es justo lo que un cierre nuevo
    # cuadraría en este momento.
    result = await db.execute(
        select(func.count(Pedido.id), func.coalesce(func.sum(Pedido.monto_total), 0)).where(
            Pedido.restaurante_id == restaurante_id,
            Pedido.pagado.is_(True),
            Pedido.cierre_caja_id.is_(None),
            Pedido.estado != EstadoPedido.CANCELADO,
        )
    )
    cantidad, total = result.one()
    return ResumenCajaOut(cobrado_periodo_actual=total, pedidos_periodo_actual=cantidad)


@staff_router.post(
    "/cierres-caja",
    response_model=CierreCajaOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(RolUsuario.ADMIN, RolUsuario.CAJERO))],
)
async def crear_cierre_caja(
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(get_current_usuario),
    restaurante_id: int = Depends(get_current_restaurante_id),
) -> CierreCaja:
    return await cerrar_caja(db, restaurante_id, usuario.id)


@staff_router.get(
    "/cierres-caja",
    response_model=list[CierreCajaOut],
    dependencies=[Depends(require_role(RolUsuario.ADMIN, RolUsuario.CAJERO))],
)
async def listar_cierres_caja(
    db: AsyncSession = Depends(get_db),
    restaurante_id: int = Depends(get_current_restaurante_id),
) -> list[CierreCaja]:
    result = await db.execute(
        select(CierreCaja).where(CierreCaja.restaurante_id == restaurante_id).order_by(CierreCaja.hasta.desc())
    )
    return list(result.scalars().all())


@staff_router.patch(
    "/{pedido_id}/estado",
    response_model=PedidoOut,
    dependencies=[
        Depends(require_role(RolUsuario.ADMIN, RolUsuario.COCINA, RolUsuario.MESERO))
    ],
)
async def actualizar_estado_pedido(
    pedido_id: int,
    payload: ActualizarEstadoRequest,
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(get_current_usuario),
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

    if payload.estado == EstadoPedido.CANCELADO:
        if pedido.cierre_caja_id is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Este pedido ya quedó incluido en un cierre de caja, no se puede cancelar",
            )
        if usuario.rol not in (RolUsuario.ADMIN, RolUsuario.COCINA):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado para esta acción")
        if usuario.rol == RolUsuario.COCINA:
            restaurante = await db.get(Restaurante, restaurante_id)
            if not restaurante.pin_cancelacion_hash:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El administrador aún no configuró un código de cancelación",
                )
            if not payload.pin or not verify_password(payload.pin, restaurante.pin_cancelacion_hash):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="Código de cancelación incorrecto"
                )
    elif usuario.rol not in ROLES_POR_TRANSICION.get(payload.estado, set()):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado para esta acción")

    pedido = await transicionar_estado(db, pedido, payload.estado)
    if pedido.estado == EstadoPedido.CANCELADO:
        await restaurar_stock(db, [(ip.item_id, ip.cantidad) for ip in pedido.items])
        if pedido.requiere_factura:
            await generar_nota_credito(db, pedido)
    pedido_out = pedido_a_out(pedido)
    await manager.broadcast(restaurante_id, EstadoActualizadoMessage(pedido=pedido_out).model_dump(mode="json"))
    return pedido_out


@staff_router.patch(
    "/{pedido_id}/pagado",
    response_model=PedidoOut,
    dependencies=[Depends(require_role(RolUsuario.ADMIN, RolUsuario.CAJERO))],
)
async def marcar_pedido_pagado(
    pedido_id: int,
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

    pedido = await marcar_pagado(db, pedido)
    pedido_out = pedido_a_out(pedido)
    await manager.broadcast(restaurante_id, EstadoActualizadoMessage(pedido=pedido_out).model_dump(mode="json"))
    return pedido_out
