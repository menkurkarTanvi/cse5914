from __future__ import annotations
from datetime import date
# models.py
from sqlalchemy import Column, String, Text, false, ARRAY
from sqlalchemy.dialects.postgresql import TEXT, UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector
import uuid
from database import Base

class Exercise(Base):
    __tablename__ = "exercises"

    exercise_id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)

    # Kinetic
    type: Mapped[str] = mapped_column(String, nullable=False)
    difficulty_level: Mapped[str] = mapped_column(String, nullable=False)
    force_type: Mapped[str] = mapped_column(String, nullable=False)
    mechanics: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    instructions: Mapped[str] = mapped_column(Text, nullable=False)

    primary_muscles: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False)
    secondary_muscles: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False)
    tertiary_muscles: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False)
    equipment_required: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False)

    # FitStack enrichment
    exercise_family: Mapped[str] = mapped_column(String, nullable=False)
    movement_pattern: Mapped[str] = mapped_column(String, nullable=False)
    training_role: Mapped[list[str]] = mapped_column( ARRAY(Text), nullable=False)
    unilateral: Mapped[bool] = mapped_column(nullable=False)
    load_type: Mapped[str] = mapped_column(String, nullable=False)
    progression_methods: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False)
    substitution_group: Mapped[str | None] = mapped_column(String, nullable=True)
    goal_suitability: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False)

    mobility_requirements: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False)
    balance_requirement: Mapped[str] = mapped_column(String, nullable=False)
    stability_requirement: Mapped[str] = mapped_column(String, nullable=False)
    fatigue_cost: Mapped[str] = mapped_column(String, nullable=False)

    # pgvector
    embedding: Mapped[list[float]] = mapped_column(Vector(1536), nullable=True)

class ExercisePrescription(Base):
    __tablename__ = "exercise_prescriptions"

    prescription_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4)
    exercise_id: Mapped[str] = mapped_column(String, nullable=False)
    goal: Mapped[str] = mapped_column(String,nullable=False)
    sets_min: Mapped[int] = mapped_column(nullable=False)
    sets_max: Mapped[int] = mapped_column(nullable=False)
    reps_min: Mapped[int] = mapped_column(nullable=False)
    reps_max: Mapped[int] = mapped_column(nullable=False)
    rest_seconds: Mapped[int] = mapped_column(nullable=False)
    target_rpe_min: Mapped[float] = mapped_column(nullable=False)
    target_rpe_max: Mapped[float] = mapped_column(nullable=False)

