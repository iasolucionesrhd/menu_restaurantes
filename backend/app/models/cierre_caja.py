from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class CierreCaja(Base):
    """Snapshot inmutable de lo cobrado en un período: desde el cierre
    anterior (o desde el primer pedido, si es el primero) hasta ahora.
    Los pedidos incluidos quedan marcados (Pedido.cierre_caja_id) y no se
    pueden volver a incluir en otro cierre ni cancelar."""

    __tablename__ = "cierre_caja"

    id: Mapped[int] = mapped_column(primary_key=True)
    restaurante_id: Mapped[int] = mapped_column(ForeignKey("restaurante.id"), index=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"))

    desde: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    hasta: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    total_efectivo: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    cantidad_efectivo: Mapped[int] = mapped_column(Integer, default=0)
    total_tarjeta: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    cantidad_tarjeta: Mapped[int] = mapped_column(Integer, default=0)
    total_sinpe: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    cantidad_sinpe: Mapped[int] = mapped_column(Integer, default=0)
    total_apple_pay: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    cantidad_apple_pay: Mapped[int] = mapped_column(Integer, default=0)
    total_general: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    cantidad_general: Mapped[int] = mapped_column(Integer, default=0)

    pedidos: Mapped[list["Pedido"]] = relationship(back_populates="cierre_caja")
