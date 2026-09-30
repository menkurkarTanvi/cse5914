from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.dependencies import get_db
from backend.services.user_service import User_Service
# Prefix tag
router = APIRouter(
    prefix="/users",
    tags=["users"]
)

@router.get("/login")
def get_current_user(db: Session = Depends(get_db)):
    #Get the current user from the database based on provided credentials 
    #If the user is not found, raise an HTTPException with a 401 status code 

    #Verify the user password with the hashed password store in the database. If the password is incorrect, raise an HTTPException with a 401 status code.
    return {"message": "Login successful!"}

@router.post("/register")
def register_user(db: Session = Depends(get_db)):
    #Register a new user in the database with the provided credentials.
    user_service = User_Service(db)
    return {"message": "User registered successfully!"}
