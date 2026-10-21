
# seed_exercise_prescriptions.py

import argparse
import asyncio

# Import the model package first to register SQLAlchemy relationships.
import models

from sqlalchemy import select

from database.database import AsyncSessionLocal
from models.exercise import Exercise
from models.exercise_prescription import ExercisePrescription

#Run Preview 10 exercises without saving anything : python seed_exercise_prescriptions.py --limit 10 --dry-run
#Actual run: python seed_exercise_prescriptions.py --limit 10
#Complete run: python seed_exercise_prescriptions.py
GOALS = (
    "strength",
    "hypertrophy",
    "muscular_endurance",
    "power",
    "general_fitness",
)


def get_prescription_template(
    exercise: Exercise,
    goal: str,
) -> dict[str, int | float] | None:
    """
    Return baseline programming guidance for an exercise and goal.

    Returns None for exercises that aren't suitable for this
    rep-based prescription table, such as mobility-only or
    conditioning-only exercises.
    """

    roles = set(exercise.training_role or [])

    if not roles:
        return None

    # This table stores set/rep prescriptions, not duration- or
    # distance-based prescriptions.
    if roles.issubset({"conditioning", "mobility"}):
        return None

    family = (exercise.exercise_family or "").lower()

    is_compound = bool(
        roles.intersection({"primary_compound", "secondary_compound"})
    )
    is_isolation = "isolation" in roles or family == "isolation"
    is_core = "core" in roles or family == "core"
    is_accessory = "accessory" in roles

    # Power prescriptions are reserved for compound exercises
    # identified by the enrichment metadata.
    if goal == "power" and not is_compound:
        return None

    # Return values matching ExercisePrescription's columns.
    if goal == "strength":
        if is_core:
            values = (2, 3, 8, 12, 60, 6.0, 8.0)
        elif is_isolation or is_accessory:
            values = (2, 4, 6, 10, 90, 7.0, 9.0)
        else:
            values = (3, 5, 3, 6, 180, 7.0, 9.0)

    elif goal == "hypertrophy":
        if is_core:
            values = (2, 4, 8, 15, 60, 7.0, 9.0)
        elif is_isolation or is_accessory:
            values = (2, 4, 10, 15, 75, 7.0, 9.0)
        else:
            values = (3, 4, 6, 12, 120, 7.0, 9.0)

    elif goal == "muscular_endurance":
        if is_isolation:
            values = (2, 3, 15, 20, 45, 6.0, 8.0)
        else:
            values = (2, 3, 12, 20, 60, 6.0, 8.0)

    elif goal == "power":
        values = (3, 5, 2, 5, 180, 6.0, 8.0)

    elif goal == "general_fitness":
        if is_core:
            values = (2, 3, 8, 15, 60, 6.0, 8.0)
        elif is_isolation or is_accessory:
            values = (2, 3, 10, 15, 60, 6.0, 8.0)
        else:
            values = (2, 3, 8, 12, 90, 6.0, 8.0)

    else:
        return None

    (
        sets_min,
        sets_max,
        reps_min,
        reps_max,
        rest_seconds,
        target_rpe_min,
        target_rpe_max,
    ) = values

    return {
        "sets_min": sets_min,
        "sets_max": sets_max,
        "reps_min": reps_min,
        "reps_max": reps_max,
        "rest_seconds": rest_seconds,
        "target_rpe_min": target_rpe_min,
        "target_rpe_max": target_rpe_max,
    }


async def seed_prescriptions(
    limit: int | None = None,
    dry_run: bool = False,
) -> None:
    async with AsyncSessionLocal() as db:
        # Load enriched exercises.
        statement = select(Exercise).order_by(Exercise.name)

        if limit is not None:
            statement = statement.limit(limit)

        result = await db.execute(statement)
        exercises = result.scalars().all()

        # Find existing exercise/goal pairs to prevent duplicates.
        existing_result = await db.execute(
            select(
                ExercisePrescription.exercise_id,
                ExercisePrescription.goal,
            )
        )

        existing_keys = {
            (exercise_id, goal)
            for exercise_id, goal in existing_result.all()
        }

        new_prescriptions = []
        skipped_existing = 0
        skipped_missing_goals = 0
        skipped_unsupported = 0
        unknown_goals: set[str] = set()

        for exercise in exercises:
            supported_goals = set(exercise.goal_suitability or [])

            if not supported_goals:
                skipped_missing_goals += 1
                continue

            unknown_goals.update(supported_goals - set(GOALS))

            for goal in GOALS:
                if goal not in supported_goals:
                    continue

                key = (exercise.exercise_id, goal)

                if key in existing_keys:
                    skipped_existing += 1
                    continue

                template = get_prescription_template(exercise, goal)

                if template is None:
                    skipped_unsupported += 1
                    continue

                new_prescriptions.append(
                    ExercisePrescription(
                        exercise_id=exercise.exercise_id,
                        goal=goal,
                        **template,
                    )
                )

                # Prevent duplicates within this batch too.
                existing_keys.add(key)

        print(f"Exercises examined: {len(exercises)}")
        print(f"New prescriptions prepared: {len(new_prescriptions)}")
        print(f"Existing prescriptions skipped: {skipped_existing}")
        print(f"Exercises without goal metadata: {skipped_missing_goals}")
        print(f"Unsupported combinations skipped: {skipped_unsupported}")

        if unknown_goals:
            print(f"Unexpected goal values: {sorted(unknown_goals)}")

        # Preview a few rows before writing anything.
        for prescription in new_prescriptions[:10]:
            exercise = next(
                ex for ex in exercises
                if ex.exercise_id == prescription.exercise_id
            )
            print(
                f"Preview: {exercise.name} | {prescription.goal} | "
                f"{prescription.sets_min}-{prescription.sets_max} sets | "
                f"{prescription.reps_min}-{prescription.reps_max} reps | "
                f"rest={prescription.rest_seconds}s | "
                f"RPE={prescription.target_rpe_min}-"
                f"{prescription.target_rpe_max}"
            )

        if dry_run:
            print("DRY RUN: no database records were saved.")
            return

        db.add_all(new_prescriptions)
        await db.commit()

        print(f"Successfully inserted {len(new_prescriptions)} prescriptions.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Seed baseline exercise prescriptions."
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit the number of exercises examined.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without inserting records.",
    )

    args = parser.parse_args()

    asyncio.run(
        seed_prescriptions(
            limit=args.limit,
            dry_run=args.dry_run,
        )
    )
