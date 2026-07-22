from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.enums import EstadoPedido, MetodoPago, TipoEntrega


class Pedido(Base):
    __tablename__ = "pedido"

    id: Mapped[int] = mapped_column(primary_key=True)
    restaurante_id: Mapped[int] = mapped_column(ForeignKey("restaurante.id"), index=True)
    mesa_id: Mapped[int | None] = mapped_column(ForeignKey("mesa.id"), nullable=True, index=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("cliente.id"), index=True)

    estado: Mapped[EstadoPedido] = mapped_column(
        Enum(EstadoPedido, name="estado_pedido", native_enum=True, values_callable=lambda obj: [e.value for e in obj]),
        default=EstadoPedido.RECIBIDO,
        index=True,
    )
    metodo_pago: Mapped[MetodoPago] = mapped_column(
        Enum(MetodoPago, name="metodo_pago", native_enum=True, values_callable=lambda obj: [e.value for e in obj])
    )
    monto_total: Mapped[float] = mapped_column(Numeric(10, 2))
    # tarjeta/sinpe/apple_pay quedan pagado=True desde que se crean (el pago
    # ya se verificó contra el adaptador); efectivo_en_restaurante empieza
    # en False hasta que cajero lo marca al recibir el dinero.
    pagado: Mapped[bool] = mapped_column(Boolean, default=False)
    tilopay_transaction_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tipo_entrega: Mapped[TipoEntrega] = mapped_column(
        Enum(TipoEntrega, name="tipo_entrega", native_enum=True, values_callable=lambda obj: [e.value for e in obj])
    )

    # Snapshot inmutable de los datos de facturación al momento del pedido
    # (igual que precio_unitario en ItemPedido) — necesario incluso para
    # invitados, cuya fila Cliente nunca se vuelve a leer.
    requiere_factura: Mapped[bool] = mapped_column(Boolean, default=False)
    factura_nombre: Mapped[str | None] = mapped_column(String(200), nullable=True)
    factura_cedula: Mapped[str | None] = mapped_column(String(30), nullable=True)
    factura_correo: Mapped[str | None] = mapped_column(String(255), nullable=True)
    factura_telefono: Mapped[str | None] = mapped_column(String(50), nullable=True)
    factura_direccion: Mapped[str | None] = mapped_column(String(500), nullable=True)
    factura_actividad_economica: Mapped[str | None] = mapped_column(String(50), nullable=True)

    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    # Marcas de tiempo para medir cuánto tarda cocina; se llenan al entrar a
    # cada estado (ver transicionar_estado), no son editables directamente.
    en_cocina_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    listo_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    restaurante: Mapped["Restaurante"] = relationship(back_populates="pedidos")
    mesa: Mapped["Mesa | None"] = relationship(back_populates="pedidos")
    cliente: Mapped["Cliente"] = relationship(back_populates="pedidos")
    items: Mapped[list["ItemPedido"]] = relationship(back_populates="pedido", cascade="all, delete-orphan")
    nota_credito: Mapped["NotaCredito | None"] = relationship(
        back_populates="pedido", cascade="all, delete-orphan", uselist=False
    )
