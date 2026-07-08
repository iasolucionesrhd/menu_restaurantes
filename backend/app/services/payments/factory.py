from app.config import settings
from app.services.payments.base import PaymentAdapter
from app.services.payments.stub_adapter import StubPaymentAdapter
from app.services.payments.tilopay_adapter import TilopayAdapter


def get_payment_adapter() -> PaymentAdapter:
    if settings.PAYMENT_MODE == "tilopay":
        return TilopayAdapter()
    return StubPaymentAdapter()
