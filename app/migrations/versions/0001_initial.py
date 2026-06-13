"""Начальная схема: таблица peaks

Revision ID: 0001
Revises:
Create Date: 2026-06-04
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "peaks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("height_m", sa.Integer(), nullable=False),
        sa.Column("country", sa.String(length=80), nullable=False),
        sa.Column("range_name", sa.String(length=120), nullable=False),
        sa.Column("first_ascent_year", sa.Integer(), nullable=True),
        sa.Column("difficulty", sa.String(length=40), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )


def downgrade() -> None:
    op.drop_table("peaks")
