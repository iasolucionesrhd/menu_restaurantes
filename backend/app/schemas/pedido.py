from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, field_validator

from app.enums import EstadoPedido, MetodoPago


class DatosFacturacion(BaseModel):
    nombre: str
    cedula: str
    correo: str | None = None
    telefono: str | None = None
    direccion: str
    actividad_economica: str | None = None

    @field_validator("nombre", "cedula", "direccion")
    @classmethod
    def no_vacio(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Este campo no puede estar vacío")
        return v


class ClienteCreate(BaseModel):
    nombre: str
    correo: str | None = None
    telefono: str | None = None
    consentimiento_datos: bool = True
    consentimiento_marketing: bool = False
    google_id_token: str | None = None
    datos_facturacion: DatosFacturacion | None = None


class ItemPedidoCreate(BaseModel):
    item_id: int
    cantidad: int
    notas: str | None = None
    modificador_ids: list[int] = []

    @field_validator("cantidad")
    @classmethod
    def cantidad_positiva(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("La cantidad debe ser mayor a cero")
        return v


class PedidoCreateRequest(BaseModel):
    mesa_codigo_qr: str | None = None
    cliente: ClienteCreate
    metodo_pago: MetodoPago
    items: list[ItemPedidoCreate]
    payment_intent_id: str | None = None


class ItemPedidoModificadorOut(BaseModel):
    nombre: str
    precio_extra: Decimal

    model_config = {"from_attributes": True}


class ItemPedidoOut(BaseModel):
    id: int
    item_id: int
    nombre: str
    cantidad: int
    precio_unitario: Decimal
    notas: str | None
    modificadores: list[ItemPedidoModificadorOut] = []

    model_config = {"from_attributes": True}


class PedidoOut(BaseModel):
    id: int
    estado: EstadoPedido
    metodo_pago: MetodoPago
    pagado: bool
    monto_total: Decimal
    tipo_entrega: str
    mesa_numero: int | None
    cliente_nombre: str
    tilopay_transaction_id: str | None
    requiere_factura: bool
    factura_nombre: str | None
    factura_cedula: str | None
    factura_correo: str | None
    factura_telefono: str | None
    factura_direccion: str | None
    factura_actividad_economica: str | None
    creado_en: datetime
    en_cocina_en: datetime | None
    listo_en: datetime | None
    items: list[ItemPedidoOut]


class ActualizarEstadoRequest(BaseModel):
    estado: EstadoPedido
    pin: str | None = None


class PedidoAsistidoCreateRequest(BaseModel):
    mesa_id: int
    cliente_nombre: str
    items: list[ItemPedidoCreate]

    @field_validator("cliente_nombre")
    @classmethod
    def nombre_no_vacio(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("El nombre del cliente no puede estar vacío")
        return v


class ResumenCajaOut(BaseModel):
    cobrado_hoy: Decimal
    pedidos_cobrados_hoy: int
