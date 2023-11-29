"""empty message

Revision ID: 0d434ca40d7d
Revises: 2bfa67ae868b
Create Date: 2023-11-29 13:19:23.650392

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0d434ca40d7d'
down_revision: Union[str, None] = '2bfa67ae868b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
