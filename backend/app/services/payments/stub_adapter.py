from decimal import Decimal
from uuid import uuid4

from app.enums import MetodoPago
from app.models.restaurante import Restaurante
from app.services.payments.base import PaymentAdapter, PaymentIntentResult, PaymentVerificationResult


class StubPaymentAdapter(PaymentAdapter):
    """Simula una pasarela de pago aprobada, para desarrollar/probar el flujo
    completo de checkout sin credenciales reales de Tilopay."""

    async def iniciar_pago(
        self,
        *,
        restaurante: Restaurante,
        monto: Decimal,
        metodo_pago: MetodoPago,
        referencia_externa: str,
    ) -> PaymentIntentResult:
        return PaymentIntentResult(payment_intent_id=f"stub_{uuid4()}", client_config={})

    async def verificar_transaccion(
        self,
        *,
        restaurante: Restaurante,
        payment_intent_id: str,
        transaction_reference: str | None = None,
    ) -> PaymentVerificationResult:
        return PaymentVerificationResult(aprobado=True, transaction_id=payment_intent_id)
