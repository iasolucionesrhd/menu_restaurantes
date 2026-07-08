from sqlalchemy import Boolean, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Item(Base):
    __tablename__ = "item"

    id: Mapped[int] = mapped_column(primary_key=True)
    restaurante_id: Mapped[int] = mapped_column(ForeignKey("restaurante.id"), index=True)
    categoria_id: Mapped[int] = mapped_column(ForeignKey("categoria.id"), index=True)

    nombre: Mapped[str] = mapped_column(String(200))
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    precio: Mapped[float] = mapped_column(Numeric(10, 2))
    disponible: Mapped[bool] = mapped_column(Boolean, default=True)
    imagen_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    restaurante: Mapped["Restaurante"] = relationship(back_populates="items")
    categoria: Mapped["Categoria"] = relationship(back_populates="items")
