from fastapi import APIRouter, Depends, HTTPException, status

from app.deps import get_restaurante_by_slug
from app.enums import MetodoPago
from app.models.restaurante import Restaurante
from app.schemas.pagos import (
    ConfirmarPagoRequest,
    ConfirmarPagoResponse,
    IniciarPagoRequest,
    IniciarPagoResponse,
)
from app.services.payments.base import PaymentAdapter
from app.services.payments.factory import get_payment_adapter

router = APIRouter(prefix="/api/public/{slug}/pagos", tags=["public:pagos"])


@router.post("/iniciar", response_model=IniciarPagoResponse)
async def iniciar_pago(
    payload: IniciarPagoRequest,
    restaurante: Restaurante = Depends(get_restaurante_by_slug),
    adapter: PaymentAdapter = Depends(get_payment_adapter),
) -> IniciarPagoResponse:
    if payload.metodo_pago == MetodoPago.EFECTIVO_EN_RESTAURANTE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El pago en efectivo no requiere iniciar una transacción",
        )

    resultado = await adapter.iniciar_pago(
        restaurante=restaurante,
        monto=payload.monto,
        metodo_pago=payload.metodo_pago,
        referencia_externa=payload.referencia_externa,
    )
    return IniciarPagoResponse(payment_intent_id=resultado.payment_intent_id, client_config=resultado.client_config)


@router.post("/confirmar", response_model=ConfirmarPagoResponse)
async def confirmar_pago(
    payload: ConfirmarPagoRequest,
    restaurante: Restaurante = Depends(get_restaurante_by_slug),
    adapter: PaymentAdapter = Depends(get_payment_adapter),
) -> ConfirmarPagoResponse:
    resultado = await adapter.verificar_transaccion(
        restaurante=restaurante,
        payment_intent_id=payload.payment_intent_id,
        transaction_reference=payload.transaction_reference,
    )
    return ConfirmarPagoResponse(aprobado=resultado.aprobado, transaction_id=resultado.transaction_id)
