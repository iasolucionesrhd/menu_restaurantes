"""add origen a pedido y cierre_caja

Revision ID: a2f9c7e1b3d4
Revises: 184f63f09e8a
Create Date: 2026-07-22 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a2f9c7e1b3d4'
down_revision: Union[str, None] = '184f63f09e8a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

origen_pedido_enum = sa.Enum("nube", "evento_local", name="origen_pedido")


def upgrade() -> None:
    origen_pedido_enum.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "pedido",
        sa.Column("origen", origen_pedido_enum, nullable=False, server_default="nube"),
    )
    op.add_column(
        "cierre_caja",
        sa.Column(
            "origen",
            sa.Enum("nube", "evento_local", name="origen_pedido", create_type=False),
            nullable=False,
            server_default="nube",
        ),
    )
    op.add_column(
        "cierre_caja",
        sa.Column("sincronizado", sa.Boolean(), nullable=False, server_default=sa.true()),
    )


def downgrade() -> None:
    op.drop_column("cierre_caja", "sincronizado")
    op.drop_column("cierre_caja", "origen")
    op.drop_column("pedido", "origen")
    origen_pedido_enum.drop(op.get_bind(), checkfirst=True)
