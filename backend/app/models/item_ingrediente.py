from sqlalchemy import ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ItemIngrediente(Base):
    """Receta: cuánto de un ingrediente requiere una unidad de un item."""

    __tablename__ = "item_ingrediente"
    __table_args__ = (UniqueConstraint("item_id", "ingrediente_id", name="uq_item_ingrediente"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("item.id"), index=True)
    ingrediente_id: Mapped[int] = mapped_column(ForeignKey("ingrediente.id"), index=True)
    cantidad_requerida: Mapped[float] = mapped_column(Numeric(10, 2))

    item: Mapped["Item"] = relationship(back_populates="ingredientes")
    ingrediente: Mapped["Ingrediente"] = relationship()
