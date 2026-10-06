import asyncio

from fastapi import HTTPException
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models.user import User


class User_Service:
    # Initialize the PasswordHash instance with Argon2
    password_hash = PasswordHash((Argon2Hasher(),))

    def __init__(self, db: Session):
        self.db = db

    async def hash_password(self, password: str) -> str:
        # Argon2 is CPU-bound and synchronous — run it off the event loop
        # so one slow hash doesn't stall every other request.
        return await asyncio.to_thread(self.password_hash.hash, password)

    async def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        # Argon2 hashes are salted, so compare with verify() instead of hashing again.
        return await asyncio.to_thread(
            self.password_hash.verify, plain_password, hashed_password
        )

    async def get_user_by_email(self, email: str) -> User | None:
        query = select(User).where(User.email == email)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def register_new_user(self, email: str, password: str) -> User:
        # Optional pre-check for a friendlier error in the common case —
        # the IntegrityError catch below is what actually prevents the race
        # where two requests for the same email both pass this check.
        existing_user = await self.get_user_by_email(email)
        if existing_user:
            raise HTTPException(status_code=400, detail="User already exists")

        hashed_password = await self.hash_password(password)
        new_user = User(email=email, hashed_password=hashed_password)
        self.db.add(new_user)

        try:
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            raise HTTPException(status_code=400, detail="User already exists")

        return new_user