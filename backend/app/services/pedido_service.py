from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.enums import TRANSICIONES_ESTADO_PEDIDO, EstadoPedido, MetodoPago, TipoEntrega
from app.models.cliente import Cliente
from app.models.item import Item
from app.models.item_pedido import ItemPedido
from app.models.mesa import Mesa
from app.models.pedido import Pedido
from app.models.restaurante import Restaurante
from app.schemas.pedido import ClienteCreate, ItemPedidoCreate
from app.services.google_auth import verify_google_id_token
from app.services.payments.base import PaymentAdapter


async def _resolver_mesa(
    db: AsyncSession, restaurante_id: int, mesa_codigo_qr: str | None
) -> tuple[Mesa | None, TipoEntrega]:
    if mesa_codigo_qr is None:
        return None, TipoEntrega.RETIRO

    result = await db.execute(
        select(Mesa).where(Mesa.codigo_qr == mesa_codigo_qr, Mesa.restaurante_id == restaurante_id)
    )
    mesa = result.scalar_one_or_none()
    if mesa is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mesa no encontrada")

    tipo_entrega = TipoEntrega.MESA if mesa.numero is not None else TipoEntrega.RETIRO
    return mesa, tipo_entrega


async def crear_pedido(
    db: AsyncSession,
    *,
    restaurante: Restaurante,
    mesa_codigo_qr: str | None,
    cliente_data: ClienteCreate,
    metodo_pago: MetodoPago,
    items_data: list[ItemPedidoCreate],
    payment_intent_id: str | None,
    adapter: PaymentAdapter,
) -> Pedido:
    if not items_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El pedido no tiene items")

    # Verificar el token de Google primero, antes de tocar mesa/items/pago,
    # para fallar rápido si el token es inválido.
    google_info = None
    if cliente_data.google_id_token:
        google_info = await verify_google_id_token(cliente_data.google_id_token)

    mesa, tipo_entrega = await _resolver_mesa(db, restaurante.id, mesa_codigo_qr)

    item_ids = [i.item_id for i in items_data]
    result = await db.execute(
        select(Item).where(Item.id.in_(item_ids), Item.restaurante_id == restaurante.id)
    )
    items_por_id = {item.id: item for item in result.scalars().all()}

    monto_total = 0
    item_pedido_rows: list[ItemPedido] = []
    for entrada in items_data:
        item = items_por_id.get(entrada.item_id)
        if item is None or not item.disponible:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=f"Item {entrada.item_id} no disponible"
            )
        monto_total += item.precio * entrada.cantidad
        item_pedido_rows.append(
            ItemPedido(
                restaurante_id=restaurante.id,
                item_id=item.id,
                cantidad=entrada.cantidad,
                precio_unitario=item.precio,
                notas=entrada.notas,
            )
        )

    tilopay_transaction_id: str | None = None
    if metodo_pago != MetodoPago.EFECTIVO_EN_RESTAURANTE:
        if payment_intent_id is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Falta payment_intent_id")
        verificacion = await adapter.verificar_transaccion(
            restaurante=restaurante, payment_intent_id=payment_intent_id
        )
        if not verificacion.aprobado:
            raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail="El pago no fue aprobado")
        tilopay_transaction_id = verificacion.transaction_id

    cliente: Cliente | None = None
    if google_info is not None:
        result = await db.execute(
            select(Cliente).where(
                Cliente.restaurante_id == restaurante.id,
                Cliente.google_sub == google_info.sub,
            )
        )
        cliente = result.scalar_one_or_none()

    if cliente is not None:
        cliente.nombre = cliente_data.nombre
        # El correo viene del token ya verificado, no del JSON del cliente:
        # si no, alguien podría mandar un token válido junto con un correo
        # arbitrario en el body.
        cliente.correo = google_info.email
        cliente.telefono = cliente_data.telefono
        cliente.consentimiento_datos = cliente_data.consentimiento_datos
        cliente.consentimiento_marketing = cliente_data.consentimiento_marketing
        if cliente_data.datos_facturacion is not None:
            d = cliente_data.datos_facturacion
            cliente.factura_nombre = d.nombre
            cliente.factura_cedula = d.cedula
            cliente.factura_correo = d.correo
            cliente.factura_telefono = d.telefono
            cliente.factura_direccion = d.direccion
            cliente.factura_actividad_economica = d.actividad_economica
    else:
        cliente = Cliente(
            restaurante_id=restaurante.id,
            nombre=cliente_data.nombre,
            correo=google_info.email if google_info else cliente_data.correo,
            telefono=cliente_data.telefono,
            consentimiento_datos=cliente_data.consentimiento_datos,
            consentimiento_marketing=cliente_data.consentimiento_marketing,
            google_sub=google_info.sub if google_info else None,
        )
        if cliente_data.datos_facturacion is not None:
            d = cliente_data.datos_facturacion
            cliente.factura_nombre = d.nombre
            cliente.factura_cedula = d.cedula
            cliente.factura_correo = d.correo
            cliente.factura_telefono = d.telefono
            cliente.factura_direccion = d.direccion
            cliente.factura_actividad_economica = d.actividad_economica
        db.add(cliente)
        try:
            await db.flush()
        except IntegrityError:
            # Condición de carrera: dos requests casi simultáneos del mismo
            # cliente de Google nuevo (doble clic / dos pestañas) chocando
            # contra el unique constraint. Recuperar la fila que ganó la carrera.
            await db.rollback()
            result = await db.execute(
                select(Cliente).where(
                    Cliente.restaurante_id == restaurante.id,
                    Cliente.google_sub == google_info.sub,
                )
            )
            cliente = result.scalar_one()

    datos_facturacion = cliente_data.datos_facturacion
    pedido = Pedido(
        restaurante_id=restaurante.id,
        mesa_id=mesa.id if mesa else None,
        cliente_id=cliente.id,
        estado=EstadoPedido.RECIBIDO,
        metodo_pago=metodo_pago,
        monto_total=monto_total,
        tilopay_transaction_id=tilopay_transaction_id,
        tipo_entrega=tipo_entrega,
        requiere_factura=datos_facturacion is not None,
        factura_nombre=datos_facturacion.nombre if datos_facturacion else None,
        factura_cedula=datos_facturacion.cedula if datos_facturacion else None,
        factura_correo=datos_facturacion.correo if datos_facturacion else None,
        factura_telefono=datos_facturacion.telefono if datos_facturacion else None,
        factura_direccion=datos_facturacion.direccion if datos_facturacion else None,
        factura_actividad_economica=datos_facturacion.actividad_economica if datos_facturacion else None,
    )
    pedido.items = item_pedido_rows
    db.add(pedido)
    await db.commit()

    result = await db.execute(
        select(Pedido)
        .where(Pedido.id == pedido.id)
        .options(selectinload(Pedido.items).selectinload(ItemPedido.item), selectinload(Pedido.cliente), selectinload(Pedido.mesa))
    )
    return result.scalar_one()


