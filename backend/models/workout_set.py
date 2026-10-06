from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.database import Base


class WorkoutSet(Base):
    __tablename__ = "workout_sets"

    set_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    workout_plan_exercise_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "workout_plan_exercises.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    set_number: Mapped[int] = mapped_column(
        nullable=False
    )

    weight: Mapped[float | None] = mapped_column(
        nullable=True
    )

    weight_unit: Mapped[str] = mapped_column(
        String(2),
        nullable=False,
        default="lb"
    )

    reps: Mapped[int] = mapped_column(
        nullable=False
    )

    rpe: Mapped[float | None] = mapped_column(
        nullable=True
    )

    completed: Mapped[bool] = mapped_column(
        nullable=False,
        default=True
    )

    workout_plan_exercise: Mapped["WorkoutPlanExercise"] = relationship(
        "WorkoutPlanExercise",
        back_populates="sets"
    )

    __table_args__ = (
        CheckConstraint(
            "set_number > 0",
            name="ck_set_number"
        ),
        CheckConstraint(
            "reps > 0",
            name="ck_reps"
        ),
        CheckConstraint(
            "weight IS NULL OR weight >= 0",
            name="ck_weight"
        ),
        CheckConstraint(
            "rpe IS NULL OR (rpe >= 0 AND rpe <= 10)",
            name="ck_rpe"
        ),
    )