from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.enums import TRANSICIONES_ESTADO_PEDIDO, EstadoPedido, MetodoPago, TipoEntrega
from app.models.cliente import Cliente
from app.models.ingrediente import Ingrediente
from app.models.item import Item
from app.models.item_ingrediente import ItemIngrediente
from app.models.item_pedido import ItemPedido
from app.models.item_pedido_modificador import ItemPedidoModificador
from app.models.mesa import Mesa
from app.models.modificador_grupo import ModificadorGrupo
from app.models.nota_credito import NotaCredito
from app.models.pedido import Pedido
from app.models.restaurante import Restaurante
from app.schemas.pedido import ClienteCreate, ItemPedidoCreate
from app.services.google_auth import verify_google_id_token
from app.services.payments.base import PaymentAdapter


async def _ajustar_stock(db: AsyncSession, items_cantidades: list[tuple[int, int]], *, signo: int) -> None:
    """signo=1 descuenta stock (venta), signo=-1 lo devuelve (cancelación).

    Nunca bloquea: el stock puede quedar negativo, la alerta de reponer se
    calcula al leer (stock_actual <= stock_minimo), no al escribir aquí.
    """
    item_ids = [item_id for item_id, _ in items_cantidades]
    if not item_ids:
        return
    result = await db.execute(select(ItemIngrediente).where(ItemIngrediente.item_id.in_(item_ids)))
    recetas = result.scalars().all()
    cantidad_por_item = dict(items_cantidades)
    for receta in recetas:
        delta = receta.cantidad_requerida * cantidad_por_item[receta.item_id] * signo
        await db.execute(
            update(Ingrediente)
            .where(Ingrediente.id == receta.ingrediente_id)
            .values(stock_actual=Ingrediente.stock_actual - delta)
        )
    await db.commit()


async def descontar_stock(db: AsyncSession, items_cantidades: list[tuple[int, int]]) -> None:
    await _ajustar_stock(db, items_cantidades, signo=1)


async def restaurar_stock(db: AsyncSession, items_cantidades: list[tuple[int, int]]) -> None:
    await _ajustar_stock(db, items_cantidades, signo=-1)


def _validar_y_construir_modificadores(
    item: Item, modificador_ids: list[int]
) -> tuple[list[ItemPedidoModificador], float]:
    """Valida las opciones elegidas contra los grupos del item y arma el snapshot.

    No confía en el precio/nombre que mande el cliente: los toma siempre del
    Modificador en base de datos, igual que ya se hace con precio_unitario.
    """
    modificadores_por_id = {m.id: m for grupo in item.modificador_grupos for m in grupo.modificadores}

    for modificador_id in modificador_ids:
        if modificador_id not in modificadores_por_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Modificador inválido")

    for grupo in item.modificador_grupos:
        ids_del_grupo = {m.id for m in grupo.modificadores}
        seleccionados = [mid for mid in modificador_ids if mid in ids_del_grupo]
        if grupo.obligatorio and not seleccionados:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=f"Falta seleccionar una opción de '{grupo.nombre}'"
            )
        if not grupo.seleccion_multiple and len(seleccionados) > 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=f"'{grupo.nombre}' solo permite una opción"
            )

    filas = [
        ItemPedidoModificador(
            modificador_id=modificadores_por_id[mid].id,
            nombre=modificadores_por_id[mid].nombre,
            precio_extra=modificadores_por_id[mid].precio_extra,
        )
        for mid in modificador_ids
    ]
    extra_total = sum((modificadores_por_id[mid].precio_extra for mid in modificador_ids), start=0)
    return filas, extra_total


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
        select(Item)
        .where(Item.id.in_(item_ids), Item.restaurante_id == restaurante.id)
        .options(selectinload(Item.modificador_grupos).selectinload(ModificadorGrupo.modificadores))
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
        modificadores_row, extra_por_unidad = _validar_y_construir_modificadores(item, entrada.modificador_ids)
        monto_total += (item.precio + extra_por_unidad) * entrada.cantidad
        item_pedido_rows.append(
            ItemPedido(
                restaurante_id=restaurante.id,
                item_id=item.id,
                cantidad=entrada.cantidad,
                precio_unitario=item.precio,
                notas=entrada.notas,
                modificadores=modificadores_row,
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
    await descontar_stock(db, [(entrada.item_id, entrada.cantidad) for entrada in items_data])

    result = await db.execute(
        select(Pedido)
        .where(Pedido.id == pedido.id)
        .options(
            selectinload(Pedido.items).selectinload(ItemPedido.item),
            selectinload(Pedido.items).selectinload(ItemPedido.modificadores),
            selectinload(Pedido.cliente),
            selectinload(Pedido.mesa),
        )
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
    if nuevo_estado == EstadoPedido.EN_COCINA:
        pedido.en_cocina_en = datetime.now(timezone.utc)
    elif nuevo_estado == EstadoPedido.LISTO:
        pedido.listo_en = datetime.now(timezone.utc)
    await db.commit()
    return pedido


async def generar_nota_credito(db: AsyncSession, pedido: Pedido) -> NotaCredito:
    """Registro interno de cancelación de un pedido facturado (stub, sin envío a Hacienda)."""
    nota = NotaCredito(
        restaurante_id=pedido.restaurante_id,
        pedido_id=pedido.id,
        monto=pedido.monto_total,
        motivo="Cancelación de pedido facturado",
    )
    db.add(nota)
    await db.commit()
    return nota


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
        creado_en=pedido.creado_en,
        en_cocina_en=pedido.en_cocina_en,
        listo_en=pedido.listo_en,
        items=[
            ItemPedidoOut(
                id=ip.id,
                item_id=ip.item_id,
                nombre=ip.item.nombre,
                cantidad=ip.cantidad,
                precio_unitario=ip.precio_unitario,
                notas=ip.notas,
                modificadores=ip.modificadores,
            )
            for ip in pedido.items
        ],
    )
