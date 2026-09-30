from datetime import date

from sqlalchemy import Column, Date, String, Text, false, ARRAY
from sqlalchemy.dialects.postgresql import TEXT, UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector
import uuid
from database import Base

class WorkoutPlanExercise(Base):
    __tablename__ = "workout_plan_exercises"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    workout_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False
    )

    exercise_id: Mapped[str] = mapped_column(
        String,
        nullable=False
    )

    exercise_order: Mapped[int] = mapped_column(
        nullable=False
    )

    sets_planned: Mapped[int] = mapped_column(
        nullable=False
    )

    reps_min: Mapped[int] = mapped_column(
        nullable=False
    )

    reps_max: Mapped[int] = mapped_column(
        nullable=False
    )

    target_rpe: Mapped[float] = mapped_column(
        nullable=False
    )

    rest_seconds: Mapped[int] = mapped_column(
        nullable=False
    )

    starting_weight: Mapped[float | None] = mapped_column(
        nullable=True
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )