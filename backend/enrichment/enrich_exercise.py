# enrichment/enrich_exercise.py

from sqlalchemy.ext.asyncio import AsyncSession

from models.exercise import Exercise

from .openai_client import enrich_with_openai
from .searchable_text import build_searchable_text
from .embeddings import generate_embedding, EMBEDDING_MODEL


async def enrich_exercise(
    db: AsyncSession,
    exercise: Exercise,
) -> Exercise:
    """Enrich an exercise and generate its embedding."""

    # 1. Generate structured exercise metadata.
    enrichment = await enrich_with_openai(exercise)

    exercise.exercise_family = enrichment.exercise_family
    exercise.movement_pattern = enrichment.movement_pattern
    exercise.training_role = enrichment.training_role
    exercise.unilateral = enrichment.unilateral
    exercise.load_type = enrichment.load_type
    exercise.progression_methods = enrichment.progression_methods
    exercise.substitution_group = enrichment.substitution_group
    exercise.goal_suitability = enrichment.goal_suitability
    exercise.mobility_requirements = enrichment.mobility_requirements
    exercise.balance_requirement = enrichment.balance_requirement
    exercise.stability_requirement = enrichment.stability_requirement
    exercise.fatigue_cost = enrichment.fatigue_cost

    # 2. Create searchable text after updating metadata.
    exercise.searchable_text = build_searchable_text(exercise)

    # 3. Generate embedding from the searchable text.
    exercise.embedding = await generate_embedding(
        exercise.searchable_text
    )

    # 4. Record which model generated the vector.
    exercise.embedding_model = EMBEDDING_MODEL

    db.add(exercise)

    # The caller handles commit/rollback.
    return exercise