async def transicionar_estado(db: AsyncSession, pedido: Pedido, nuevo_estado: EstadoPedido) -> Pedido:
    permitidos = TRANSICIONES_ESTADO_PEDIDO.get(pedido.estado, set())
    if nuevo_estado not in permitidos:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No se puede pasar de '{pedido.estado.value}' a '{nuevo_estado.value}'",
        )
    pedido.estado = nuevo_estado
    await db.commit()
    return pedido


def pedido_a_out(pedido: Pedido) -> "PedidoOut":
    from app.schemas.pedido import ItemPedidoOut, PedidoOut

    return PedidoOut(
        id=pedido.id,
        estado=pedido.estado,
        metodo_pago=pedido.metodo_pago,
        monto_total=pedido.monto_total,
        tipo_entrega=pedido.tipo_entrega.value,
        mesa_numero=pedido.mesa.numero if pedido.mesa else None,
        cliente_nombre=pedido.cliente.nombre,
        tilopay_transaction_id=pedido.tilopay_transaction_id,
        requiere_factura=pedido.requiere_factura,
        factura_nombre=pedido.factura_nombre,
        factura_cedula=pedido.factura_cedula,
        factura_correo=pedido.factura_correo,
        factura_telefono=pedido.factura_telefono,
        factura_direccion=pedido.factura_direccion,
        factura_actividad_economica=pedido.factura_actividad_economica,
        items=[
            ItemPedidoOut(
                id=ip.id,
                item_id=ip.item_id,
                nombre=ip.item.nombre,
                cantidad=ip.cantidad,
                precio_unitario=ip.precio_unitario,
                notas=ip.notas,
            )
            for ip in pedido.items
        ],
    )
