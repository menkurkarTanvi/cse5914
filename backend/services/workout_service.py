from fastapi import HTTPException
from sqlalchemy.orm import Session
from models.user import User
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher
import jwt
from datetime import datetime, timedelta, timezone
from typing import Any
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
import os
from dotenv import load_dotenv
load_dotenv()

class Workout_Service:
    def __init__(self, db: Session):
        self.db = db

    async def get_workout_plan(self, user_id: str):
        # Implement the logic to retrieve the workout plan for the given user_id from the database.
        # If the current date is Monday, generate a new workout plan for the user and return it.
        # Otherwise, return the user's last workout plan from the database.
        pass

    async def get_most_recent_workout_plan(self, user_id: str):
        # Implement the logic to retrieve the most recent workout plan for the given user_id from the database.
        pass