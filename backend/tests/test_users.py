"""
Tests for the /users routes: registration and login.

Uses the `client` and `db_session` fixtures from conftest.py. Every test
runs in a transaction that is rolled back, so nothing persists.

Run from the backend folder:
    python -m pytest tests/test_users.py -v
"""

import os

import jwt
import pytest
from sqlalchemy import func, select

from models.user import User
from services.user_service import User_Service

pytestmark = pytest.mark.asyncio

REGISTER_URL = "/users/register"
LOGIN_URL = "/users/login"

# Lowercase on purpose, so the tests don't depend on how (or whether)
# emails are normalized.
EMAIL = "newuser@example.com"
PASSWORD = "correct-horse-battery"


async def create_user(db, email: str = EMAIL, password: str = PASSWORD) -> User:
    """Arrange step for login tests: create an account without the HTTP layer."""
    return await User_Service(db).register_new_user(email, password)


async def count_users_with_email(db, email: str) -> int:
    result = await db.execute(
        select(func.count()).select_from(User).where(User.email == email)
    )
    return result.scalar_one()


# ---------------------------------------------------------------------------
# Creating an account
# ---------------------------------------------------------------------------

async def test_register_creates_account(client, db_session):
    response = await client.post(
        REGISTER_URL, json={"email": EMAIL, "password": PASSWORD}
    )

    assert response.status_code == 201
    assert response.json() == {"message": "User registered successfully!"}

    result = await db_session.execute(select(User).where(User.email == EMAIL))
    user = result.scalar_one()
    # The password must be stored as an Argon2 hash, never as plain text.
    assert user.hashed_password != PASSWORD
    assert user.hashed_password.startswith("$argon2")


async def test_register_duplicate_email_returns_400(client, db_session):
    await create_user(db_session)

    response = await client.post(
        REGISTER_URL, json={"email": EMAIL, "password": "a-different-password"}
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "User already exists"
    assert await count_users_with_email(db_session, EMAIL) == 1


@pytest.mark.parametrize(
    "body",
    [
        {"email": EMAIL},
        {"password": PASSWORD},
        {},
    ],
)
async def test_register_missing_fields_returns_422(client, body):
    response = await client.post(REGISTER_URL, json=body)

    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Logging in with an account
# ---------------------------------------------------------------------------

async def test_login_with_valid_credentials_returns_token(client, db_session):
    user = await create_user(db_session)

    response = await client.post(
        LOGIN_URL, json={"email": EMAIL, "password": PASSWORD}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"

    payload = jwt.decode(
        body["access_token"], os.getenv("SECRET_KEY"), algorithms=["HS256"]
    )
    assert payload["sub"] == str(user.id)
    assert "exp" in payload


async def test_login_with_wrong_password_returns_401(client, db_session):
    await create_user(db_session)

    response = await client.post(
        LOGIN_URL, json={"email": EMAIL, "password": "not-the-password"}
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


async def test_register_then_login(client):
    register = await client.post(
        REGISTER_URL, json={"email": EMAIL, "password": PASSWORD}
    )
    assert register.status_code == 201

    login = await client.post(
        LOGIN_URL, json={"email": EMAIL, "password": PASSWORD}
    )

    assert login.status_code == 200
    assert "access_token" in login.json()


# ---------------------------------------------------------------------------
# Logging in without an account
# ---------------------------------------------------------------------------

async def test_login_with_unknown_email_returns_401(client):
    response = await client.post(
        LOGIN_URL, json={"email": "nobody@example.com", "password": PASSWORD}
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


async def test_login_errors_do_not_reveal_whether_email_exists(client, db_session):
    await create_user(db_session)

    wrong_password = await client.post(
        LOGIN_URL, json={"email": EMAIL, "password": "not-the-password"}
    )
    unknown_email = await client.post(
        LOGIN_URL, json={"email": "nobody@example.com", "password": PASSWORD}
    )

    assert wrong_password.status_code == unknown_email.status_code == 401
    assert wrong_password.json() == unknown_email.json()