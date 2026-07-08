from decimal import Decimal

from pydantic import BaseModel

from app.enums import MetodoPago


class IniciarPagoRequest(BaseModel):
    monto: Decimal
    metodo_pago: MetodoPago
    referencia_externa: str


class IniciarPagoResponse(BaseModel):
    payment_intent_id: str
    client_config: dict


class ConfirmarPagoRequest(BaseModel):
    payment_intent_id: str
    transaction_reference: str | None = None


class ConfirmarPagoResponse(BaseModel):
    aprobado: bool
    transaction_id: str | None
