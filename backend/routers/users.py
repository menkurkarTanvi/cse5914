from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from services.user_service import User_Service
from schemas.user import LoginRequest, SignUpRequest
from database.database import get_db
from core.auth import create_access_token
# Prefix tag
router = APIRouter(
    prefix="/users",
    tags=["users"]
)

@router.post("/login")
async def login(credentials: LoginRequest, db: AsyncSession = Depends(get_db)):
    user_service = User_Service(db)
    user = await user_service.get_user_by_email(credentials.email)

    # Always verify against *something* so a missing user and a wrong
    # password take the same amount of time — prevents timing-based
    # email enumeration.
    hashed_password = user.hashed_password
    password_valid = await user_service.verify_password(
        credentials.password, hashed_password
    )
    #Check if the user exists and the password is valid. 
    if not user or not password_valid:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = await create_access_token(data={"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}


@router.post("/register", status_code=201)
async def register_user(credentials: SignUpRequest, db: AsyncSession = Depends(get_db)):
    user_service = User_Service(db)
    await user_service.register_new_user(credentials.email, credentials.password)
    return {"message": "User registered successfully!"}
