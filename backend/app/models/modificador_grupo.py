from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ModificadorGrupo(Base):
    """Grupo de opciones de un item, ej. 'Tamaño' (única) o 'Extras' (múltiple)."""

    __tablename__ = "modificador_grupo"

    id: Mapped[int] = mapped_column(primary_key=True)
    restaurante_id: Mapped[int] = mapped_column(ForeignKey("restaurante.id"), index=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("item.id"), index=True)

    nombre: Mapped[str] = mapped_column(String(100))
    obligatorio: Mapped[bool] = mapped_column(Boolean, default=False)
    seleccion_multiple: Mapped[bool] = mapped_column(Boolean, default=False)

    item: Mapped["Item"] = relationship(back_populates="modificador_grupos")
    modificadores: Mapped[list["Modificador"]] = relationship(
        back_populates="grupo", cascade="all, delete-orphan", order_by="Modificador.id"
    )
