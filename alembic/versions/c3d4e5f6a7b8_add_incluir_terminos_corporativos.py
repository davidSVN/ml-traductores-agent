"""add_incluir_terminos_corporativos

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-04-19
"""

from alembic import op
import sqlalchemy as sa

revision = "c3d4e5f6a7b8"
down_revision = "b2c3d4e5f6a7"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "cotizaciones",
        sa.Column(
            "incluir_terminos_corporativos",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
    )


def downgrade():
    op.drop_column("cotizaciones", "incluir_terminos_corporativos")
