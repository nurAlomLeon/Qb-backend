"""explanation images

Revision ID: bd09119db751
Revises: 2a6f04425089
Create Date: 2026-10-04 18:20:00.000000

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = 'bd09119db751'
down_revision = '2a6f04425089'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table('questions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('explanation_images', sa.JSON(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('questions', schema=None) as batch_op:
        batch_op.drop_column('explanation_images')
