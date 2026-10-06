from __future__ import annotations
import uuid
from datetime import date
from sqlalchemy import (
    Date,
    ForeignKey,
    String,
    UniqueConstraint,
    CheckConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.database import Base

#This represents ONE actualy workout
class WorkoutPlan(Base):
    __tablename__ = "workout_plans"

    workout_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    program_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "workout_programs.program_id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    # Week 1–4 of the program
    week_number: Mapped[int] = mapped_column(
        nullable=False
    )

    # Example: Monday, Wednesday, Friday
    day_of_week: Mapped[str] = mapped_column(
        String,
        nullable=False
    )

    scheduled_date: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String,
        nullable=False,
        default="scheduled"
    )

    #Relationships
    program: Mapped["WorkoutProgram"] = relationship(
        "WorkoutProgram",
        back_populates="workouts"
    )

    exercises: Mapped[list["WorkoutPlanExercise"]] = relationship(
        "WorkoutPlanExercise",
        back_populates="workout",
        cascade="all, delete-orphan"
    )

    feedback: Mapped["WorkoutFeedback | None"] = relationship(
        "WorkoutFeedback",
        back_populates="workout",
        uselist=False,
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint(
            "program_id",
            "week_number",
            "day_of_week",
            name="uq_program_week_day"
        ),
        CheckConstraint(
            "week_number BETWEEN 1 AND 4",
            name="ck_week_number"
        ),
    )