"""Agrega columnas de temporizador 

Revision ID: eb0f06503013
Revises: fa47c9abbb14
Create Date: 2025-03-12 10:33:01.380569

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'eb0f06503013'
down_revision: Union[str, None] = 'fa47c9abbb14'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Agregar la columna 'timerActive' con valor por defecto false
    op.add_column(
        'radar', 
        sa.Column('timerActive', sa.Boolean(), server_default=sa.text('false'), nullable=False)
    )
    # Agregar la columna 'duration'
    op.add_column(
        'radar', 
        sa.Column('duration', sa.Integer(), nullable=True)
    )


def downgrade() -> None:
    # En la reversión, se eliminan las columnas agregadas
    op.drop_column('radar', 'duration')
    op.drop_column('radar', 'timerActive')
