from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ItemPedidoModificador(Base):
    """Snapshot inmutable de un modificador elegido al momento del pedido.

    Igual que precio_unitario en ItemPedido: si luego se edita/borra el
    Modificador original, el pedido ya creado conserva nombre y precio tal
    como estaban cuando se pidió.
    """

    __tablename__ = "item_pedido_modificador"

    id: Mapped[int] = mapped_column(primary_key=True)
    item_pedido_id: Mapped[int] = mapped_column(ForeignKey("item_pedido.id"), index=True)
    modificador_id: Mapped[int | None] = mapped_column(
        ForeignKey("modificador.id", ondelete="SET NULL"), nullable=True, index=True
    )

    nombre: Mapped[str] = mapped_column(String(100))
    precio_extra: Mapped[float] = mapped_column(Numeric(10, 2))

    item_pedido: Mapped["ItemPedido"] = relationship(back_populates="modificadores")
