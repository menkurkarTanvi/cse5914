from __future__ import annotations
# models.py
from sqlalchemy import Column, String, Text, false
from sqlalchemy.dialects.postgresql import TEXT, UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector
import uuid
from database import Base

#Exercise table model
class Exercise(Base):
    __tablename__ = "exercises"
    # Kinetic data
    exercise_id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[str] = mapped_column(String, nullable=False)
    difficulty_level: Mapped[str] = mapped_column(String, nullable=False)
    force_type: Mapped[str] = mapped_column(String, nullable=False)
    mechanics: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    instructions: Mapped[str] = mapped_column(String, nullable=False)

    # Kinetic muscle/equipment data
    primary_muscles: Mapped[list[str]] = mapped_column(TEXT[], nullable=False)
    secondary_muscles: Mapped[list[str]] = mapped_column(TEXT[], nullable=False)
    tertiary_muscles: Mapped[list[str]] = mapped_column(TEXT[], nullable=False)
    equipment_required: Mapped[list[str]] = mapped_column(TEXT[], nullable=False)

    # FitStack enrichment --> llm uses the data to generate the input for these attributes
    exercise_family: str
    movement_pattern: str
    training_role: list[str]
    unilateral: bool
    load_type: str
    progression_methods: list[str]
    substitution_group: str | None
    goal_suitability: list[str]
    fatigue_cost: str
    mobility_requirements: list[str]

#Class for workout tailored to user 
class ExercisePrescription(Base):
    __tablename__ = "exercise_prescriptions"
    exercise_id: Mapped[str] = mapped_column(String, primary_key=True)
    sets: int
    reps_min: int
    reps_max: int
    rest_seconds: int
    target_rpe: float

#User profile model
class Profile(Base):
    __tablename__ = "profiles"

class WorkoutPlan(Base):
    __tablename__ = "workout_plans"
    workout_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    week_number: Mapped[int] = mapped_column(nullable=False)
    day_of_week: Mapped[str] = mapped_column(nullable=False)
    


class WorkoutHistory(Base):
    __tablename__ = "workout_history"
    workout_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)



