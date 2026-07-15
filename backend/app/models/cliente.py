from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Cliente(Base):
    __tablename__ = "cliente"
    # Unique compuesto (restaurante_id, google_sub), NUNCA unique de google_sub
    # solo: un unique de una sola columna dejaría que la misma cuenta de Google
    # se mezclara entre restaurantes distintos, rompiendo el aislamiento
    # multi-tenant. Postgres trata cada NULL como distinto, así que los
    # clientes invitados (google_sub=None) nunca chocan entre sí.
    __table_args__ = (
        UniqueConstraint("restaurante_id", "google_sub", name="uq_cliente_restaurante_id_google_sub"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    restaurante_id: Mapped[int] = mapped_column(ForeignKey("restaurante.id"), index=True)

    nombre: Mapped[str] = mapped_column(String(200))
    correo: Mapped[str | None] = mapped_column(String(255), nullable=True)
    telefono: Mapped[str | None] = mapped_column(String(50), nullable=True)
    consentimiento_datos: Mapped[bool] = mapped_column(Boolean, default=True)
    # Consentimiento separado del anterior (Ley 8968: finalidades distintas
    # requieren consentimientos distintos) — no viene premarcado, requiere
    # una acción afirmativa explícita del cliente.
    consentimiento_marketing: Mapped[bool] = mapped_column(Boolean, default=False)
    google_sub: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Perfil de facturación "actual" — se sobrescribe cada vez que se
    # reenvía, igual que nombre/telefono. Ver Pedido.factura_* para el
    # snapshot inmutable por pedido (dos lecturas distintas, no redundante).
    factura_nombre: Mapped[str | None] = mapped_column(String(200), nullable=True)
    factura_cedula: Mapped[str | None] = mapped_column(String(30), nullable=True)
    factura_correo: Mapped[str | None] = mapped_column(String(255), nullable=True)
    factura_telefono: Mapped[str | None] = mapped_column(String(50), nullable=True)
    factura_direccion: Mapped[str | None] = mapped_column(String(500), nullable=True)
    factura_actividad_economica: Mapped[str | None] = mapped_column(String(50), nullable=True)

    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    restaurante: Mapped["Restaurante"] = relationship(back_populates="clientes")
    pedidos: Mapped[list["Pedido"]] = relationship(back_populates="cliente")
