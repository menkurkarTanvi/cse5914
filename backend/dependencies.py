from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.auth import get_current_user_id
from database.database import get_db  # adjust to wherever your get_db session dependency lives
from models.user import User

# Use this when a route only needs the caller's id.
CurrentUserId = Annotated[str, Depends(get_current_user_id)]


async def get_current_user(
    user_id: CurrentUserId,
    db: Session = Depends(get_db),
) -> User:
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


# Use this when a route needs the full User row (e.g. role checks, profile data).
CurrentUser = Annotated[User, Depends(get_current_user)]