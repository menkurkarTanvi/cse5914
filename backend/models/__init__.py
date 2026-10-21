# Importing every model file here registers all the classes with SQLAlchemy,
# so relationships like relationship("Profile") can find each other.
from models.user import User  # noqa: F401
from models.profile import Profile  # noqa: F401
from models.user_availability import UserAvailability  # noqa: F401
from models.exercise import Exercise  # noqa: F401
from models.exercise_prescription import ExercisePrescription  # noqa: F401
from models.workout_program import WorkoutProgram  # noqa: F401
from models.workout_plan import WorkoutPlan  # noqa: F401
from models.workout_plan_exercise import WorkoutPlanExercise  # noqa: F401
from models.workout_set import WorkoutSet  # noqa: F401
from models.workout_feedback import WorkoutFeedback  # noqa: F401