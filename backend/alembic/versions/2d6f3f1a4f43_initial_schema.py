"""initial schema

Revision ID: 2d6f3f1a4f43
Revises:
Create Date: 2026-07-08 17:09:44.143145

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2d6f3f1a4f43'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

rol_usuario = sa.Enum("admin", "cocina", name="rol_usuario")
estado_pedido = sa.Enum(
    "recibido", "en_cocina", "listo", "entregado", "cancelado", name="estado_pedido"
)
metodo_pago = sa.Enum(
    "tarjeta", "sinpe", "apple_pay", "efectivo_en_restaurante", name="metodo_pago"
)
tipo_entrega = sa.Enum("mesa", "retiro", name="tipo_entrega")


def upgrade() -> None:
    bind = op.get_bind()
    rol_usuario.create(bind, checkfirst=True)
    estado_pedido.create(bind, checkfirst=True)
    metodo_pago.create(bind, checkfirst=True)
    tipo_entrega.create(bind, checkfirst=True)

    op.create_table(
        "restaurante",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nombre", sa.String(length=200), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("tilopay_llave_api", sa.String(length=500), nullable=True),
        sa.Column("tilopay_usuario_api", sa.String(length=500), nullable=True),
        sa.Column("tilopay_password_api", sa.String(length=500), nullable=True),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_restaurante_slug", "restaurante", ["slug"], unique=True)

    op.create_table(
        "usuario",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("restaurante_id", sa.Integer(), sa.ForeignKey("restaurante.id"), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("rol", rol_usuario, nullable=False),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("email", name="uq_usuario_email"),
    )
    op.create_index("ix_usuario_restaurante_id", "usuario", ["restaurante_id"])
    op.create_index("ix_usuario_email", "usuario", ["email"])

    op.create_table(
        "mesa",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("restaurante_id", sa.Integer(), sa.ForeignKey("restaurante.id"), nullable=False),
        sa.Column("numero", sa.Integer(), nullable=True),
        sa.Column("codigo_qr", sa.String(length=64), nullable=False),
    )
    op.create_index("ix_mesa_restaurante_id", "mesa", ["restaurante_id"])
    op.create_index("ix_mesa_codigo_qr", "mesa", ["codigo_qr"], unique=True)

    op.create_table(
        "categoria",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("restaurante_id", sa.Integer(), sa.ForeignKey("restaurante.id"), nullable=False),
        sa.Column("nombre", sa.String(length=150), nullable=False),
        sa.Column("orden", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index("ix_categoria_restaurante_id", "categoria", ["restaurante_id"])

    op.create_table(
        "item",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("restaurante_id", sa.Integer(), sa.ForeignKey("restaurante.id"), nullable=False),
        sa.Column("categoria_id", sa.Integer(), sa.ForeignKey("categoria.id"), nullable=False),
        sa.Column("nombre", sa.String(length=200), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("precio", sa.Numeric(10, 2), nullable=False),
        sa.Column("disponible", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("imagen_url", sa.String(length=500), nullable=True),
    )
    op.create_index("ix_item_restaurante_id", "item", ["restaurante_id"])
    op.create_index("ix_item_categoria_id", "item", ["categoria_id"])

    op.create_table(
        "cliente",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("restaurante_id", sa.Integer(), sa.ForeignKey("restaurante.id"), nullable=False),
        sa.Column("nombre", sa.String(length=200), nullable=False),
        sa.Column("correo", sa.String(length=255), nullable=True),
        sa.Column("telefono", sa.String(length=50), nullable=True),
        sa.Column("consentimiento_datos", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_cliente_restaurante_id", "cliente", ["restaurante_id"])

    op.create_table(
        "pedido",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("restaurante_id", sa.Integer(), sa.ForeignKey("restaurante.id"), nullable=False),
        sa.Column("mesa_id", sa.Integer(), sa.ForeignKey("mesa.id"), nullable=True),
        sa.Column("cliente_id", sa.Integer(), sa.ForeignKey("cliente.id"), nullable=False),
        sa.Column("estado", estado_pedido, nullable=False, server_default="recibido"),
        sa.Column("metodo_pago", metodo_pago, nullable=False),
        sa.Column("monto_total", sa.Numeric(10, 2), nullable=False),
        sa.Column("tilopay_transaction_id", sa.String(length=255), nullable=True),
        sa.Column("tipo_entrega", tipo_entrega, nullable=False),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "actualizado_en",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_pedido_restaurante_id", "pedido", ["restaurante_id"])
    op.create_index("ix_pedido_mesa_id", "pedido", ["mesa_id"])
    op.create_index("ix_pedido_cliente_id", "pedido", ["cliente_id"])
    op.create_index("ix_pedido_estado", "pedido", ["estado"])

    op.create_table(
        "item_pedido",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("restaurante_id", sa.Integer(), sa.ForeignKey("restaurante.id"), nullable=False),
        sa.Column("pedido_id", sa.Integer(), sa.ForeignKey("pedido.id"), nullable=False),
        sa.Column("item_id", sa.Integer(), sa.ForeignKey("item.id"), nullable=False),
        sa.Column("cantidad", sa.Integer(), nullable=False),
        sa.Column("precio_unitario", sa.Numeric(10, 2), nullable=False),
        sa.Column("notas", sa.Text(), nullable=True),
    )
    op.create_index("ix_item_pedido_restaurante_id", "item_pedido", ["restaurante_id"])
    op.create_index("ix_item_pedido_pedido_id", "item_pedido", ["pedido_id"])
    op.create_index("ix_item_pedido_item_id", "item_pedido", ["item_id"])


def downgrade() -> None:
    op.drop_table("item_pedido")
    op.drop_table("pedido")
    op.drop_table("cliente")
    op.drop_table("item")
    op.drop_table("categoria")
    op.drop_table("mesa")
    op.drop_table("usuario")
    op.drop_table("restaurante")

    bind = op.get_bind()
    tipo_entrega.drop(bind, checkfirst=True)
    metodo_pago.drop(bind, checkfirst=True)
    estado_pedido.drop(bind, checkfirst=True)
    rol_usuario.drop(bind, checkfirst=True)
