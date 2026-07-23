from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.enums import OrigenPedido


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

    # NUBE para un cierre hecho normalmente; EVENTO_LOCAL para uno que se hizo
    # en un nodo de evento y se subió (importó) a la nube después.
    origen: Mapped[OrigenPedido] = mapped_column(
        Enum(OrigenPedido, name="origen_pedido", native_enum=True, values_callable=lambda obj: [e.value for e in obj]),
        default=OrigenPedido.NUBE,
    )
    # Solo relevante para origen=EVENTO_LOCAL: False mientras el nodo no ha
    # podido subir este cierre a la nube (sin internet en ese momento).
    sincronizado: Mapped[bool] = mapped_column(Boolean, default=True)

    pedidos: Mapped[list["Pedido"]] = relationship(back_populates="cierre_caja")
