from __future__ import annotations
from datetime import date
# models.py
from sqlalchemy import Column, String, Text, false, ARRAY
from sqlalchemy.dialects.postgresql import TEXT, UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector
import uuid
from database import Base

#The user profile information
class Profile(Base):
    __tablename__ = "profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    goal: Mapped[str] = mapped_column(
        String,
        nullable=False
    )

    experience_level: Mapped[str] = mapped_column(
        String,
        nullable=False
    )

    days_per_week: Mapped[int] = mapped_column(
        nullable=False
    )

    session_duration_minutes: Mapped[int] = mapped_column(
        nullable=False
    )

    available_equipment: Mapped[list[str]] = mapped_column(
        ARRAY(Text),
        nullable=False
    )

    preferred_exercises: Mapped[list[str]] = mapped_column(
        ARRAY(Text),
        nullable=False,
        default=list
    )

    disliked_exercises: Mapped[list[str]] = mapped_column(
        ARRAY(Text),
        nullable=False,
        default=list
    )

    limitations: Mapped[list[str]] = mapped_column(
        ARRAY(Text),
        nullable=False,
        default=list
    )
