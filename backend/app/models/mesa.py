from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Mesa(Base):
    __tablename__ = "mesa"

    id: Mapped[int] = mapped_column(primary_key=True)
    restaurante_id: Mapped[int] = mapped_column(ForeignKey("restaurante.id"), index=True)

    numero: Mapped[int | None] = mapped_column(Integer, nullable=True)
    codigo_qr: Mapped[str] = mapped_column(String(64), unique=True, index=True)

    restaurante: Mapped["Restaurante"] = relationship(back_populates="mesas")
    pedidos: Mapped[list["Pedido"]] = relationship(back_populates="mesa")
