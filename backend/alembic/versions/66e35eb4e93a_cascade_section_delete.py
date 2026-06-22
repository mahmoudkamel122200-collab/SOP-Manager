"""cascade section delete

Revision ID: 66e35eb4e93a
Revises: 146f394e068a
Create Date: 2026-06-22 03:48:54.141575
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '66e35eb4e93a'
down_revision: Union[str, None] = '146f394e068a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint('documents_section_id_fkey', 'documents', type_='foreignkey')
    op.create_foreign_key('documents_section_id_fkey', 'documents', 'sections', ['section_id'], ['id'], onupdate='CASCADE', ondelete='CASCADE')

def downgrade() -> None:
    op.drop_constraint('documents_section_id_fkey', 'documents', type_='foreignkey')
    op.create_foreign_key('documents_section_id_fkey', 'documents', 'sections', ['section_id'], ['id'], onupdate='CASCADE', ondelete='RESTRICT')
