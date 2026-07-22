from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class UsuarioRestaurante(Base):
    """Sucursales adicionales a las que un Usuario (típicamente admin) puede
    cambiarse sin tener otra cuenta — ver deps.get_current_restaurante_id y
    routers/sucursales.py. usuario.restaurante_id sigue siendo su sucursal
    de origen; esta tabla son las extra."""

    __tablename__ = "usuario_restaurante"
    __table_args__ = (UniqueConstraint("usuario_id", "restaurante_id", name="uq_usuario_restaurante"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"), index=True)
    restaurante_id: Mapped[int] = mapped_column(ForeignKey("restaurante.id"), index=True)
