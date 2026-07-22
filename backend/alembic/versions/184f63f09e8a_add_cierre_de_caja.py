"""add cierre de caja

Revision ID: 184f63f09e8a
Revises: ef14b9d7481f
Create Date: 2026-07-22 09:46:40.484629

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '184f63f09e8a'
down_revision: Union[str, None] = 'ef14b9d7481f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "cierre_caja",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("restaurante_id", sa.Integer(), sa.ForeignKey("restaurante.id"), nullable=False),
        sa.Column("usuario_id", sa.Integer(), sa.ForeignKey("usuario.id"), nullable=False),
        sa.Column("desde", sa.DateTime(timezone=True), nullable=False),
        sa.Column("hasta", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("total_efectivo", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("cantidad_efectivo", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_tarjeta", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("cantidad_tarjeta", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_sinpe", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("cantidad_sinpe", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_apple_pay", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("cantidad_apple_pay", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_general", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("cantidad_general", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index("ix_cierre_caja_restaurante_id", "cierre_caja", ["restaurante_id"])

    op.add_column("pedido", sa.Column("cierre_caja_id", sa.Integer(), sa.ForeignKey("cierre_caja.id"), nullable=True))
    op.create_index("ix_pedido_cierre_caja_id", "pedido", ["cierre_caja_id"])


def downgrade() -> None:
    op.drop_column("pedido", "cierre_caja_id")
    op.drop_table("cierre_caja")
