"""Initial onboarding schema."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

goal_enum = sa.Enum("strength", "hypertrophy", "fat_loss", "endurance", name="goal_enum")
experience_enum = sa.Enum("beginner", "intermediate", "advanced", name="experience_level_enum")


def upgrade() -> None:
    op.create_table(
        "profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("display_name", sa.String(100), nullable=False),
        sa.Column("goal", goal_enum, nullable=False),
        sa.Column("experience_level", experience_enum, nullable=False),
        sa.Column("training_block_weeks", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "profile_equipment",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("profile_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(80), nullable=False),
        sa.UniqueConstraint("profile_id", "name"),
    )
    op.create_table(
        "availability",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("profile_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("day_of_week", sa.Integer(), nullable=False),
        sa.Column("session_minutes", sa.Integer(), nullable=False),
        sa.CheckConstraint("day_of_week BETWEEN 0 AND 6"),
        sa.CheckConstraint("session_minutes BETWEEN 15 AND 240"),
        sa.UniqueConstraint("profile_id", "day_of_week"),
    )
    op.create_table(
        "limitations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("profile_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("body_area", sa.String(80), nullable=False),
        sa.Column("notes", sa.String(500)),
        sa.Column("hard_exclusion", sa.Boolean(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("limitations")
    op.drop_table("availability")
    op.drop_table("profile_equipment")
    op.drop_table("profiles")
    experience_enum.drop(op.get_bind())
    goal_enum.drop(op.get_bind())
