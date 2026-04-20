"""add_rut_and_billing_fields_to_clientes

Revision ID: a1b2c3d4e5f6
Revises: 95c3bb1ecdcc
Create Date: 2026-04-19 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '95c3bb1ecdcc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "clientes",
        sa.Column("tiene_rut", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "clientes",
        sa.Column("numero_rut", sa.String(50), nullable=True),
    )
    op.add_column(
        "clientes",
        sa.Column("correo_facturacion", sa.String(255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("clientes", "correo_facturacion")
    op.drop_column("clientes", "numero_rut")
    op.drop_column("clientes", "tiene_rut")
