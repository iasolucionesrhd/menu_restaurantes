from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from decimal import Decimal

from app.enums import MetodoPago
from app.models.restaurante import Restaurante


@dataclass
class PaymentIntentResult:
    payment_intent_id: str
    client_config: dict = field(default_factory=dict)


@dataclass
class PaymentVerificationResult:
    aprobado: bool
    transaction_id: str | None = None
    raw_response: dict | None = None


class PaymentAdapter(ABC):
    """Contrato único que deben cumplir todas las pasarelas de pago soportadas."""

    @abstractmethod
    async def iniciar_pago(
        self,
        *,
        restaurante: Restaurante,
        monto: Decimal,
        metodo_pago: MetodoPago,
        referencia_externa: str,
    ) -> PaymentIntentResult:
        """Prepara lo que el frontend necesita para iniciar el cobro (formulario/SDK)."""

    @abstractmethod
    async def verificar_transaccion(
        self,
        *,
        restaurante: Restaurante,
        payment_intent_id: str,
        transaction_reference: str | None = None,
    ) -> PaymentVerificationResult:
        """Confirma del lado del servidor si el cobro realmente se aprobó."""
