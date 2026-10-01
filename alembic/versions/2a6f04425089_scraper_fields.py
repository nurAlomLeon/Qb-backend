"""scraper fields

Revision ID: 2a6f04425089
Revises: c7ba7a5a39db
Create Date: 2026-10-02 02:21:50.867809

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = '2a6f04425089'
down_revision = 'c7ba7a5a39db'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table('question_options', schema=None) as batch_op:
        batch_op.add_column(sa.Column('text_html', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('image_url', sa.String(length=500), nullable=True))

    with op.batch_alter_table('questions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('mark', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('source', sa.String(length=40), nullable=True))
        batch_op.add_column(sa.Column('source_pk', sa.String(length=40), nullable=True))
        batch_op.add_column(sa.Column('stem_html', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('explanation_html', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('images', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('tags', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('raw_json', sa.JSON(), nullable=True))
        batch_op.create_index('ix_questions_paper_source_pk', ['paper_id', 'source_pk'], unique=False)


def downgrade() -> None:
    with op.batch_alter_table('questions', schema=None) as batch_op:
        batch_op.drop_index('ix_questions_paper_source_pk')
        batch_op.drop_column('raw_json')
        batch_op.drop_column('tags')
        batch_op.drop_column('images')
        batch_op.drop_column('explanation_html')
        batch_op.drop_column('stem_html')
        batch_op.drop_column('source_pk')
        batch_op.drop_column('source')
        batch_op.drop_column('mark')

    with op.batch_alter_table('question_options', schema=None) as batch_op:
        batch_op.drop_column('image_url')
        batch_op.drop_column('text_html')
