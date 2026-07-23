from enum import Enum


class RolUsuario(str, Enum):
    ADMIN = "admin"
    COCINA = "cocina"
    MESERO = "mesero"
    CAJERO = "cajero"


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


class OrigenPedido(str, Enum):
    """De dónde salió un pedido/cierre de caja: la nube (flujo normal) o un
    nodo de evento local, importado en bloque al cerrar caja allá."""

    NUBE = "nube"
    EVENTO_LOCAL = "evento_local"


# Transiciones legales de estado de un Pedido. Cancelado solo es alcanzable
# antes de que el pedido esté listo para servir; una vez listo/entregado/
# cancelado el pedido es terminal respecto a la cancelación.
TRANSICIONES_ESTADO_PEDIDO: dict[EstadoPedido, set[EstadoPedido]] = {
    EstadoPedido.RECIBIDO: {EstadoPedido.EN_COCINA, EstadoPedido.CANCELADO},
    EstadoPedido.EN_COCINA: {EstadoPedido.LISTO, EstadoPedido.CANCELADO},
    EstadoPedido.LISTO: {EstadoPedido.ENTREGADO},
    EstadoPedido.ENTREGADO: set(),
    EstadoPedido.CANCELADO: set(),
}
