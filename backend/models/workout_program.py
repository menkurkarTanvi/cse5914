from __future__ import annotations
import uuid
from datetime import date
from sqlalchemy import Date, ForeignKey, String, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.database import Base

#This class represents the enture 4 week session
#WorkoutProgram
#    │
#    ├── WorkoutPlan
#    ├── WorkoutPlan
#    ├── WorkoutPlan

class WorkoutProgram(Base):
    __tablename__ = "workout_programs"
    __table_args__ = (
        CheckConstraint("end_date >= start_date", name="ck_program_dates"),
        CheckConstraint("status IN ('draft','active','completed')", name="ck_program_status"),
        CheckConstraint("goal IN ('strength','hypertrophy','muscular_endurance','power','general_fitness')", name="ck_program_goal"),
    )

    program_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    start_date: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )

    end_date: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )

    goal: Mapped[str] = mapped_column(
        String,
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String,
        nullable=False,
        default="draft"
    )

    #Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="workout_programs"
    )

    workouts: Mapped[list["WorkoutPlan"]] = relationship(
        "WorkoutPlan",
        back_populates="program",
        cascade="all, delete-orphan"
    )
