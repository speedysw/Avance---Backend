"""Agrega columnas termino de temporizador 

Revision ID: f010d511d40f
Revises: eb0f06503013
Create Date: 2025-03-13 14:48:17.393419

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f010d511d40f'
down_revision: Union[str, None] = 'eb0f06503013'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'radar',
        sa.Column(
            'hora_termino',
            sa.DateTime(timezone=True),
            nullable=True,
        )
    )

def downgrade() -> None:
    op.drop_column('radar', 'hora_termino')

