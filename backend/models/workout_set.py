from datetime import date
from backend.database.database import Base



from sqlalchemy import Column, Date, String, Text, false, ARRAY
from sqlalchemy.dialects.postgresql import TEXT, UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector
import uuid
from database import Base

#Information we get from the user after they complete the workout plan for the week. 
class WorkoutSet(Base):
    __tablename__ = "workout_sets"

    set_id: Mapped[uuid.UUID] = mapped_column(
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

    set_number: Mapped[int] = mapped_column(
        nullable=False
    )

    weight: Mapped[float | None] = mapped_column(
        nullable=True
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