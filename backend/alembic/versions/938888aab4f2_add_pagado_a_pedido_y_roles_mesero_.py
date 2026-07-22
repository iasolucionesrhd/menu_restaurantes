"""add pagado a pedido y roles mesero cajero

Revision ID: 938888aab4f2
Revises: 7bb11f46943b
Create Date: 2026-07-22 07:49:49.825148

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '938888aab4f2'
down_revision: Union[str, None] = '7bb11f46943b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE rol_usuario ADD VALUE IF NOT EXISTS 'mesero'")
    op.execute("ALTER TYPE rol_usuario ADD VALUE IF NOT EXISTS 'cajero'")

    op.add_column("pedido", sa.Column("pagado", sa.Boolean(), nullable=False, server_default=sa.false()))
    # Backfill: tarjeta/sinpe/apple_pay ya se cobraron en línea al crearse.
    op.execute("UPDATE pedido SET pagado = true WHERE metodo_pago != 'efectivo_en_restaurante'")


def downgrade() -> None:
    op.drop_column("pedido", "pagado")
    # Postgres no permite quitar valores de un enum existente de forma
    # sencilla; 'mesero'/'cajero' quedan en el tipo rol_usuario.
