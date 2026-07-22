"""add cancelacion pin y nota credito

Revision ID: 7d6468a2718c
Revises: 51d3dccca84a
Create Date: 2026-07-21 19:59:10.331427

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7d6468a2718c'
down_revision: Union[str, None] = '51d3dccca84a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("restaurante", sa.Column("pin_cancelacion_hash", sa.String(length=255), nullable=True))

    op.create_table(
        "nota_credito",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("restaurante_id", sa.Integer(), sa.ForeignKey("restaurante.id"), nullable=False, index=True),
        sa.Column("pedido_id", sa.Integer(), sa.ForeignKey("pedido.id"), nullable=False, unique=True, index=True),
        sa.Column("monto", sa.Numeric(10, 2), nullable=False),
        sa.Column("motivo", sa.String(length=500), nullable=False),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("nota_credito")
    op.drop_column("restaurante", "pin_cancelacion_hash")
