from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Categoria(Base):
    __tablename__ = "categoria"

    id: Mapped[int] = mapped_column(primary_key=True)
    restaurante_id: Mapped[int] = mapped_column(ForeignKey("restaurante.id"), index=True)

    nombre: Mapped[str] = mapped_column(String(150))
    orden: Mapped[int] = mapped_column(Integer, default=0)

    restaurante: Mapped["Restaurante"] = relationship(back_populates="categorias")
    items: Mapped[list["Item"]] = relationship(back_populates="categoria", cascade="all, delete-orphan")
