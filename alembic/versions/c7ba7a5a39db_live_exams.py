"""live exams

Revision ID: c7ba7a5a39db
Revises: b5e10453f989
Create Date: 2026-10-02 01:27:45.665021

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = 'c7ba7a5a39db'
down_revision = 'b5e10453f989'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('live_exams',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('university_id', sa.Integer(), nullable=False),
    sa.Column('paper_id', sa.Integer(), nullable=False),
    sa.Column('title_bn', sa.String(length=160), nullable=False),
    sa.Column('subtitle_bn', sa.String(length=200), nullable=True),
    sa.Column('starts_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('ends_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('duration_minutes', sa.Integer(), nullable=False),
    sa.Column('question_count', sa.Integer(), nullable=False),
    sa.Column('participants', sa.Integer(), nullable=False),
    sa.Column('is_published', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['paper_id'], ['papers.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['university_id'], ['universities.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('live_exams', schema=None) as batch_op:
        batch_op.create_index('ix_live_exams_paper', ['paper_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_live_exams_university_id'), ['university_id'], unique=False)
        batch_op.create_index('ix_live_exams_university_published_starts', ['university_id', 'is_published', 'starts_at'], unique=False)


def downgrade() -> None:
    with op.batch_alter_table('live_exams', schema=None) as batch_op:
        batch_op.drop_index('ix_live_exams_university_published_starts')
        batch_op.drop_index(batch_op.f('ix_live_exams_university_id'))
        batch_op.drop_index('ix_live_exams_paper')

    op.drop_table('live_exams')
