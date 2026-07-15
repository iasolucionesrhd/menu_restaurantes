"""add google_sub to cliente

Revision ID: 579a2ecd1052
Revises: 2d6f3f1a4f43
Create Date: 2026-07-14 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '579a2ecd1052'
down_revision: Union[str, None] = '2d6f3f1a4f43'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("cliente", sa.Column("google_sub", sa.String(length=255), nullable=True))
    # Compuesto con restaurante_id a propósito: aísla la identidad de Google
    # por tenant, nunca un unique de google_sub solo (ver comentario en el modelo).
    op.create_unique_constraint(
        "uq_cliente_restaurante_id_google_sub", "cliente", ["restaurante_id", "google_sub"]
    )


def downgrade() -> None:
    op.drop_constraint("uq_cliente_restaurante_id_google_sub", "cliente", type_="unique")
    op.drop_column("cliente", "google_sub")
