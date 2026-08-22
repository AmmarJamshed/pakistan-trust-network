"""Initial PTN schema

Revision ID: 001_initial
Revises:
Create Date: 2026-08-16
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create all tables from metadata for MVP simplicity
    from app.database.base import Base
    from app.database import models  # noqa: F401

    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    from app.database.base import Base
    from app.database import models  # noqa: F401

    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
