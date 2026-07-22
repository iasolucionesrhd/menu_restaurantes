from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Modificador(Base):
    """Opción dentro de un grupo, ej. 'Grande' (+₡2.00) dentro de 'Tamaño'."""

    __tablename__ = "modificador"

    id: Mapped[int] = mapped_column(primary_key=True)
    restaurante_id: Mapped[int] = mapped_column(ForeignKey("restaurante.id"), index=True)
    grupo_id: Mapped[int] = mapped_column(ForeignKey("modificador_grupo.id"), index=True)

    nombre: Mapped[str] = mapped_column(String(100))
    precio_extra: Mapped[float] = mapped_column(Numeric(10, 2), default=0)

    grupo: Mapped["ModificadorGrupo"] = relationship(back_populates="modificadores")
