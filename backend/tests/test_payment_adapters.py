from decimal import Decimal

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.enums import MetodoPago
from app.services.payments.factory import get_payment_adapter
from app.services.payments.stub_adapter import StubPaymentAdapter
from app.services.payments.tilopay_adapter import TilopayAdapter


async def test_stub_adapter_always_approves(make_restaurante, db: AsyncSession):
    restaurante = await make_restaurante(db)
    adapter = StubPaymentAdapter()

    intent = await adapter.iniciar_pago(
        restaurante=restaurante, monto=Decimal("10.00"), metodo_pago=MetodoPago.TARJETA, referencia_externa="ref-1"
    )
    assert intent.payment_intent_id.startswith("stub_")

    resultado = await adapter.verificar_transaccion(restaurante=restaurante, payment_intent_id=intent.payment_intent_id)
    assert resultado.aprobado is True
    assert resultado.transaction_id == intent.payment_intent_id


def test_factory_returns_stub_by_default(monkeypatch):
    monkeypatch.setattr(settings, "PAYMENT_MODE", "stub")
    assert isinstance(get_payment_adapter(), StubPaymentAdapter)


def test_factory_returns_tilopay_when_configured(monkeypatch):
    monkeypatch.setattr(settings, "PAYMENT_MODE", "tilopay")
    assert isinstance(get_payment_adapter(), TilopayAdapter)
    monkeypatch.setattr(settings, "PAYMENT_MODE", "stub")


async def test_iniciar_pago_rejects_efectivo(client: AsyncClient, db: AsyncSession, make_restaurante):
    restaurante = await make_restaurante(db)
    response = await client.post(
        f"/api/public/{restaurante.slug}/pagos/iniciar",
        json={"monto": "5.00", "metodo_pago": "efectivo_en_restaurante", "referencia_externa": "ref-x"},
    )
    assert response.status_code == 400


async def test_iniciar_y_confirmar_pago_stub(client: AsyncClient, db: AsyncSession, make_restaurante):
    restaurante = await make_restaurante(db)
    iniciar = await client.post(
        f"/api/public/{restaurante.slug}/pagos/iniciar",
        json={"monto": "10.00", "metodo_pago": "tarjeta", "referencia_externa": "ref-1"},
    )
    assert iniciar.status_code == 200
    payment_intent_id = iniciar.json()["payment_intent_id"]

    confirmar = await client.post(
        f"/api/public/{restaurante.slug}/pagos/confirmar",
        json={"payment_intent_id": payment_intent_id},
    )
    assert confirmar.status_code == 200
    assert confirmar.json() == {"aprobado": True, "transaction_id": payment_intent_id}
