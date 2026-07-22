from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Ingrediente(Base):
    __tablename__ = "ingrediente"

    id: Mapped[int] = mapped_column(primary_key=True)
    restaurante_id: Mapped[int] = mapped_column(ForeignKey("restaurante.id"), index=True)

    nombre: Mapped[str] = mapped_column(String(200))
    unidad: Mapped[str] = mapped_column(String(50))
    stock_actual: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    stock_minimo: Mapped[float] = mapped_column(Numeric(10, 2), default=0)

    restaurante: Mapped["Restaurante"] = relationship(back_populates="ingredientes")
