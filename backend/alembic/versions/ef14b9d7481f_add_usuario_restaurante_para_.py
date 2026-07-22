"""add usuario_restaurante para multisucursal

Revision ID: ef14b9d7481f
Revises: 938888aab4f2
Create Date: 2026-07-22 08:55:14.573199

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ef14b9d7481f'
down_revision: Union[str, None] = '938888aab4f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "usuario_restaurante",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("usuario_id", sa.Integer(), sa.ForeignKey("usuario.id"), nullable=False),
        sa.Column("restaurante_id", sa.Integer(), sa.ForeignKey("restaurante.id"), nullable=False),
        sa.UniqueConstraint("usuario_id", "restaurante_id", name="uq_usuario_restaurante"),
    )
    op.create_index("ix_usuario_restaurante_usuario_id", "usuario_restaurante", ["usuario_id"])
    op.create_index("ix_usuario_restaurante_restaurante_id", "usuario_restaurante", ["restaurante_id"])


def downgrade() -> None:
    op.drop_table("usuario_restaurante")
