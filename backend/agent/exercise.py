from typing import TypedDict


class ExerciseMuscleEmphasis(TypedDict):
    muscle: str
    emphasis: str  # "low", "moderate", "high"


class ExerciseAlternative(TypedDict):
    equipment: list[str]
    substitute_exercise_id: str
    substitute_name: str


class ExerciseDifficulty(TypedDict):
    level: str
    minimum_experience_months: int
    technical_complexity: str
    coordination_requirement: str
    stability_requirement: str


class ExercisePhysicalRequirements(TypedDict):
    mobility_requirements: list[str]
    range_of_motion: str
    balance_requirement: str
    core_demand: str
    cardiovascular_demand: str
    fatigue_cost: str


class ExerciseSafety(TypedDict):
    contraindications: list[str]
    caution_flags: list[str]
    safe_for_injury_flags: list[str]
    requires_professional_clearance: bool


class RepRange(TypedDict):
    min: int
    max: int


class GoalProgramming(TypedDict):
    sets: RepRange
    reps: RepRange
    rest_seconds: RepRange
    target_rpe: RepRange


class ExerciseProgramming(TypedDict):
    suitable_goals: list[str]
    not_ideal_for: list[str]

    strength: GoalProgramming
    hypertrophy: GoalProgramming
    endurance: GoalProgramming


class ExerciseLoading(TypedDict):
    load_type: list[str]
    loadable: bool

    progression_methods: list[str]

    deload_compatible: bool
    minimum_load_increment: float | None


class ExerciseSubstitution(TypedDict):
    replaceable: bool

    substitution_priority: list[str]

    acceptable_variation: str


class ExercisePairing(TypedDict):
    superset_compatible: bool
    good_pairings: list[str]
    avoid_pairing_with: list[str]


class ExerciseMedia(TypedDict):
    video_url: str | None
    thumbnail_url: str | None
    gif_url: str | None


class ExerciseSource(TypedDict):
    provider: str
    license: str
    last_reviewed: str


class Exercise(TypedDict):
    # Identity
    id: str
    name: str
    aliases: list[str]

    exercise_family: str
    variant_of: str | None

    # Classification
    movement_pattern: str
    secondary_movement_patterns: list[str]

    exercise_type: str
    mechanics: str
    unilateral: bool
    force_type: str

    body_region: str
    primary_region: str

    training_role: list[str]

    # Muscles
    primary_muscles: list[str]
    secondary_muscles: list[str]
    stabilizers: list[str]
    muscle_emphasis: list[ExerciseMuscleEmphasis]

    # Equipment
    equipment_required: list[str]
    equipment_optional: list[str]
    equipment_alternatives: list[ExerciseAlternative]

    # Difficulty
    difficulty: ExerciseDifficulty

    # Physical requirements
    physical_requirements: ExercisePhysicalRequirements

    # Safety
    safety: ExerciseSafety

    # Programming
    programming: ExerciseProgramming

    # Loading / progression
    loading: ExerciseLoading

    # Substitution
    substitution: ExerciseSubstitution

    # Pairing
    pairing: ExercisePairing

    # Coaching
    instructions: list[str]
    coaching_cues: list[str]
    common_mistakes: list[str]

    # Media
    media: ExerciseMedia

    # Search
    tags: list[str]
    searchable_text: str

    # Data source
    source: ExerciseSource