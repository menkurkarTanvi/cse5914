from pydantic import BaseModel

#This is the Pydantic model to validate the request body from the frontend for user login.
#If the request body does not match the expected format, FastAPI will automatically return a 422 Unprocessable Entity response.
class LoginRequest(BaseModel):
    email: str
    password: str

class SignUpRequest(BaseModel):
    email: str
    password: str
