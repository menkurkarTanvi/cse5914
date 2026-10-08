from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Text, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.database import Base


class WorkoutFeedback(Base):
    __tablename__ = "workout_feedback"

    feedback_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    workout_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workout_plans.workout_id", ondelete="CASCADE"),
        nullable=False,
        unique=True
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    overall_rating: Mapped[int | None] = mapped_column(
        nullable=True
    )

    comments: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    exercise_feedback: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True
    )

    workout: Mapped["WorkoutPlan"] = relationship(
        "WorkoutPlan",
        back_populates="feedback"
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="workout_feedback"
    )

    __table_args__ = (
        CheckConstraint(
            "overall_rating IS NULL OR "
            "(overall_rating >= 1 AND overall_rating <= 5)",
            name="ck_overall_rating"
        ),
    )