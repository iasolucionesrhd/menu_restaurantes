from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class NotaCredito(Base):
    """Registro interno de que un pedido facturado fue cancelado.

    Es un stub: no genera ni envía ningún comprobante electrónico real a
    Hacienda, igual que los campos factura_* en Pedido/Cliente hoy.
    """

    __tablename__ = "nota_credito"

    id: Mapped[int] = mapped_column(primary_key=True)
    restaurante_id: Mapped[int] = mapped_column(ForeignKey("restaurante.id"), index=True)
    pedido_id: Mapped[int] = mapped_column(ForeignKey("pedido.id"), unique=True, index=True)

    monto: Mapped[float] = mapped_column(Numeric(10, 2))
    motivo: Mapped[str] = mapped_column(String(500))

    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    pedido: Mapped["Pedido"] = relationship(back_populates="nota_credito")
