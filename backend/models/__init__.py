# Importing every model file here registers all the classes with SQLAlchemy,
# so relationships like relationship("Profile") can find each other.
from models.user import User
from models.profile import Profile
from models.user_availability import UserAvailability
from models.exercise import Exercise
from models.exercise_prescription import ExercisePrescription
from models.workout_program import WorkoutProgram
from models.workout_plan import WorkoutPlan
from models.workout_plan_exercise import WorkoutPlanExercise
from models.workout_set import WorkoutSet
from models.workout_feedback import WorkoutFeedback