from __future__ import annotations

import uuid

from sqlalchemy import (
    ARRAY,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import TEXT
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from database.database import Base


class Exercise(Base):
    __tablename__ = "exercises"

    # -------------------------
    # Kinetic Exercise DB
    # -------------------------

    exercise_id: Mapped[str] = mapped_column(
        String,
        primary_key=True
    )

    name: Mapped[str] = mapped_column(
        String,
        nullable=False
    )

    type: Mapped[str] = mapped_column(
        String,
        nullable=False
    )

    difficulty_level: Mapped[str] = mapped_column(
        String,
        nullable=False
    )

    force_type: Mapped[str] = mapped_column(
        String,
        nullable=False
    )

    mechanics: Mapped[str] = mapped_column(
        String,
        nullable=False
    )

    category: Mapped[str] = mapped_column(
        String,
        nullable=False
    )

    instructions: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    primary_muscles: Mapped[list[str]] = mapped_column(
        ARRAY(Text),
        nullable=False
    )

    secondary_muscles: Mapped[list[str]] = mapped_column(
        ARRAY(Text),
        nullable=False
    )

    tertiary_muscles: Mapped[list[str]] = mapped_column(
        ARRAY(Text),
        nullable=False
    )

    equipment_required: Mapped[list[str]] = mapped_column(
        ARRAY(Text),
        nullable=False
    )

    # -------------------------
    # FitStack enrichment
    # -------------------------

    # These start as NULL because they will
    # be populated during your enrichment step.

    exercise_family: Mapped[str | None] = mapped_column(
        String,
        nullable=True
    )

    movement_pattern: Mapped[str | None] = mapped_column(
        String,
        nullable=True
    )

    training_role: Mapped[list[str] | None] = mapped_column(
        ARRAY(Text),
        nullable=True
    )

    unilateral: Mapped[bool | None] = mapped_column(
        nullable=True
    )

    load_type: Mapped[str | None] = mapped_column(
        String,
        nullable=True
    )

    progression_methods: Mapped[list[str] | None] = mapped_column(
        ARRAY(Text),
        nullable=True
    )

    substitution_group: Mapped[str | None] = mapped_column(
        String,
        nullable=True
    )

    goal_suitability: Mapped[list[str] | None] = mapped_column(
        ARRAY(Text),
        nullable=True
    )

    mobility_requirements: Mapped[list[str] | None] = mapped_column(
        ARRAY(Text),
        nullable=True
    )

    balance_requirement: Mapped[str | None] = mapped_column(
        String,
        nullable=True
    )

    stability_requirement: Mapped[str | None] = mapped_column(
        String,
        nullable=True
    )

    fatigue_cost: Mapped[str | None] = mapped_column(
        String,
        nullable=True
    )

    # -------------------------
    # Search / embeddings
    # -------------------------

    searchable_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(1536),
        nullable=True
    )

    embedding_model: Mapped[str | None] = mapped_column(
        String,
        nullable=True
    )

    # -------------------------
    # Relationships
    # -------------------------

    prescriptions: Mapped[list["ExercisePrescription"]] = relationship(
        "ExercisePrescription",
        back_populates="exercise",
        cascade="all, delete-orphan"
    )

    workout_plan_exercises: Mapped[list["WorkoutPlanExercise"]] = relationship(
        "WorkoutPlanExercise",
        back_populates="exercise"
    )


