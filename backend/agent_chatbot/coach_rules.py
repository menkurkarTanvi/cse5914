
import re

# Tunable values for the AI coach (agent/nodes/coach*.py), kept apart from
# the logic the same way program_rules.py is for program generation.


# ============================================================
# Reading messages
# ============================================================

# The details each follow-up question asks for. A reply only continues the
# earlier request if it supplies one of them.
FOLLOW_UP_FIELDS = {
    "swap_exercise": ("exercise_name",),
    "shorten_workout": ("minutes_available",),
    "adjust_difficulty": ("difficulty_direction", "exercise_name", "whole_workout"),
    "exercise_question": ("exercise_name",),
}

WHOLE_WORKOUT = re.compile(r"\b(?:whole|entire)\b|\beverything\b|\ball of (?:it|them)\b|\ball (?:the )?exercises\b")

# Numbers followed by these are counts, not minutes ("3 exercises", "2 dumbbells").
NOT_MINUTES = r"\s*(?:exercises?|sets?|reps?|lbs?|kgs?|kilos?|pounds?|dumbbells?|days?|weeks?|times?|x)\b"

STOP_WORDS = {"the", "a", "an", "my", "of", "to", "with", "on", "and", "exercise", "exercises", "today", "todays"}

# ============================================================
# Swaps
# ============================================================

SWAP_OPTION_COUNT = 3

# Equipment counts as unavailable only when one of these sits right next to
# it: "no barbell", "don't have dumbbells", "the cable machine is taken".
UNAVAILABLE_BEFORE = (
    r"\b(?:no|without|don'?t have|do not have|haven'?t got|can'?t use|cannot use|no access to)"
    r"\s+(?:a |an |any |the |my )?(?:\w+ )?"
)

UNAVAILABLE_AFTER = (
    r"s?\s+(?:\w+\s+)?(?:is|are|'s)\s+(?:all\s+)?"
    r"(?:busy|taken|broken|in use|occupied|unavailable|not available|out of order)\b"
)

# A reason only becomes an injury limitation when it mentions pain.
PAIN_WORDS = (
    "pain", "hurt", "sore", "injur", "tweak", "ache", "strain", "sprain",
    "pulled", "tender", "twinge", "aggravat", "bad ",
)

# ============================================================
# Shorten and adjust
# ============================================================

MIN_SETS = 1

ACCESSORY_MIN_SETS = 2

MAX_SETS = 6

HARDER_WEIGHT_FACTOR = 1.05

EASIER_WEIGHT_FACTOR = 0.9

HARDER_RPE_SHIFT = 0.5

EASIER_RPE_SHIFT = -1.0

# ============================================================
# Pending actions
# ============================================================

PENDING_ACTION_MINUTES = 30

PENDING_ACTION_AUDIENCE = "coach_pending_action"
