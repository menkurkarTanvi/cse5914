from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from database.models import ExperienceLevel, Goal

EquipmentName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)]


class AvailabilityInput(BaseModel):
    day_of_week: int = Field(ge=0, le=6, description="Monday=0, Sunday=6")
    session_minutes: int = Field(ge=15, le=240)


class LimitationInput(BaseModel):
    body_area: str = Field(min_length=1, max_length=80)
    notes: str | None = Field(default=None, max_length=500)
    hard_exclusion: bool = True


class ProfileCreate(BaseModel):
    display_name: str = Field(min_length=1, max_length=100)
    goal: Goal
    experience_level: ExperienceLevel
    training_block_weeks: int = Field(default=4, ge=1, le=12)
    equipment: list[EquipmentName] = Field(default_factory=list)
    availability: list[AvailabilityInput] = Field(default_factory=list)
    limitations: list[LimitationInput] = Field(default_factory=list)


class EquipmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str


class AvailabilityRead(AvailabilityInput):
    model_config = ConfigDict(from_attributes=True)


class LimitationRead(LimitationInput):
    model_config = ConfigDict(from_attributes=True)


class ProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    display_name: str
    goal: Goal
    experience_level: ExperienceLevel
    training_block_weeks: int
    equipment: list[EquipmentRead]
    availability: list[AvailabilityRead]
    limitations: list[LimitationRead]
