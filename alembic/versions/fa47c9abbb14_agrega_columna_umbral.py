"""Agrega columna umbral

Revision ID: fa47c9abbb14
Revises: 
Create Date: 2025-02-20 13:10:48.517738

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fa47c9abbb14'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'radar',  # Nombre de la tabla en la BD
        sa.Column('umbral', sa.Float(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('radar', 'umbral')

