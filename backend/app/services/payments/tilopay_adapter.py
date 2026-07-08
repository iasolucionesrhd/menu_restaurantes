from decimal import Decimal

import httpx

from app.config import settings
from app.enums import MetodoPago
from app.models.restaurante import Restaurante
from app.security import decrypt_str
from app.services.payments.base import PaymentAdapter, PaymentIntentResult, PaymentVerificationResult


class TilopayAdapter(PaymentAdapter):
    """Integración real con Tilopay. Usa las credenciales propias de cada
    restaurante (guardadas cifradas) para iniciar y verificar transacciones.

    TODO: confirmar los endpoints exactos y el formato de payload de la API
    de Tilopay una vez se cuente con credenciales de sandbox reales. La
    estructura de esta clase (mismo contrato que StubPaymentAdapter) ya
    permite activarla solo cambiando PAYMENT_MODE=tilopay.
    """

    async def iniciar_pago(
        self,
        *,
        restaurante: Restaurante,
        monto: Decimal,
        metodo_pago: MetodoPago,
        referencia_externa: str,
    ) -> PaymentIntentResult:
        llave_api = decrypt_str(restaurante.tilopay_llave_api) if restaurante.tilopay_llave_api else None
        usuario_api = decrypt_str(restaurante.tilopay_usuario_api) if restaurante.tilopay_usuario_api else None

        async with httpx.AsyncClient(base_url=settings.TILOPAY_API_BASE_URL) as http:
            # TODO: reemplazar por la llamada real de Tilopay para iniciar sesión de pago.
            response = await http.post(
                "/api/v1/payment-intents",
                json={
                    "apiKey": llave_api,
                    "apiUser": usuario_api,
                    "amount": str(monto),
                    "method": metodo_pago.value,
                    "reference": referencia_externa,
                },
            )
            response.raise_for_status()
            data = response.json()

        return PaymentIntentResult(
            payment_intent_id=data.get("id", referencia_externa),
            client_config=data.get("client_config", {}),
        )

    async def verificar_transaccion(
        self,
        *,
        restaurante: Restaurante,
        payment_intent_id: str,
        transaction_reference: str | None = None,
    ) -> PaymentVerificationResult:
        llave_api = decrypt_str(restaurante.tilopay_llave_api) if restaurante.tilopay_llave_api else None

        async with httpx.AsyncClient(base_url=settings.TILOPAY_API_BASE_URL) as http:
            # TODO: reemplazar por el endpoint real de verificación de transacción de Tilopay.
            response = await http.get(
                f"/api/v1/payment-intents/{payment_intent_id}",
                headers={"Authorization": f"Bearer {llave_api}"},
            )
            response.raise_for_status()
            data = response.json()

        return PaymentVerificationResult(
            aprobado=data.get("status") == "approved",
            transaction_id=data.get("transaction_id"),
            raw_response=data,
        )
