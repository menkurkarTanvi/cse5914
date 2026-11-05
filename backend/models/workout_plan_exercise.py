from __future__ import annotations
import uuid
from sqlalchemy import (
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    CheckConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.database import Base


class WorkoutPlanExercise(Base):
    __tablename__ = "workout_plan_exercises"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    workout_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "workout_plans.workout_id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    exercise_id: Mapped[str] = mapped_column(
        ForeignKey(
            "exercises.exercise_id"
        ),
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

    target_rpe_min: Mapped[float | None] = mapped_column(
        nullable=True
    )

    target_rpe_max: Mapped[float | None] = mapped_column(
        nullable=True
    )

    rest_seconds: Mapped[int] = mapped_column(
        nullable=False
    )

    # Weight planned for THIS workout.
    planned_weight: Mapped[float | None] = mapped_column(
        nullable=True
    )

    weight_unit: Mapped[str] = mapped_column(
        String(2),
        nullable=False,
        default="lb"
    )

    progression_method: Mapped[str | None] = mapped_column(
        String,
        nullable=True
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    #------------------Relationships---------------------------------
    workout: Mapped["WorkoutPlan"] = relationship(
        "WorkoutPlan",
        back_populates="exercises"
    )

    exercise: Mapped["Exercise"] = relationship(
        "Exercise",
        back_populates="workout_plan_exercises"
    )

    sets: Mapped[list["WorkoutSet"]] = relationship(
        "WorkoutSet",
        back_populates="workout_plan_exercise",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint(
            "workout_id",
            "exercise_order",
            name="uq_workout_exercise_order"
        ),
        CheckConstraint(
            "exercise_order > 0",
            name="ck_exercise_order"
        ),
        CheckConstraint(
            "sets_planned > 0",
            name="ck_sets_planned"
        ),
        CheckConstraint(
            "reps_min > 0 AND reps_max >= reps_min",
            name="ck_reps_range"
        ),
        CheckConstraint(
            "rest_seconds >= 0",
            name="ck_rest_seconds"
        ),
        CheckConstraint(
            "target_rpe_min IS NULL OR "
            "(target_rpe_min >= 0 AND target_rpe_min <= 10)",
            name="ck_target_rpe_min"
        ),
        CheckConstraint(
            "target_rpe_max IS NULL OR "
            "(target_rpe_max >= 0 AND target_rpe_max <= 10)",
            name="ck_target_rpe_max"
        ),
    )