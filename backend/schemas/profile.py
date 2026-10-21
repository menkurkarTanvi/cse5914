from typing import Literal

from pydantic import BaseModel, Field, model_validator
from pydantic import ConfigDict

# Keep these vocabularies in sync with the rest of the app:
# Goal matches ExercisePrescription.goal / the enrichment Goal literal,
# and analyze_starting_point checks experience_level == "beginner".
Goal = Literal[
    "strength",
    "hypertrophy",
    "muscular_endurance",
    "power",
    "general_fitness",
]

ExperienceLevel = Literal["beginner", "intermediate", "advanced"]

DayOfWeek = Literal[
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]


class AvailabilityRequest(BaseModel):
    """One row of UserAvailability."""

    day_of_week: DayOfWeek
    is_available: bool = True
    max_duration_minutes: int | None = Field(default=None, gt=0, le=300)


class ProfileRequest(BaseModel):
    """Profile fields the user supplies. user_id comes from the JWT, never the body."""

    goal: Goal
    experience_level: ExperienceLevel
    available_equipment: list[str] = Field(default_factory=list)
    preferred_exercises: list[str] = Field(default_factory=list)
    disliked_exercises: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class CreateProfileRequest(BaseModel):
    """Single request body for /createProfile: profile plus weekly availability."""

    profile: ProfileRequest
    availability: list[AvailabilityRequest] = Field(min_length=1, max_length=7)

    @model_validator(mode="after")
    def validate_availability(self):
        days = [entry.day_of_week for entry in self.availability]

        # Mirrors the uq_user_availability_day unique constraint, so the
        # client gets a clean 422 instead of a database IntegrityError.
        if len(days) != len(set(days)):
            raise ValueError("Each day_of_week may appear only once")

        # analyze_starting_point can't build a program with zero days.
        if not any(entry.is_available for entry in self.availability):
            raise ValueError("At least one day must be available")

        return self


#---------------------------------------------------------------------------------------------------------

class AvailabilityResponse(AvailabilityRequest):
    model_config = ConfigDict(from_attributes=True)

class ProfileResponse(ProfileRequest):
    model_config = ConfigDict(from_attributes=True)

class ProfileWithAvailabilityResponse(BaseModel):
    profile: ProfileResponse
    availability: list[AvailabilityResponse]

