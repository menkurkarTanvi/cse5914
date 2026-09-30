from datetime import date

from sqlalchemy import Column, Date, String, Text, false, ARRAY
from sqlalchemy.dialects.postgresql import TEXT, UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector
import uuid
from database import Base

class WorkoutFeedback(Base):
    __tablename__ = "workout_feedback"

    feedback_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    workout_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
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