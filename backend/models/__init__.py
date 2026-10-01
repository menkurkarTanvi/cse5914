# Importing every model file here registers all the classes with SQLAlchemy,
# so relationships like relationship("Profile") can find each other.
from models.user import User          # noqa: F401
from models.profile import Profile    # noqa: F401
from models.exercise import *         # noqa: F401,F403