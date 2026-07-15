"""add consentimiento_marketing to cliente

Revision ID: d009d0576601
Revises: 579a2ecd1052
Create Date: 2026-07-15 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd009d0576601'
down_revision: Union[str, None] = '579a2ecd1052'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "cliente",
        sa.Column("consentimiento_marketing", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column("cliente", "consentimiento_marketing")
