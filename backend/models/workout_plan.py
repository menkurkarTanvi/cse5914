from datetime import date

from sqlalchemy import Column, Date, String, Text, false, ARRAY
from sqlalchemy.dialects.postgresql import TEXT, UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector
import uuid
from database import Base

#This represents ONE actualy workout
class WorkoutPlan(Base):
    __tablename__ = "workout_plans"

    workout_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4)

    program_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),nullable=False)
    #Which week of the 4 week program is this workout plan for
    week_number: Mapped[int] = mapped_column(nullable=False)

    day_of_week: Mapped[str] = mapped_column(String,nullable=False)

    scheduled_date: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String,
        nullable=False
    )