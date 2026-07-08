from enum import Enum


class RolUsuario(str, Enum):
    ADMIN = "admin"
    COCINA = "cocina"


class EstadoPedido(str, Enum):
    RECIBIDO = "recibido"
    EN_COCINA = "en_cocina"
    LISTO = "listo"
    ENTREGADO = "entregado"
    CANCELADO = "cancelado"


class MetodoPago(str, Enum):
    TARJETA = "tarjeta"
    SINPE = "sinpe"
    APPLE_PAY = "apple_pay"
    EFECTIVO_EN_RESTAURANTE = "efectivo_en_restaurante"


class TipoEntrega(str, Enum):
    MESA = "mesa"
    RETIRO = "retiro"


# Transiciones legales de estado de un Pedido. Cancelado es alcanzable desde
# cualquier estado activo; una vez entregado/cancelado el pedido es terminal.
TRANSICIONES_ESTADO_PEDIDO: dict[EstadoPedido, set[EstadoPedido]] = {
    EstadoPedido.RECIBIDO: {EstadoPedido.EN_COCINA, EstadoPedido.CANCELADO},
    EstadoPedido.EN_COCINA: {EstadoPedido.LISTO, EstadoPedido.CANCELADO},
    EstadoPedido.LISTO: {EstadoPedido.ENTREGADO, EstadoPedido.CANCELADO},
    EstadoPedido.ENTREGADO: set(),
    EstadoPedido.CANCELADO: set(),
}
