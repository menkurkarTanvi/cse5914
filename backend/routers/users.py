from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from services.user_service import User_Service
from schemas.user import LoginRequest, SignUpRequest
from database.database import get_db
# Prefix tag
router = APIRouter(
    prefix="/users",
    tags=["users"]
)

@router.post("/login")
async def get_current_user(credentials: LoginRequest, db: AsyncSession = Depends(get_db)):
    #Get the current user from the database based on provided credentials 
    user_service = User_Service(db)
    user = await user_service.get_user_by_email(credentials.email)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    #Verify the user password with the hashed password store in the database. If the password is incorrect, raise an HTTPException with a 401 status code.
    if not await user_service.verify_password(credentials.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    #If the credentials are valid, return jwt token to the user. The token can be used for subsequent requests to authenticate the user.
    token = await user_service.create_access_token(data={"sub": str(user.id)})
    return {"message": "Login successful!", "token": token}

@router.post("/register")
async def register_user(credentials: SignUpRequest, db: AsyncSession = Depends(get_db)):
    #Register a new user in the database with the provided credentials.
    user_service = User_Service(db)
    await user_service.register_new_user(credentials.email, credentials.password)
    return {"message": "User registered successfully!"}
