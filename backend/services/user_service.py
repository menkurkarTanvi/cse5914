from fastapi import HTTPException
from sqlalchemy.orm import Session
from models.user import User
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher
import jwt
from datetime import datetime, timedelta, timezone
from typing import Any
from sqlalchemy import select
import os
from dotenv import load_dotenv
load_dotenv()

class User_Service:
    # Initialize the PasswordHash instance with Argon2
    password_hash = PasswordHash((Argon2Hasher(),))
    def __init__(self, db: Session):
        self.db = db

    async def create_access_token(self, data: dict, expires_delta: timedelta = timedelta(minutes=15)) -> str:
        # Create a JWT access token with the provided data and expiration time.
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + expires_delta
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, os.getenv("SECRET_KEY"), algorithm="HS256")
        return encoded_jwt

    async def hash_password(self, password: str) -> str:
        # Hash the provided password using a secure hashing algorithm (e.g., bcrypt) and return the hashed password.
        return self.password_hash.hash(password)

    #Function to register a new user with password and email
    async def register_new_user(self, email: str, password: str):
        # Check if the user already exists in the database, if it does, return an HTTPException with a 400 status code and a message indicating that the user already exists.
        existing_user = await self.get_user_by_email(email)
        if existing_user:
            raise HTTPException(status_code=400, detail="User already exists")

        #Create a new user object and add it to the database. The password should be hashed before storing it in the database.
        hashed_password = await self.hash_password(password)
        new_user = User(email=email, hashed_password=hashed_password)
        self.db.add(new_user)
        await self.db.commit()
        return new_user

    async def get_user_by_email(self, email: str):
        # Retrieve the user from the database based on the provided email
        query = select(User).where(User.email == email)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        # Verify the provided password against the hashed password stored in the database
        # Argon2 hashes are salted, so compare with verify() instead of hashing again
        return self.password_hash.verify(plain_password, hashed_password)
