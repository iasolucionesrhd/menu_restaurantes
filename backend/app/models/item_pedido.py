from sqlalchemy import ForeignKey, Integer, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ItemPedido(Base):
    __tablename__ = "item_pedido"

    id: Mapped[int] = mapped_column(primary_key=True)
    restaurante_id: Mapped[int] = mapped_column(ForeignKey("restaurante.id"), index=True)
    pedido_id: Mapped[int] = mapped_column(ForeignKey("pedido.id"), index=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("item.id"), index=True)

    cantidad: Mapped[int] = mapped_column(Integer)
    precio_unitario: Mapped[float] = mapped_column(Numeric(10, 2))
    notas: Mapped[str | None] = mapped_column(Text, nullable=True)

    pedido: Mapped["Pedido"] = relationship(back_populates="items")
    item: Mapped["Item"] = relationship()
    modificadores: Mapped[list["ItemPedidoModificador"]] = relationship(
        back_populates="item_pedido", cascade="all, delete-orphan"
    )
