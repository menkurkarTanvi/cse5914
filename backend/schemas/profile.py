from pydantic import BaseModel

class Availability(BaseModel):
    day_of_week: str
    max_availability: int

class ProfileRequest(BaseModel):
    weekly_availability: list[Availability]
    pass



#-----------------------------------------------------------------------

