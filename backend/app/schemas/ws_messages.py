from typing import Literal

from pydantic import BaseModel

from app.enums import EstadoPedido
from app.schemas.pedido import PedidoOut


class NuevoPedidoMessage(BaseModel):
    tipo: Literal["nuevo_pedido"] = "nuevo_pedido"
    pedido: PedidoOut


class EstadoActualizadoMessage(BaseModel):
    tipo: Literal["estado_actualizado"] = "estado_actualizado"
    pedido_id: int
    estado: EstadoPedido
