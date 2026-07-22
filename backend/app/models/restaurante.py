from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models._types import EncryptedString


class Restaurante(Base):
    __tablename__ = "restaurante"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(200))
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)

    tilopay_llave_api: Mapped[str | None] = mapped_column(EncryptedString(500))
    tilopay_usuario_api: Mapped[str | None] = mapped_column(EncryptedString(500))
    tilopay_password_api: Mapped[str | None] = mapped_column(EncryptedString(500))

    # Código que el personal de cocina debe ingresar para cancelar un pedido
    # (el admin no lo necesita). Se guarda con el mismo hash de una sola vía
    # que las contraseñas, nunca en texto plano.
    pin_cancelacion_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)

    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    usuarios: Mapped[list["Usuario"]] = relationship(back_populates="restaurante", cascade="all, delete-orphan")
    mesas: Mapped[list["Mesa"]] = relationship(back_populates="restaurante", cascade="all, delete-orphan")
    categorias: Mapped[list["Categoria"]] = relationship(back_populates="restaurante", cascade="all, delete-orphan")
    items: Mapped[list["Item"]] = relationship(back_populates="restaurante", cascade="all, delete-orphan")
    clientes: Mapped[list["Cliente"]] = relationship(back_populates="restaurante", cascade="all, delete-orphan")
    pedidos: Mapped[list["Pedido"]] = relationship(back_populates="restaurante", cascade="all, delete-orphan")
