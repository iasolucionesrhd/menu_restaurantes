"""add ingredientes receta y tiempos de cocina

Revision ID: 3fa6a3a36f72
Revises: 7d6468a2718c
Create Date: 2026-07-22 01:59:41.178299

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3fa6a3a36f72'
down_revision: Union[str, None] = '7d6468a2718c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ingrediente",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("restaurante_id", sa.Integer(), sa.ForeignKey("restaurante.id"), nullable=False),
        sa.Column("nombre", sa.String(length=200), nullable=False),
        sa.Column("unidad", sa.String(length=50), nullable=False),
        sa.Column("stock_actual", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("stock_minimo", sa.Numeric(10, 2), nullable=False, server_default="0"),
    )
    op.create_index("ix_ingrediente_restaurante_id", "ingrediente", ["restaurante_id"])

    op.create_table(
        "item_ingrediente",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("item_id", sa.Integer(), sa.ForeignKey("item.id"), nullable=False),
        sa.Column("ingrediente_id", sa.Integer(), sa.ForeignKey("ingrediente.id"), nullable=False),
        sa.Column("cantidad_requerida", sa.Numeric(10, 2), nullable=False),
        sa.UniqueConstraint("item_id", "ingrediente_id", name="uq_item_ingrediente"),
    )
    op.create_index("ix_item_ingrediente_item_id", "item_ingrediente", ["item_id"])
    op.create_index("ix_item_ingrediente_ingrediente_id", "item_ingrediente", ["ingrediente_id"])

    op.add_column("pedido", sa.Column("en_cocina_en", sa.DateTime(timezone=True), nullable=True))
    op.add_column("pedido", sa.Column("listo_en", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("pedido", "listo_en")
    op.drop_column("pedido", "en_cocina_en")

    op.drop_table("item_ingrediente")
    op.drop_table("ingrediente")
