"""empty message

Revision ID: ba2050f7230d
Revises: 0d434ca40d7d
Create Date: 2023-11-29 13:26:03.331577

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ba2050f7230d'
down_revision: Union[str, None] = '0d434ca40d7d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
