from typing import Literal
from pydantic import BaseModel, Field


ExerciseFamily = Literal[
    "squat",
    "hinge",
    "lunge",
    "horizontal_push",
    "horizontal_pull",
    "vertical_push",
    "vertical_pull",
    "carry",
    "core",
    "isolation",
    "calf",
    "conditioning",
    "mobility",
    "other",
]


MovementPattern = Literal[
    "squat",
    "hinge",
    "lunge",
    "horizontal_push",
    "horizontal_pull",
    "vertical_push",
    "vertical_pull",
    "carry",
    "rotation",
    "anti_rotation",
    "anti_extension",
    "anti_flexion",
    "isolation",
    "locomotion",
    "other",
]


TrainingRole = Literal[
    "primary_compound",
    "secondary_compound",
    "accessory",
    "isolation",
    "core",
    "conditioning",
    "mobility",
]


LoadType = Literal[
    "bodyweight",
    "free_weight",
    "machine",
    "cable",
    "band",
    "weighted_bodyweight",
    "assisted",
    "other",
]


ProgressionMethod = Literal[
    "increase_weight",
    "increase_reps",
    "increase_sets",
    "increase_time",
    "increase_distance",
    "reduce_assistance",
    "increase_range_of_motion",
]


Goal = Literal[
    "strength",
    "hypertrophy",
    "muscular_endurance",
    "power",
    "general_fitness",
]


MobilityRequirement = Literal[
    "ankle_mobility",
    "hip_mobility",
    "thoracic_mobility",
    "shoulder_mobility",
    "wrist_mobility",
    "hamstring_mobility",
    "none",
]


DifficultyLevel = Literal[
    "low",
    "medium",
    "high",
]


class ExerciseEnrichment(BaseModel):
    exercise_family: ExerciseFamily
    movement_pattern: MovementPattern
    training_role: list[TrainingRole]
    unilateral: bool
    load_type: LoadType
    progression_methods: list[ProgressionMethod]
    substitution_group: str
    goal_suitability: list[Goal]
    mobility_requirements: list[MobilityRequirement]
    balance_requirement: DifficultyLevel
    stability_requirement: DifficultyLevel
    fatigue_cost: DifficultyLevel