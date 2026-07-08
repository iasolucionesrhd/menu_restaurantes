from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.enums import EstadoPedido, MetodoPago, TipoEntrega


class Pedido(Base):
    __tablename__ = "pedido"

    id: Mapped[int] = mapped_column(primary_key=True)
    restaurante_id: Mapped[int] = mapped_column(ForeignKey("restaurante.id"), index=True)
    mesa_id: Mapped[int | None] = mapped_column(ForeignKey("mesa.id"), nullable=True, index=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("cliente.id"), index=True)

    estado: Mapped[EstadoPedido] = mapped_column(
        Enum(EstadoPedido, name="estado_pedido", native_enum=True),
        default=EstadoPedido.RECIBIDO,
        index=True,
    )
    metodo_pago: Mapped[MetodoPago] = mapped_column(Enum(MetodoPago, name="metodo_pago", native_enum=True))
    monto_total: Mapped[float] = mapped_column(Numeric(10, 2))
    tilopay_transaction_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tipo_entrega: Mapped[TipoEntrega] = mapped_column(Enum(TipoEntrega, name="tipo_entrega", native_enum=True))

    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    restaurante: Mapped["Restaurante"] = relationship(back_populates="pedidos")
    mesa: Mapped["Mesa | None"] = relationship(back_populates="pedidos")
    cliente: Mapped["Cliente"] = relationship(back_populates="pedidos")
    items: Mapped[list["ItemPedido"]] = relationship(back_populates="pedido", cascade="all, delete-orphan")
