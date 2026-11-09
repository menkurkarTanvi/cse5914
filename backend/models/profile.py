from __future__ import annotations
from datetime import date
from typing import TYPE_CHECKING
# models.py
from sqlalchemy import Column, ForeignKey, String, Text, false, ARRAY, CheckConstraint
from sqlalchemy.dialects.postgresql import TEXT, UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector
import uuid
from database.database import Base


#The user profile information
class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # One-to-one relationship with User
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), 
        unique=True,
        nullable=False
    )

    goal: Mapped[str] = mapped_column(
        String,
        nullable=False
    )

    experience_level: Mapped[str] = mapped_column(
        String,
        nullable=False
    )

    available_equipment: Mapped[list[str]] = mapped_column(
        ARRAY(Text),
        nullable=False,
        default=list
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

    #------Relationships

    user: Mapped["User"] = relationship(
        "User",
        back_populates="profile"
    )

    __table_args__ = (
        CheckConstraint("goal IN ('strength','hypertrophy','muscular_endurance','power','general_fitness')", name="ck_profile_goal"),
        CheckConstraint("experience_level IN ('beginner','intermediate','advanced')", name="ck_profile_experience"),
    )
