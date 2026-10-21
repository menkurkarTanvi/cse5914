"""Tunable rules for new program generation (agent/nodes/new_program.py).

Change sets/reps, splits, equipment names or injury rules here; the
generator logic itself shouldn't need to change.
"""

from __future__ import annotations

from dataclasses import dataclass


PROGRAM_WEEKS = 4
DEFAULT_WEIGHT_UNIT = "lb"

DAY_ORDER = [
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
]

# More days than this per week isn't productive for the experience level.
MAX_DAYS_BY_EXPERIENCE = {
    "beginner": 4,
    "intermediate": 5,
    "advanced": 6,
}

MAX_EXERCISES_BY_EXPERIENCE = {
    "beginner": 5,
    "intermediate": 6,
    "advanced": 7,
}

# Kinetic difficulty levels each experience level may use. Kinetic labels
# staples like Deadlift and Romanian Deadlift "intermediate", so beginners
# keep those and only "expert" is excluded.
ALLOWED_DIFFICULTY = {
    "beginner": {"beginner", "intermediate"},
    "intermediate": {"beginner", "intermediate", "unknown"},
    "advanced": {"beginner", "intermediate", "expert", "unknown"},
}

PREFERRED_DIFFICULTY = {
    "beginner": {"beginner"},
    "intermediate": {"intermediate"},
    "advanced": {"intermediate", "expert"},
}

# Kinetic categories used to build rep-based workouts. Stretching and
# cardio aren't prescribed as sets x reps, and strongman needs odd gear.
BASE_CATEGORIES = {"strength", "powerlifting"}
EXTRA_CATEGORIES_BY_GOAL = {
    "power": {"plyometrics", "olympicWeightlifting"},
    "general_fitness": {"plyometrics"},
}

# Body-only exercises are always allowed, whatever the user listed.
ALWAYS_AVAILABLE_EQUIPMENT = {"body only"}

# Kinetic equipment names (lowercased):
# body only, barbell, dumbbell, other, cable, machine, kettlebells, bands,
# medicine ball, exercise ball, foam roll, e-z curl bar
FULL_GYM_EQUIPMENT = {
    "body only", "barbell", "dumbbell", "cable", "machine", "kettlebells",
    "bands", "medicine ball", "exercise ball", "e-z curl bar", "other",
}

# Maps what users/the frontend may type onto Kinetic equipment names.
# A value that is a set expands to several pieces (frontend presets).
EQUIPMENT_ALIASES: dict[str, str | set[str]] = {
    "full gym": FULL_GYM_EQUIPMENT,
    "gym": FULL_GYM_EQUIPMENT,
    "dumbbells only": {"dumbbell", "body only"},
    "bodyweight": "body only",
    "body weight": "body only",
    "none": "body only",
    "travel / limited": {"body only", "bands"},
    "travel": {"body only", "bands"},
    "dumbbells": "dumbbell",
    "barbells": "barbell",
    "kettlebell": "kettlebells",
    "band": "bands",
    "resistance bands": "bands",
    "cables": "cable",
    "machines": "machine",
    "ez bar": "e-z curl bar",
    "ez curl bar": "e-z curl bar",
    "e-z bar": "e-z curl bar",
    "stability ball": "exercise ball",
    "swiss ball": "exercise ball",
}

# Limitations are hard exclusions. A limitation matches a rule when the
# rule's keyword appears in it ("tweaked my left knee" -> "knee"). Rules
# are deliberately conservative: when unsure, leave the exercise out.
# "names" catches exercises by name, since raw Kinetic muscle data alone
# misses some (a step-up lists glutes, not quads, as primary).
LIMITATION_RULES: dict[str, dict[str, set[str]]] = {
    "knee": {
        "families": {"squat", "lunge"},
        "muscles": {"quadriceps"},
        "categories": {"plyometrics"},
        "names": {"squat", "lunge", "step-up", "step up", "jump", "leg press", "leg extension"},
    },
    "back": {
        "families": {"hinge"},
        "muscles": {"lower back"},
        "categories": {"olympicWeightlifting"},
        "names": {"deadlift", "good morning"},
    },
    "shoulder": {
        "families": {"vertical_push"},
        "muscles": {"shoulders"},
        "mobility": {"shoulder_mobility"},
        "names": {"overhead", "military press", "shoulder press", "upright row"},
    },
    "wrist": {
        "muscles": {"forearms"},
        "mobility": {"wrist_mobility"},
    },
    "ankle": {
        "muscles": {"calves"},
        "mobility": {"ankle_mobility"},
        "categories": {"plyometrics"},
    },
    "hip": {
        "muscles": {"adductors", "abductors"},
        "mobility": {"hip_mobility"},
    },
    "neck": {
        "muscles": {"neck", "traps"},
    },
}

