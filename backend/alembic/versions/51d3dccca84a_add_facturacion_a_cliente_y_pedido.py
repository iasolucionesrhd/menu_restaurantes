"""add facturacion a cliente y pedido

Revision ID: 51d3dccca84a
Revises: d009d0576601
Create Date: 2026-07-15 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '51d3dccca84a'
down_revision: Union[str, None] = 'd009d0576601'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("cliente", sa.Column("factura_nombre", sa.String(length=200), nullable=True))
    op.add_column("cliente", sa.Column("factura_cedula", sa.String(length=30), nullable=True))
    op.add_column("cliente", sa.Column("factura_correo", sa.String(length=255), nullable=True))
    op.add_column("cliente", sa.Column("factura_telefono", sa.String(length=50), nullable=True))
    op.add_column("cliente", sa.Column("factura_direccion", sa.String(length=500), nullable=True))
    op.add_column("cliente", sa.Column("factura_actividad_economica", sa.String(length=50), nullable=True))

    op.add_column(
        "pedido", sa.Column("requiere_factura", sa.Boolean(), nullable=False, server_default=sa.false())
    )
    op.add_column("pedido", sa.Column("factura_nombre", sa.String(length=200), nullable=True))
    op.add_column("pedido", sa.Column("factura_cedula", sa.String(length=30), nullable=True))
    op.add_column("pedido", sa.Column("factura_correo", sa.String(length=255), nullable=True))
    op.add_column("pedido", sa.Column("factura_telefono", sa.String(length=50), nullable=True))
    op.add_column("pedido", sa.Column("factura_direccion", sa.String(length=500), nullable=True))
    op.add_column("pedido", sa.Column("factura_actividad_economica", sa.String(length=50), nullable=True))


def downgrade() -> None:
    op.drop_column("pedido", "factura_actividad_economica")
    op.drop_column("pedido", "factura_direccion")
    op.drop_column("pedido", "factura_telefono")
    op.drop_column("pedido", "factura_correo")
    op.drop_column("pedido", "factura_cedula")
    op.drop_column("pedido", "factura_nombre")
    op.drop_column("pedido", "requiere_factura")

    op.drop_column("cliente", "factura_actividad_economica")
    op.drop_column("cliente", "factura_direccion")
    op.drop_column("cliente", "factura_telefono")
    op.drop_column("cliente", "factura_correo")
    op.drop_column("cliente", "factura_cedula")
    op.drop_column("cliente", "factura_nombre")
