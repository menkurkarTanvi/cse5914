from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Goal(str, enum.Enum):
    strength = "strength"
    hypertrophy = "hypertrophy"
    fat_loss = "fat_loss"
    endurance = "endurance"


class ExperienceLevel(str, enum.Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    display_name: Mapped[str] = mapped_column(String(100))
    goal: Mapped[Goal] = mapped_column(Enum(Goal, name="goal_enum"))
    experience_level: Mapped[ExperienceLevel] = mapped_column(Enum(ExperienceLevel, name="experience_level_enum"))
    training_block_weeks: Mapped[int] = mapped_column(Integer, default=4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    equipment: Mapped[list[Equipment]] = relationship(cascade="all, delete-orphan", back_populates="profile")
    availability: Mapped[list[Availability]] = relationship(cascade="all, delete-orphan", back_populates="profile")
    limitations: Mapped[list[Limitation]] = relationship(cascade="all, delete-orphan", back_populates="profile")


class Equipment(Base):
    __tablename__ = "profile_equipment"
    __table_args__ = (UniqueConstraint("profile_id", "name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    profile_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("profiles.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(80))
    profile: Mapped[Profile] = relationship(back_populates="equipment")


class Availability(Base):
    __tablename__ = "availability"
    __table_args__ = (UniqueConstraint("profile_id", "day_of_week"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    profile_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("profiles.id", ondelete="CASCADE"))
    day_of_week: Mapped[int] = mapped_column(Integer)
    session_minutes: Mapped[int] = mapped_column(Integer)
    profile: Mapped[Profile] = relationship(back_populates="availability")


class Limitation(Base):
    __tablename__ = "limitations"

    id: Mapped[int] = mapped_column(primary_key=True)
    profile_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("profiles.id", ondelete="CASCADE"))
    body_area: Mapped[str] = mapped_column(String(80))
    notes: Mapped[str | None] = mapped_column(String(500))
    hard_exclusion: Mapped[bool] = mapped_column(Boolean, default=True)
    profile: Mapped[Profile] = relationship(back_populates="limitations")
