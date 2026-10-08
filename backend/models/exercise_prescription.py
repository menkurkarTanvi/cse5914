from __future__ import annotations

import uuid

from sqlalchemy import (
    ForeignKey,
    String,
    UniqueConstraint,
    CheckConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.database import Base


class ExercisePrescription(Base):
    __tablename__ = "exercise_prescriptions"

    prescription_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    exercise_id: Mapped[str] = mapped_column(
        ForeignKey("exercises.exercise_id", ondelete="CASCADE"),
        nullable=False
    )

    goal: Mapped[str] = mapped_column(
        String,
        nullable=False
    )

    sets_min: Mapped[int] = mapped_column(
        nullable=False
    )

    sets_max: Mapped[int] = mapped_column(
        nullable=False
    )

    reps_min: Mapped[int] = mapped_column(
        nullable=False
    )

    reps_max: Mapped[int] = mapped_column(
        nullable=False
    )

    rest_seconds: Mapped[int] = mapped_column(
        nullable=False
    )

    target_rpe_min: Mapped[float] = mapped_column(
        nullable=False
    )

    target_rpe_max: Mapped[float] = mapped_column(
        nullable=False
    )

    exercise: Mapped["Exercise"] = relationship(
        "Exercise",
        back_populates="prescriptions"
    )

    __table_args__ = (
        UniqueConstraint(
            "exercise_id",
            "goal",
            name="uq_exercise_prescription_goal"
        ),
        CheckConstraint(
            "sets_min > 0 AND sets_max >= sets_min",
            name="ck_valid_sets"
        ),
        CheckConstraint(
            "reps_min > 0 AND reps_max >= reps_min",
            name="ck_valid_reps"
        ),
        CheckConstraint(
            "rest_seconds >= 0",
            name="ck_valid_rest"
        ),
        CheckConstraint(
            "target_rpe_min >= 0 AND target_rpe_max <= 10 "
            "AND target_rpe_max >= target_rpe_min",
            name="ck_valid_rpe"
        ),
    )