# Slot-ranking preference per piece of equipment. Weird or unknown gear
# ranks low; the weakest piece an exercise needs is what counts.
EQUIPMENT_PREFERENCE = {
    "barbell": 1.0,
    "dumbbell": 1.0,
    "machine": 0.75,
    "cable": 0.75,
    "e-z curl bar": 0.75,
    "kettlebells": 0.5,
    "bands": 0.25,
    "body only": 0.0,
    "medicine ball": 0.0,
    "exercise ball": -0.5,
    "foam roll": -1.0,
    "other": -1.5,
}
LOADED_GOALS = {"strength", "hypertrophy", "power"}

# Common gym movements. Kinetic has many niche variations, and before
# enrichment there is little else to tell "Barbell Squat" apart from
# "Balance Trainer Squat".
STAPLE_KEYWORDS = (
    "squat", "deadlift", "bench press", "military press", "shoulder press",
    "overhead press", "row", "pullup", "pull-up", "chin-up", "pulldown",
    "lunge", "leg press", "hip thrust", "glute bridge", "leg curl",
    "leg extension", "calf raise", "curl", "pushdown", "dip", "push-up",
    "plank", "crunch", "lateral raise", "face pull", "shrug", "step-up",
)

# Fallback (sets_min, sets_max, reps_min, reps_max, rest, rpe_min, rpe_max)
# when an exercise has no exercise_prescriptions row for the goal, e.g.
# before enrichment has run. Values mirror seed_exercise_prescription.py.
FALLBACK_PRESCRIPTIONS = {
    ("strength", True): (3, 5, 3, 6, 180, 7.0, 9.0),
    ("strength", False): (2, 4, 6, 10, 90, 7.0, 9.0),
    ("hypertrophy", True): (3, 4, 6, 12, 120, 7.0, 9.0),
    ("hypertrophy", False): (2, 4, 10, 15, 75, 7.0, 9.0),
    ("muscular_endurance", True): (2, 3, 12, 20, 60, 6.0, 8.0),
    ("muscular_endurance", False): (2, 3, 15, 20, 45, 6.0, 8.0),
    ("power", True): (3, 5, 2, 5, 180, 6.0, 8.0),
    ("power", False): (2, 4, 6, 10, 90, 7.0, 9.0),
    ("general_fitness", True): (2, 3, 8, 12, 90, 6.0, 8.0),
    ("general_fitness", False): (2, 3, 10, 15, 60, 6.0, 8.0),
}

# Rough timing used to keep each session inside the user's daily limit.
SECONDS_PER_SET = 40
SETUP_SECONDS_PER_EXERCISE = 60

# Week-over-week target RPE shift inside the block. Week 4 is a deload.
# Load progression itself happens in the current-program path, using
# what the user actually logged.
RPE_SHIFT_BY_WEEK = {1: 0.0, 2: 0.5, 3: 1.0}
DELOAD_WEEK = 4
DELOAD_SET_FACTOR = 0.6
DELOAD_RPE_DROP = 2.0
DELOAD_WEIGHT_FACTOR = 0.85


# ============================================================
# Split / slot definitions
# ============================================================

@dataclass(frozen=True)
class Slot:
    """One position in a workout, filled by the best matching exercise."""

    label: str
    muscles: frozenset[str]
    families: frozenset[str]
    compound: bool


def _slot(label: str, muscles: set[str], families: set[str], compound: bool) -> Slot:
    return Slot(label, frozenset(muscles), frozenset(families), compound)


