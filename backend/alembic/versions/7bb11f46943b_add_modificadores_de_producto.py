"""add modificadores de producto

Revision ID: 7bb11f46943b
Revises: 3fa6a3a36f72
Create Date: 2026-07-22 06:31:06.165014

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7bb11f46943b'
down_revision: Union[str, None] = '3fa6a3a36f72'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "modificador_grupo",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("restaurante_id", sa.Integer(), sa.ForeignKey("restaurante.id"), nullable=False),
        sa.Column("item_id", sa.Integer(), sa.ForeignKey("item.id"), nullable=False),
        sa.Column("nombre", sa.String(length=100), nullable=False),
        sa.Column("obligatorio", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("seleccion_multiple", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index("ix_modificador_grupo_restaurante_id", "modificador_grupo", ["restaurante_id"])
    op.create_index("ix_modificador_grupo_item_id", "modificador_grupo", ["item_id"])

    op.create_table(
        "modificador",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("restaurante_id", sa.Integer(), sa.ForeignKey("restaurante.id"), nullable=False),
        sa.Column("grupo_id", sa.Integer(), sa.ForeignKey("modificador_grupo.id"), nullable=False),
        sa.Column("nombre", sa.String(length=100), nullable=False),
        sa.Column("precio_extra", sa.Numeric(10, 2), nullable=False, server_default="0"),
    )
    op.create_index("ix_modificador_restaurante_id", "modificador", ["restaurante_id"])
    op.create_index("ix_modificador_grupo_id", "modificador", ["grupo_id"])

    op.create_table(
        "item_pedido_modificador",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("item_pedido_id", sa.Integer(), sa.ForeignKey("item_pedido.id"), nullable=False),
        sa.Column(
            "modificador_id", sa.Integer(), sa.ForeignKey("modificador.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column("nombre", sa.String(length=100), nullable=False),
        sa.Column("precio_extra", sa.Numeric(10, 2), nullable=False),
    )
    op.create_index("ix_item_pedido_modificador_item_pedido_id", "item_pedido_modificador", ["item_pedido_id"])
    op.create_index("ix_item_pedido_modificador_modificador_id", "item_pedido_modificador", ["modificador_id"])


def downgrade() -> None:
    op.drop_table("item_pedido_modificador")
    op.drop_table("modificador")
    op.drop_table("modificador_grupo")
