from datetime import date

from sqlalchemy import Column, Date, String, Text, false, ARRAY
from sqlalchemy.dialects.postgresql import TEXT, UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector
import uuid
from database import Base

#This class represents the enture 4 week session
#WorkoutProgram
#    │
#    ├── WorkoutPlan
#    ├── WorkoutPlan
#    ├── WorkoutPlan
class WorkoutProgram(Base):
    __tablename__ = "workout_programs"

    program_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),nullable=False)
    start_date: Mapped[date] = mapped_column(Date,nullable=False)
    end_date: Mapped[date] = mapped_column(Date,nullable=False)
    goal: Mapped[str] = mapped_column(String,nullable=False)
    status: Mapped[str] = mapped_column(String,nullable=False)