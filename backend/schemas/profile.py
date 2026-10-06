from pydantic import BaseModel

class ProfileRequest(BaseModel):
    pass

#-----------------------------------------------------------------------

class Exercise(BaseModel):
    pass

class WorkOutPlan(BaseModel):
    day_of_week: str
    description: str
    exercises: list[Exercise]

class WorkOutPlanResponse(BaseModel):
    workout_plan_description: str
    workout_plan_list: list[WorkOutPlan]