# Slots are in priority order: when a session is short, the first slots
# (the main compound lifts) are the ones that get kept.
DAY_TEMPLATES: dict[str, list[Slot]] = {
    "full_body": [
        _slot("knee-dominant lower body", {"quadriceps"}, {"squat", "lunge"}, True),
        _slot("upper body push", {"chest"}, {"horizontal_push"}, True),
        _slot("hip hinge", {"hamstrings", "glutes"}, {"hinge"}, True),
        _slot("upper body pull", {"lats", "middle back"}, {"horizontal_pull", "vertical_pull"}, True),
        _slot("shoulders", {"shoulders"}, {"vertical_push"}, True),
        _slot("core", {"abdominals"}, {"core"}, False),
        _slot("arms", {"biceps", "triceps"}, {"isolation"}, False),
    ],
    "upper": [
        _slot("horizontal push", {"chest"}, {"horizontal_push"}, True),
        _slot("horizontal pull", {"middle back", "lats"}, {"horizontal_pull"}, True),
        _slot("vertical push", {"shoulders"}, {"vertical_push"}, True),
        _slot("vertical pull", {"lats"}, {"vertical_pull"}, True),
        _slot("biceps", {"biceps"}, {"isolation"}, False),
        _slot("triceps", {"triceps"}, {"isolation"}, False),
        _slot("rear shoulders / upper back", {"shoulders", "traps"}, {"isolation"}, False),
    ],
    "lower": [
        _slot("squat pattern", {"quadriceps"}, {"squat"}, True),
        _slot("hip hinge", {"hamstrings", "glutes"}, {"hinge"}, True),
        _slot("single-leg work", {"quadriceps", "glutes"}, {"lunge"}, True),
        _slot("hamstrings", {"hamstrings"}, {"isolation"}, False),
        _slot("calves", {"calves"}, {"calf"}, False),
        _slot("core", {"abdominals"}, {"core"}, False),
        _slot("glutes", {"glutes", "abductors", "adductors"}, {"isolation"}, False),
    ],
    "push": [
        _slot("chest press", {"chest"}, {"horizontal_push"}, True),
        _slot("overhead press", {"shoulders"}, {"vertical_push"}, True),
        _slot("chest accessory", {"chest"}, {"horizontal_push", "isolation"}, False),
        _slot("shoulder accessory", {"shoulders"}, {"isolation"}, False),
        _slot("triceps", {"triceps"}, {"isolation"}, False),
        _slot("triceps compound", {"triceps"}, {"horizontal_push", "vertical_push"}, True),
    ],
    "pull": [
        _slot("vertical pull", {"lats"}, {"vertical_pull"}, True),
        _slot("horizontal pull", {"middle back", "lats"}, {"horizontal_pull"}, True),
        _slot("upper back", {"traps", "middle back"}, {"horizontal_pull", "isolation"}, False),
        _slot("biceps", {"biceps"}, {"isolation"}, False),
        _slot("lower back", {"lower back"}, {"hinge", "core"}, False),
        _slot("forearms / grip", {"forearms", "biceps"}, {"isolation", "carry"}, False),
    ],
    "legs": [
        _slot("squat pattern", {"quadriceps"}, {"squat"}, True),
        _slot("hip hinge", {"hamstrings", "glutes"}, {"hinge"}, True),
        _slot("single-leg work", {"quadriceps", "glutes"}, {"lunge"}, True),
        _slot("quadriceps", {"quadriceps"}, {"isolation"}, False),
        _slot("hamstrings", {"hamstrings"}, {"isolation"}, False),
        _slot("calves", {"calves"}, {"calf"}, False),
        _slot("core", {"abdominals"}, {"core"}, False),
    ],
}

# Which day types to train for a given number of sessions per week.
SPLITS_BY_DAYS = {
    1: ["full_body"],
    2: ["full_body", "full_body"],
    3: ["full_body", "full_body", "full_body"],
    4: ["upper", "lower", "upper", "lower"],
    5: ["upper", "lower", "push", "pull", "legs"],
    6: ["push", "pull", "legs", "push", "pull", "legs"],
}
