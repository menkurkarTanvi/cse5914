from __future__ import annotations
from datetime import date
from typing import TYPE_CHECKING
# models.py
from sqlalchemy import Column, String, Text, UniqueConstraint, false, ARRAY, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import TEXT, UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector
import uuid
from database.database import Base

class UserAvailability(Base):
    __tablename__ = "user_availability"

    availability_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    day_of_week: Mapped[str] = mapped_column(
        String,
        nullable=False
    )

    is_available: Mapped[bool] = mapped_column(
        nullable=False,
        default=True
    )

    max_duration_minutes: Mapped[int | None] = mapped_column(
        nullable=True
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="availability"
    )

    __table_args__ = (
        CheckConstraint("lower(day_of_week) IN ('monday','tuesday','wednesday','thursday','friday','saturday','sunday')", name="ck_availability_day"),
        CheckConstraint("max_duration_minutes IS NULL OR max_duration_minutes BETWEEN 1 AND 300", name="ck_availability_duration"),
        UniqueConstraint(
            "user_id",
            "day_of_week",
            name="uq_user_availability_day"
        ),
    )
