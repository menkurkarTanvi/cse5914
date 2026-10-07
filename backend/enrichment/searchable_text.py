#This the function to build the searchable text for an exercise. 
def build_searchable_text(exercise) -> str:

    parts = [
        exercise.name,
        exercise.type,
        exercise.difficulty_level,
        exercise.force_type,
        exercise.mechanics,
        exercise.category,
        exercise.instructions,

        "Primary muscles: "
        + ", ".join(exercise.primary_muscles or []),

        "Secondary muscles: "
        + ", ".join(exercise.secondary_muscles or []),

        "Equipment: "
        + ", ".join(exercise.equipment_required or []),

        f"Exercise family: {exercise.exercise_family}",
        f"Movement pattern: {exercise.movement_pattern}",

        "Training role: "
        + ", ".join(exercise.training_role or []),

        f"Load type: {exercise.load_type}",

        "Progression methods: "
        + ", ".join(exercise.progression_methods or []),

        f"Substitution group: {exercise.substitution_group}",

        "Goals: "
        + ", ".join(exercise.goal_suitability or []),

        "Mobility requirements: "
        + ", ".join(exercise.mobility_requirements or []),

        f"Balance requirement: {exercise.balance_requirement}",
        f"Stability requirement: {exercise.stability_requirement}",
        f"Fatigue cost: {exercise.fatigue_cost}",
    ]

    return "\n".join(
        part for part in parts
        if part
    )